"""
Porkbun CLI - Command-line interface
Author: Luke Steuber
"""
import argparse
import csv
import json
import os
import sys
from io import StringIO

from tabulate import tabulate

from .api import CONFIG_DIR, CONFIG_FILE, DNS_TYPES, PorkbunAPI
from .interactive import interactive_mode


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
