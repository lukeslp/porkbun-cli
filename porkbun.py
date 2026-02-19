#!/usr/bin/env python3
"""
Porkbun CLI - Domain and DNS management tool
Author: Luke Steuber
"""
import argparse
import csv
import json
import os
import sys
from io import StringIO

import requests
from tabulate import tabulate

# Optional: questionary for interactive mode
try:
    import questionary
    from questionary import Style
    HAS_QUESTIONARY = True
except ImportError:
    HAS_QUESTIONARY = False

CONFIG_DIR = os.path.expanduser("~/.config/porkbun-cli")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
API_BASE = "https://api.porkbun.com/api/json/v3"

# DNS record types supported by Porkbun
DNS_TYPES = ["A", "AAAA", "CNAME", "ALIAS", "MX", "TXT", "NS", "SRV", "TLSA", "CAA", "HTTPS", "SVCB", "SSHFP"]

# Custom style for questionary
STYLE = Style([
    ('qmark', 'fg:cyan bold'),
    ('question', 'bold'),
    ('answer', 'fg:cyan'),
    ('pointer', 'fg:cyan bold'),
    ('highlighted', 'fg:cyan bold'),
    ('selected', 'fg:green'),
]) if HAS_QUESTIONARY else None


class PorkbunAPI:
    """Wrapper for Porkbun API v3"""

    def __init__(self, api_key=None, secret_api_key=None):
        self.api_key = api_key
        self.secret_api_key = secret_api_key
        if not self.api_key or not self.secret_api_key:
            self._load_config()

    def _load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    self.api_key = config.get('apikey')
                    self.secret_api_key = config.get('secretapikey')
            except Exception as e:
                print(f"Error loading config: {e}", file=sys.stderr)

    def _get_auth_payload(self):
        if not self.api_key or not self.secret_api_key:
            raise ValueError("API key and Secret key are required. Run 'porkbun configure' first.")
        return {
            "apikey": self.api_key,
            "secretapikey": self.secret_api_key
        }

    def _request(self, endpoint, data=None):
        url = f"{API_BASE}/{endpoint}"
        payload = self._get_auth_payload()
        if data:
            payload.update(data)

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            if result.get('status') == 'ERROR':
                raise Exception(f"Porkbun API Error: {result.get('message')}")
            return result
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {e}")

    def ping(self):
        return self._request("ping")

    # Domain methods
    def domain_list(self):
        """List all domains in account"""
        return self._request("domain/listAll")

    def domain_check(self, domain):
        """Check domain availability and pricing"""
        return self._request(f"pricing/get/{domain}")

    def domain_create(self, domain, registration_type="personal", admin_filing_type="",
                      whois_privacy=False, auto_renew=False):
        """Register a new domain"""
        data = {
            "registrationType": registration_type,
            "adminFilingType": admin_filing_type,
            "whoisPrivacy": "yes" if whois_privacy else "no",
            "autoRenew": "yes" if auto_renew else "no"
        }
        return self._request(f"domain/create/{domain}", data)

    # Nameserver methods
    def nameservers_get(self, domain):
        """Get nameservers for a domain"""
        return self._request(f"domain/getNs/{domain}")

    def nameservers_update(self, domain, nameservers):
        """Update nameservers for a domain (list of NS hostnames)"""
        data = {"ns": nameservers}
        return self._request(f"domain/updateNs/{domain}", data)

    # SSL methods
    def ssl_retrieve(self, domain):
        """Retrieve SSL certificate bundle for domain"""
        return self._request(f"ssl/retrieve/{domain}")

    # DNS methods
    def dns_retrieve(self, domain):
        """List all DNS records for domain"""
        return self._request(f"dns/retrieve/{domain}")

    def dns_retrieve_by_type(self, domain, record_type):
        """List DNS records by type"""
        return self._request(f"dns/retrieveByNameType/{domain}/{record_type}")

    def dns_create(self, domain, record_type, content, name=None, prio=None, ttl=None):
        """Create a DNS record"""
        data = {"type": record_type, "content": content}
        if name:
            data["name"] = name
        if prio is not None:
            data["prio"] = str(prio)
        if ttl is not None:
            data["ttl"] = str(ttl)
        return self._request(f"dns/create/{domain}", data)

    def dns_edit(self, domain, record_id, record_type, content, name=None, prio=None, ttl=None):
        """Edit a DNS record by ID"""
        data = {"type": record_type, "content": content}
        if name:
            data["name"] = name
        if prio is not None:
            data["prio"] = str(prio)
        if ttl is not None:
            data["ttl"] = str(ttl)
        return self._request(f"dns/edit/{domain}/{record_id}", data)

    def dns_edit_by_name_type(self, domain, record_type, subdomain, content, prio=None, ttl=None):
        """Edit DNS record by name and type"""
        data = {"type": record_type, "content": content}
        if prio is not None:
            data["prio"] = str(prio)
        if ttl is not None:
            data["ttl"] = str(ttl)
        endpoint = f"dns/editByNameType/{domain}/{record_type}"
        if subdomain:
            endpoint += f"/{subdomain}"
        return self._request(endpoint, data)

    def dns_delete(self, domain, record_id):
        """Delete a DNS record by ID"""
        return self._request(f"dns/delete/{domain}/{record_id}")

    def dns_delete_by_name_type(self, domain, record_type, subdomain=None):
        """Delete DNS records by name and type"""
        endpoint = f"dns/deleteByNameType/{domain}/{record_type}"
        if subdomain:
            endpoint += f"/{subdomain}"
        return self._request(endpoint)

    def dns_upsert(self, domain, record_type, content, name=None, prio=None, ttl=None):
        """Create or update DNS record (finds by name+type)"""
        res = self.dns_retrieve(domain)
        records = res.get('records', [])

        target_name = f"{name}.{domain}" if name else domain

        existing_id = None
        for r in records:
            if r.get('type') == record_type and r.get('name') == target_name:
                existing_id = r.get('id')
                break

        if existing_id:
            print(f"Updating existing record {existing_id}...", file=sys.stderr)
            return self.dns_edit(domain, existing_id, record_type, content, name, prio, ttl)
        else:
            print("Creating new record...", file=sys.stderr)
            return self.dns_create(domain, record_type, content, name, prio, ttl)

    # URL Forwarding methods
    def url_retrieve(self, domain):
        """List URL forwards for domain"""
        return self._request(f"domain/getUrlForwarding/{domain}")

    def url_create(self, domain, location, subdomain="", forward_type="temporary",
                   wildcard=False, include_path=False):
        """Create URL forward"""
        data = {
            "location": location,
            "type": forward_type,
            "includePath": "yes" if include_path else "no",
            "wildcard": "yes" if wildcard else "no"
        }
        if subdomain:
            data["subdomain"] = subdomain
        return self._request(f"domain/addUrlForwarding/{domain}", data)

    def url_delete(self, domain, record_id):
        """Delete URL forward"""
        return self._request(f"domain/deleteUrlForwarding/{domain}/{record_id}")


