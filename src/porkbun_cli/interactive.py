"""
Interactive menu-driven CLI for Porkbun
Author: Luke Steuber
"""
import csv
import json
import os
import sys
from io import StringIO

from tabulate import tabulate

from .api import DNS_TYPES, PorkbunAPI

# Optional: questionary for interactive mode
try:
    import questionary
    from questionary import Style
    HAS_QUESTIONARY = True
except ImportError:
    HAS_QUESTIONARY = False
    questionary = None
    Style = None

# Custom style for questionary
STYLE = Style([
    ('qmark', 'fg:cyan bold'),
    ('question', 'bold'),
    ('answer', 'fg:cyan'),
    ('pointer', 'fg:cyan bold'),
    ('highlighted', 'fg:cyan bold'),
    ('selected', 'fg:green'),
]) if HAS_QUESTIONARY else None


def get_domain_choices(api):
    """Get list of domains for selection"""
    try:
        res = api.domain_list()
        domains = res.get('domains', [])
        return [d.get('domain') for d in domains]
    except Exception:
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


def interactive_mode():
    """Interactive menu-driven CLI"""
    if not HAS_QUESTIONARY:
        print("Interactive mode requires 'questionary' package.", file=sys.stderr)
        print("Install with: pip install porkbun-cli[interactive]", file=sys.stderr)
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