# ============================================================================
# Command handlers
# ============================================================================

def cmd_configure(args):
    """Configure API credentials"""
    os.makedirs(CONFIG_DIR, exist_ok=True)

    print("Porkbun API Configuration")
    print("Get your API keys at: https://porkbun.com/account/api")
    print()

    apikey = input("Enter API Key: ").strip()
    secretapikey = input("Enter Secret API Key: ").strip()

    config = {"apikey": apikey, "secretapikey": secretapikey}

    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)
    os.chmod(CONFIG_FILE, 0o600)
    print(f"Configuration saved to {CONFIG_FILE}")


def cmd_ping(args):
    """Test API connection"""
    api = PorkbunAPI()
    try:
        res = api.ping()
        print(f"Success! Your IP: {res.get('yourIp')}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


# --- Domain commands ---

def cmd_domain_list(args):
    """List all domains in account"""
    api = PorkbunAPI()
    try:
        res = api.domain_list()
        domains = res.get('domains', [])
        if not domains:
            print("No domains found.")
            return

        table = []
        for d in domains:
            table.append([
                d.get('domain', ''),
                d.get('status', ''),
                d.get('tld', ''),
                d.get('createDate', '')[:10] if d.get('createDate') else '',
                d.get('expireDate', '')[:10] if d.get('expireDate') else '',
                'Yes' if d.get('autoRenew') else 'No'
            ])
        print(tabulate(table, headers=["Domain", "Status", "TLD", "Created", "Expires", "AutoRenew"], tablefmt="simple"))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_domain_search(args):
    """Check domain availability and price"""
    api = PorkbunAPI()
    try:
        res = api.domain_check(args.domain)
        pricing = res.get('pricing', {})
        print(f"Domain: {args.domain}")
        if pricing:
            print(f"Registration: ${pricing.get('registration', 'N/A')}")
            print(f"Renewal: ${pricing.get('renewal', 'N/A')}")
            print(f"Transfer: ${pricing.get('transfer', 'N/A')}")
        else:
            print("Pricing information not available")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_domain_buy(args):
    """Purchase a domain"""
    api = PorkbunAPI()
    print(f"PREPARING TO BUY DOMAIN: {args.domain}")
    print("This will charge your account.")
    confirm = input("Are you sure? Type 'YES' to confirm: ")
    if confirm != 'YES':
        print("Aborted.")
        sys.exit(0)

    try:
        res = api.domain_create(args.domain, whois_privacy=True, auto_renew=True)
        print(f"Success! Domain registered.")
        if res.get('invoiceId'):
            print(f"Invoice ID: {res.get('invoiceId')}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_domain_ns(args):
    """Get nameservers for domain"""
    api = PorkbunAPI()
    try:
        res = api.nameservers_get(args.domain)
        ns_list = res.get('ns', [])
        if not ns_list:
            print("No nameservers found (using Porkbun defaults)")
            return
        print(f"Nameservers for {args.domain}:")
        for ns in ns_list:
            print(f"  {ns}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_domain_ns_set(args):
    """Set nameservers for domain"""
    api = PorkbunAPI()
    try:
        api.nameservers_update(args.domain, args.nameservers)
        print(f"Nameservers updated for {args.domain}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_domain_ssl(args):
    """Retrieve SSL certificate"""
    api = PorkbunAPI()
    try:
        res = api.ssl_retrieve(args.domain)

        if args.output:
            # Write to files
            base = args.output
            with open(f"{base}.crt", 'w') as f:
                f.write(res.get('certificatechain', ''))
            with open(f"{base}.key", 'w') as f:
                f.write(res.get('privatekey', ''))
            with open(f"{base}.ca", 'w') as f:
                f.write(res.get('intermediatecertificate', ''))
            print(f"SSL files written: {base}.crt, {base}.key, {base}.ca")
        else:
            print("=== Certificate Chain ===")
            print(res.get('certificatechain', 'N/A')[:500] + "...")
            print("\n=== Private Key ===")
            print("[REDACTED - use --output to save]")
            print(f"\nUse --output PREFIX to save files")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


# --- DNS commands ---

def cmd_dns_list(args):
    """List DNS records"""
    api = PorkbunAPI()
    try:
        res = api.dns_retrieve(args.domain)
        records = res.get('records', [])
        if not records:
            print("No records found.")
            return

        # Filter by type if specified
        if args.type:
            records = [r for r in records if r.get('type') == args.type.upper()]

        table = []
        for r in records:
            content = r.get('content', '')
            if len(content) > 50:
                content = content[:47] + "..."
            table.append([
                r.get('id', ''),
                r.get('type', ''),
                r.get('name', ''),
                content,
                r.get('prio', ''),
                r.get('ttl', '')
            ])
        print(tabulate(table, headers=["ID", "Type", "Name", "Content", "Prio", "TTL"], tablefmt="simple"))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_dns_create(args):
    """Create DNS record"""
    api = PorkbunAPI()
    try:
        api.dns_create(args.domain, args.type.upper(), args.content, args.name, args.prio, args.ttl)
        print("Record created successfully.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_dns_edit(args):
    """Edit DNS record"""
    api = PorkbunAPI()
    try:
        api.dns_edit(args.domain, args.id, args.type.upper(), args.content, args.name, args.prio, args.ttl)
        print("Record updated successfully.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_dns_delete(args):
    """Delete DNS record"""
    api = PorkbunAPI()
    try:
        api.dns_delete(args.domain, args.id)
        print("Record deleted successfully.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_dns_upsert(args):
    """Create or update DNS record"""
    api = PorkbunAPI()
    try:
        api.dns_upsert(args.domain, args.type.upper(), args.content, args.name, args.prio, args.ttl)
        print("Record upserted successfully.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


# --- URL forwarding commands ---

def cmd_url_list(args):
    """List URL forwards"""
    api = PorkbunAPI()
    try:
        res = api.url_retrieve(args.domain)
        records = res.get('forwards', [])
        if not records:
            print("No forwards found.")
            return

        table = []
        for r in records:
            table.append([
                r.get('id', ''),
                r.get('subdomain', '') or '(root)',
                r.get('location', ''),
                r.get('type', ''),
                'Yes' if r.get('wildcard') == 'yes' else 'No',
                'Yes' if r.get('includePath') == 'yes' else 'No'
            ])
        print(tabulate(table, headers=["ID", "Subdomain", "Location", "Type", "Wildcard", "Path"], tablefmt="simple"))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_url_set(args):
    """Create URL forward"""
    api = PorkbunAPI()
    try:
        # Map type argument to API values
        type_map = {'301': 'permanent', '302': 'temporary', '307': 'temporary'}
        forward_type = type_map.get(args.type, 'temporary')
        api.url_create(args.domain, args.location, args.subdomain or "", forward_type,
                       args.wildcard, args.path)
        print("URL forward set successfully.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_url_delete(args):
    """Delete URL forward"""
    api = PorkbunAPI()
    try:
        api.url_delete(args.domain, args.id)
        print("URL forward deleted successfully.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


# ============================================================================
# Bulk operations
# ============================================================================

def cmd_bulk_export(args):
    """Export DNS records to JSON or CSV"""
    api = PorkbunAPI()
    try:
        res = api.dns_retrieve(args.domain)
        records = res.get('records', [])

        export_data = {
            "domain": args.domain,
            "records": [
                {
                    "id": r.get('id'),
                    "type": r.get('type'),
                    "name": r.get('name'),
                    "content": r.get('content'),
                    "prio": r.get('prio'),
                    "ttl": r.get('ttl')
                }
                for r in records
            ]
        }

        if args.format == 'csv':
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=['type', 'name', 'content', 'prio', 'ttl'])
            writer.writeheader()
            for r in export_data['records']:
                writer.writerow({
                    'type': r['type'],
                    'name': r['name'],
                    'content': r['content'],
                    'prio': r['prio'] or '',
                    'ttl': r['ttl'] or ''
                })
            result = output.getvalue()
        else:
            result = json.dumps(export_data, indent=2)

        if args.output:
            with open(args.output, 'w') as f:
                f.write(result)
            print(f"Exported {len(records)} records to {args.output}")
        else:
            print(result)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_bulk_import(args):
    """Import DNS records from JSON or CSV"""
    api = PorkbunAPI()

    try:
        with open(args.file, 'r') as f:
            content = f.read()

        # Detect format
        if args.file.endswith('.csv') or args.format == 'csv':
            reader = csv.DictReader(StringIO(content))
            records = []
            for row in reader:
                records.append({
                    'action': row.get('action', 'create'),
                    'type': row['type'],
                    'name': row.get('name', ''),
                    'content': row['content'],
                    'prio': row.get('prio') or None,
                    'ttl': row.get('ttl') or None
                })
            domain = args.domain
        else:
            data = json.loads(content)
            domain = args.domain or data.get('domain')
            records = data.get('records', [])
            for r in records:
                if 'action' not in r:
                    r['action'] = 'create'

        if not domain:
            print("Error: Domain must be specified (--domain or in JSON)", file=sys.stderr)
            sys.exit(1)

        print(f"Importing {len(records)} records to {domain}")

        if args.dry_run:
            print("\n=== DRY RUN - No changes will be made ===\n")

        for i, r in enumerate(records, 1):
            action = r.get('action', 'create')
            name = r.get('name', '')
            # Extract subdomain from full name if needed
            if name.endswith(f'.{domain}'):
                subdomain = name[:-len(f'.{domain}')]
            elif name == domain:
                subdomain = ''
            else:
                subdomain = name

            desc = f"[{i}/{len(records)}] {action.upper()} {r['type']} {name or '(root)'} -> {r['content'][:30]}"

            if args.dry_run:
                print(f"  {desc}")
                continue

            try:
                if action == 'create':
                    api.dns_create(domain, r['type'], r['content'], subdomain or None, r.get('prio'), r.get('ttl'))
                elif action == 'upsert':
                    api.dns_upsert(domain, r['type'], r['content'], subdomain or None, r.get('prio'), r.get('ttl'))
                elif action == 'delete':
                    if r.get('id'):
                        api.dns_delete(domain, r['id'])
                    else:
                        api.dns_delete_by_name_type(domain, r['type'], subdomain or None)
                print(f"  OK: {desc}")
            except Exception as e:
                print(f"  FAIL: {desc} - {e}", file=sys.stderr)

        if args.dry_run:
            print("\n=== DRY RUN COMPLETE ===")
        else:
            print("\nImport complete.")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


# ============================================================================
# Interactive mode
# ============================================================================

def interactive_mode():
    """Interactive menu-driven CLI"""
    if not HAS_QUESTIONARY:
        print("Interactive mode requires 'questionary' package.", file=sys.stderr)
        print("Install with: pip install questionary", file=sys.stderr)
        sys.exit(1)

    api = PorkbunAPI()

    # Test connection first
    try:
        api.ping()
    except Exception as e:
        print(f"API connection failed: {e}", file=sys.stderr)
        print("Run 'porkbun configure' to set up credentials.", file=sys.stderr)
        sys.exit(1)

    print("\n  Porkbun CLI - Interactive Mode")
    print("  ===============================\n")

    while True:
        action = questionary.select(
            "What would you like to do?",
            choices=[
                "Manage DNS Records",
                "Manage URL Forwarding",
                "Manage Domains",
                "Bulk Operations",
                "Exit"
            ],
            style=STYLE
        ).ask()

        if action is None or action == "Exit":
            print("Goodbye!")
            break
        elif action == "Manage DNS Records":
            interactive_dns(api)
        elif action == "Manage URL Forwarding":
            interactive_url(api)
        elif action == "Manage Domains":
            interactive_domains(api)
        elif action == "Bulk Operations":
            interactive_bulk(api)


def get_domain_choices(api):
    """Get list of domains for selection"""
    try:
        res = api.domain_list()
        domains = res.get('domains', [])
        return [d.get('domain') for d in domains]
    except:
        return []


def interactive_dns(api):
    """DNS record management submenu"""
    domains = get_domain_choices(api)
    if not domains:
        domain = questionary.text("Enter domain name:", style=STYLE).ask()
    else:
        domain = questionary.select(
            "Select domain:",
            choices=domains + ["[Enter manually]"],
            style=STYLE
        ).ask()
        if domain == "[Enter manually]":
            domain = questionary.text("Enter domain name:", style=STYLE).ask()

    if not domain:
        return

    while True:
        action = questionary.select(
            f"DNS for {domain}:",
            choices=[
                "List all records",
                "Create record",
                "Edit record",
                "Delete record",
                "Back"
            ],
            style=STYLE
        ).ask()

        if action is None or action == "Back":
            break
        elif action == "List all records":
            try:
                res = api.dns_retrieve(domain)
                records = res.get('records', [])
                if not records:
                    print("\nNo records found.\n")
                else:
                    table = [[r.get('id'), r.get('type'), r.get('name'),
                              r.get('content', '')[:40], r.get('prio'), r.get('ttl')]
                             for r in records]
                    print("\n" + tabulate(table, headers=["ID", "Type", "Name", "Content", "Prio", "TTL"], tablefmt="simple") + "\n")
            except Exception as e:
                print(f"\nError: {e}\n")

        elif action == "Create record":
            record_type = questionary.select("Record type:", choices=DNS_TYPES, style=STYLE).ask()
            subdomain = questionary.text("Subdomain (blank for root):", style=STYLE).ask()
            content = questionary.text("Content/Value:", style=STYLE).ask()

            prio = None
            if record_type in ['MX', 'SRV']:
                prio_str = questionary.text("Priority:", default="10", style=STYLE).ask()
                prio = int(prio_str) if prio_str else None

            ttl_str = questionary.text("TTL (blank for default):", style=STYLE).ask()
            ttl = int(ttl_str) if ttl_str else None

            if content:
                try:
                    api.dns_create(domain, record_type, content, subdomain or None, prio, ttl)
                    print("\nRecord created successfully!\n")
                except Exception as e:
                    print(f"\nError: {e}\n")

        elif action == "Edit record":
            record_id = questionary.text("Record ID to edit:", style=STYLE).ask()
            record_type = questionary.select("New record type:", choices=DNS_TYPES, style=STYLE).ask()
            subdomain = questionary.text("New subdomain (blank for root):", style=STYLE).ask()
            content = questionary.text("New content/value:", style=STYLE).ask()

            prio = None
            if record_type in ['MX', 'SRV']:
                prio_str = questionary.text("Priority:", default="10", style=STYLE).ask()
                prio = int(prio_str) if prio_str else None

            ttl_str = questionary.text("TTL (blank for default):", style=STYLE).ask()
            ttl = int(ttl_str) if ttl_str else None

            if record_id and content:
                try:
                    api.dns_edit(domain, record_id, record_type, content, subdomain or None, prio, ttl)
                    print("\nRecord updated successfully!\n")
                except Exception as e:
                    print(f"\nError: {e}\n")

        elif action == "Delete record":
            record_id = questionary.text("Record ID to delete:", style=STYLE).ask()
            if record_id:
                confirm = questionary.confirm(f"Delete record {record_id}?", default=False, style=STYLE).ask()
                if confirm:
                    try:
                        api.dns_delete(domain, record_id)
                        print("\nRecord deleted successfully!\n")
                    except Exception as e:
                        print(f"\nError: {e}\n")


def interactive_url(api):
    """URL forwarding submenu"""
    domains = get_domain_choices(api)
    if not domains:
        domain = questionary.text("Enter domain name:", style=STYLE).ask()
    else:
        domain = questionary.select(
            "Select domain:",
            choices=domains + ["[Enter manually]"],
            style=STYLE
        ).ask()
        if domain == "[Enter manually]":
            domain = questionary.text("Enter domain name:", style=STYLE).ask()

    if not domain:
        return

    while True:
        action = questionary.select(
            f"URL Forwarding for {domain}:",
            choices=[
                "List forwards",
                "Create forward",
                "Delete forward",
                "Back"
            ],
            style=STYLE
        ).ask()

        if action is None or action == "Back":
            break
        elif action == "List forwards":
            try:
                res = api.url_retrieve(domain)
                records = res.get('forwards', [])
                if not records:
                    print("\nNo forwards found.\n")
                else:
                    table = [[r.get('id'), r.get('subdomain') or '(root)', r.get('location'),
                              r.get('type'), r.get('wildcard'), r.get('includePath')]
                             for r in records]
                    print("\n" + tabulate(table, headers=["ID", "Subdomain", "Location", "Type", "Wildcard", "Path"], tablefmt="simple") + "\n")
            except Exception as e:
                print(f"\nError: {e}\n")

        elif action == "Create forward":
            subdomain = questionary.text("Subdomain (blank for root):", style=STYLE).ask()
            location = questionary.text("Destination URL:", style=STYLE).ask()
            forward_type = questionary.select("Redirect type:", choices=["301 (Permanent)", "302 (Temporary)"], style=STYLE).ask()
            wildcard = questionary.confirm("Include wildcard?", default=False, style=STYLE).ask()
            include_path = questionary.confirm("Include path?", default=False, style=STYLE).ask()

            if location:
                try:
                    ftype = "permanent" if "301" in forward_type else "temporary"
                    api.url_create(domain, location, subdomain or "", ftype, wildcard, include_path)
                    print("\nURL forward created successfully!\n")
                except Exception as e:
                    print(f"\nError: {e}\n")

        elif action == "Delete forward":
            record_id = questionary.text("Forward ID to delete:", style=STYLE).ask()
            if record_id:
                confirm = questionary.confirm(f"Delete forward {record_id}?", default=False, style=STYLE).ask()
                if confirm:
                    try:
                        api.url_delete(domain, record_id)
                        print("\nForward deleted successfully!\n")
                    except Exception as e:
                        print(f"\nError: {e}\n")


def interactive_domains(api):
    """Domain management submenu"""
    while True:
        action = questionary.select(
            "Domain Management:",
            choices=[
                "List my domains",
                "Check domain availability",
                "View nameservers",
                "Get SSL certificate",
                "Back"
            ],
            style=STYLE
        ).ask()

        if action is None or action == "Back":
            break
        elif action == "List my domains":
            try:
                res = api.domain_list()
                domains = res.get('domains', [])
                if not domains:
                    print("\nNo domains found.\n")
                else:
                    table = [[d.get('domain'), d.get('status'),
                              d.get('expireDate', '')[:10] if d.get('expireDate') else '']
                             for d in domains]
                    print("\n" + tabulate(table, headers=["Domain", "Status", "Expires"], tablefmt="simple") + "\n")
            except Exception as e:
                print(f"\nError: {e}\n")

        elif action == "Check domain availability":
            domain = questionary.text("Domain to check (e.g., example.com):", style=STYLE).ask()
            if domain:
                try:
                    res = api.domain_check(domain)
                    pricing = res.get('pricing', {})
                    print(f"\nDomain: {domain}")
                    if pricing:
                        print(f"Registration: ${pricing.get('registration', 'N/A')}")
                        print(f"Renewal: ${pricing.get('renewal', 'N/A')}")
                    print()
                except Exception as e:
                    print(f"\nError: {e}\n")

        elif action == "View nameservers":
            domains = get_domain_choices(api)
            if domains:
                domain = questionary.select("Select domain:", choices=domains, style=STYLE).ask()
            else:
                domain = questionary.text("Enter domain:", style=STYLE).ask()

            if domain:
                try:
                    res = api.nameservers_get(domain)
                    ns_list = res.get('ns', [])
                    print(f"\nNameservers for {domain}:")
                    if ns_list:
                        for ns in ns_list:
                            print(f"  {ns}")
                    else:
                        print("  (using Porkbun defaults)")
                    print()
                except Exception as e:
                    print(f"\nError: {e}\n")

        elif action == "Get SSL certificate":
            domains = get_domain_choices(api)
            if domains:
                domain = questionary.select("Select domain:", choices=domains, style=STYLE).ask()
            else:
                domain = questionary.text("Enter domain:", style=STYLE).ask()

            if domain:
                output = questionary.text("Output file prefix (blank to display):", style=STYLE).ask()
                try:
                    res = api.ssl_retrieve(domain)
                    if output:
                        with open(f"{output}.crt", 'w') as f:
                            f.write(res.get('certificatechain', ''))
                        with open(f"{output}.key", 'w') as f:
                            f.write(res.get('privatekey', ''))
                        print(f"\nSSL files saved: {output}.crt, {output}.key\n")
                    else:
                        print("\n=== Certificate Chain (truncated) ===")
                        print(res.get('certificatechain', 'N/A')[:200] + "...\n")
                except Exception as e:
                    print(f"\nError: {e}\n")


def interactive_bulk(api):
    """Bulk operations submenu"""
    while True:
        action = questionary.select(
            "Bulk Operations:",
            choices=[
                "Export DNS records",
                "Import DNS records",
                "Back"
            ],
            style=STYLE
        ).ask()

        if action is None or action == "Back":
            break
        elif action == "Export DNS records":
            domains = get_domain_choices(api)
            if domains:
                domain = questionary.select("Select domain:", choices=domains, style=STYLE).ask()
            else:
                domain = questionary.text("Enter domain:", style=STYLE).ask()

            if domain:
                fmt = questionary.select("Export format:", choices=["JSON", "CSV"], style=STYLE).ask()
                output = questionary.text("Output file (blank for stdout):", style=STYLE).ask()

                try:
                    res = api.dns_retrieve(domain)
                    records = res.get('records', [])

                    export_data = {
                        "domain": domain,
                        "records": [
                            {"type": r.get('type'), "name": r.get('name'), "content": r.get('content'),
                             "prio": r.get('prio'), "ttl": r.get('ttl')}
                            for r in records
                        ]
                    }

                    if fmt == "CSV":
                        out = StringIO()
                        writer = csv.DictWriter(out, fieldnames=['type', 'name', 'content', 'prio', 'ttl'])
                        writer.writeheader()
                        for r in export_data['records']:
                            writer.writerow(r)
                        result = out.getvalue()
                    else:
                        result = json.dumps(export_data, indent=2)

                    if output:
                        with open(output, 'w') as f:
                            f.write(result)
                        print(f"\nExported {len(records)} records to {output}\n")
                    else:
                        print(f"\n{result}\n")
                except Exception as e:
                    print(f"\nError: {e}\n")

        elif action == "Import DNS records":
            filepath = questionary.text("Import file path:", style=STYLE).ask()
            if not filepath or not os.path.exists(filepath):
                print("\nFile not found.\n")
                continue

            domain = questionary.text("Target domain (blank to use file's domain):", style=STYLE).ask()
            dry_run = questionary.confirm("Dry run (preview only)?", default=True, style=STYLE).ask()

            try:
                with open(filepath, 'r') as f:
                    content = f.read()

                if filepath.endswith('.csv'):
                    reader = csv.DictReader(StringIO(content))
                    records = [{'action': row.get('action', 'create'), **row} for row in reader]
                else:
                    data = json.loads(content)
                    domain = domain or data.get('domain')
                    records = data.get('records', [])

                if not domain:
                    print("\nError: Domain required.\n")
                    continue

                print(f"\n{'DRY RUN - ' if dry_run else ''}Importing {len(records)} records to {domain}:\n")

                for i, r in enumerate(records, 1):
                    action_type = r.get('action', 'create')
                    desc = f"  [{i}] {action_type.upper()} {r.get('type', '?')} {r.get('name', '(root)')} -> {r.get('content', '')[:30]}"

                    if dry_run:
                        print(desc)
                    else:
                        try:
                            name = r.get('name', '')
                            if name.endswith(f'.{domain}'):
                                subdomain = name[:-len(f'.{domain}')]
                            elif name == domain:
                                subdomain = ''
                            else:
                                subdomain = name

                            if action_type == 'create':
                                api.dns_create(domain, r['type'], r['content'], subdomain or None, r.get('prio'), r.get('ttl'))
                            elif action_type == 'upsert':
                                api.dns_upsert(domain, r['type'], r['content'], subdomain or None, r.get('prio'), r.get('ttl'))
                            print(f"{desc} - OK")
                        except Exception as e:
                            print(f"{desc} - FAILED: {e}")

                print()
            except Exception as e:
                print(f"\nError: {e}\n")


# ============================================================================
# Main CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Porkbun CLI - Domain and DNS management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  porkbun configure              Setup API credentials
  porkbun ping                   Test API connection
  porkbun domain list            List all domains
  porkbun dns list example.com   List DNS records
  porkbun interactive            Interactive mode
  porkbun bulk export example.com -o records.json
"""
    )
    subparsers = parser.add_subparsers(dest='command', help='Command')

    # Configure
    subparsers.add_parser('configure', help='Configure API credentials')

    # Ping
    subparsers.add_parser('ping', help='Test API connection')

    # Interactive
    subparsers.add_parser('interactive', help='Interactive menu mode')
    subparsers.add_parser('i', help='Interactive menu mode (shortcut)')

    # Domain commands
    domain_parser = subparsers.add_parser('domain', help='Domain management')
    domain_sub = domain_parser.add_subparsers(dest='domain_command')

    domain_sub.add_parser('list', help='List all domains in account')

    search_p = domain_sub.add_parser('search', help='Check domain availability/pricing')
    search_p.add_argument('domain', help='Domain name')

    buy_p = domain_sub.add_parser('buy', help='Purchase a domain')
    buy_p.add_argument('domain', help='Domain name')

    ns_p = domain_sub.add_parser('ns', help='Get nameservers')
    ns_p.add_argument('domain', help='Domain name')

    ns_set_p = domain_sub.add_parser('ns-set', help='Set nameservers')
    ns_set_p.add_argument('domain', help='Domain name')
    ns_set_p.add_argument('nameservers', nargs='+', help='Nameserver hostnames')

    ssl_p = domain_sub.add_parser('ssl', help='Retrieve SSL certificate')
    ssl_p.add_argument('domain', help='Domain name')
    ssl_p.add_argument('-o', '--output', help='Output file prefix')

    # DNS commands
    dns_parser = subparsers.add_parser('dns', help='DNS record management')
    dns_sub = dns_parser.add_subparsers(dest='dns_command')

    list_p = dns_sub.add_parser('list', help='List DNS records')
    list_p.add_argument('domain', help='Domain name')
    list_p.add_argument('-t', '--type', help='Filter by record type')

    create_p = dns_sub.add_parser('create', help='Create DNS record')
    create_p.add_argument('domain', help='Domain name')
    create_p.add_argument('type', help='Record type (A, CNAME, MX, TXT, etc)')
    create_p.add_argument('content', help='Record content')
    create_p.add_argument('--name', '-n', help='Subdomain')
    create_p.add_argument('--prio', '-p', type=int, help='Priority')
    create_p.add_argument('--ttl', '-t', type=int, help='TTL')

    edit_p = dns_sub.add_parser('edit', help='Edit DNS record')
    edit_p.add_argument('domain', help='Domain name')
    edit_p.add_argument('id', help='Record ID')
    edit_p.add_argument('type', help='Record type')
    edit_p.add_argument('content', help='Record content')
    edit_p.add_argument('--name', '-n', help='Subdomain')
    edit_p.add_argument('--prio', '-p', type=int, help='Priority')
    edit_p.add_argument('--ttl', '-t', type=int, help='TTL')

    delete_p = dns_sub.add_parser('delete', help='Delete DNS record')
    delete_p.add_argument('domain', help='Domain name')
    delete_p.add_argument('id', help='Record ID')

    upsert_p = dns_sub.add_parser('upsert', help='Create or update DNS record')
    upsert_p.add_argument('domain', help='Domain name')
    upsert_p.add_argument('type', help='Record type')
    upsert_p.add_argument('content', help='Record content')
    upsert_p.add_argument('--name', '-n', help='Subdomain')
    upsert_p.add_argument('--prio', '-p', type=int, help='Priority')
    upsert_p.add_argument('--ttl', '-t', type=int, help='TTL')

    # URL Forwarding commands
    url_parser = subparsers.add_parser('url', help='URL forwarding management')
    url_sub = url_parser.add_subparsers(dest='url_command')

    url_list = url_sub.add_parser('list', help='List URL forwards')
    url_list.add_argument('domain', help='Domain name')

    url_set = url_sub.add_parser('set', help='Create URL forward')
    url_set.add_argument('domain', help='Domain name')
    url_set.add_argument('location', help='Destination URL')
    url_set.add_argument('--subdomain', '-s', default='', help='Subdomain')
    url_set.add_argument('--type', '-t', choices=['301', '302', '307'], default='302', help='Redirect type')
    url_set.add_argument('--wildcard', '-w', action='store_true', help='Enable wildcard')
    url_set.add_argument('--path', '-p', action='store_true', help='Include path')

    url_del = url_sub.add_parser('delete', help='Delete URL forward')
    url_del.add_argument('domain', help='Domain name')
    url_del.add_argument('id', help='Forward ID')

    # Bulk commands
    bulk_parser = subparsers.add_parser('bulk', help='Bulk operations')
    bulk_sub = bulk_parser.add_subparsers(dest='bulk_command')

    export_p = bulk_sub.add_parser('export', help='Export DNS records')
    export_p.add_argument('domain', help='Domain name')
    export_p.add_argument('-f', '--format', choices=['json', 'csv'], default='json', help='Output format')
    export_p.add_argument('-o', '--output', help='Output file')

    import_p = bulk_sub.add_parser('import', help='Import DNS records')
    import_p.add_argument('file', help='Import file (JSON or CSV)')
    import_p.add_argument('-d', '--domain', help='Target domain (overrides file)')
    import_p.add_argument('-f', '--format', choices=['json', 'csv'], help='File format (auto-detected)')
    import_p.add_argument('--dry-run', action='store_true', help='Preview without making changes')

    # Parse and dispatch
    args = parser.parse_args()

    if args.command == 'configure':
        cmd_configure(args)
    elif args.command == 'ping':
        cmd_ping(args)
    elif args.command in ('interactive', 'i'):
        interactive_mode()
    elif args.command == 'domain':
        if args.domain_command == 'list':
            cmd_domain_list(args)
        elif args.domain_command == 'search':
            cmd_domain_search(args)
        elif args.domain_command == 'buy':
            cmd_domain_buy(args)
        elif args.domain_command == 'ns':
            cmd_domain_ns(args)
        elif args.domain_command == 'ns-set':
            cmd_domain_ns_set(args)
        elif args.domain_command == 'ssl':
            cmd_domain_ssl(args)
        else:
            domain_parser.print_help()
    elif args.command == 'dns':
        if args.dns_command == 'list':
            cmd_dns_list(args)
        elif args.dns_command == 'create':
            cmd_dns_create(args)
        elif args.dns_command == 'edit':
            cmd_dns_edit(args)
        elif args.dns_command == 'delete':
            cmd_dns_delete(args)
        elif args.dns_command == 'upsert':
            cmd_dns_upsert(args)
        else:
            dns_parser.print_help()
    elif args.command == 'url':
        if args.url_command == 'list':
            cmd_url_list(args)
        elif args.url_command == 'set':
            cmd_url_set(args)
        elif args.url_command == 'delete':
            cmd_url_delete(args)
        else:
            url_parser.print_help()
    elif args.command == 'bulk':
        if args.bulk_command == 'export':
            cmd_bulk_export(args)
        elif args.bulk_command == 'import':
            cmd_bulk_import(args)
        else:
            bulk_parser.print_help()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
