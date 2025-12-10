#!/usr/bin/env python3
import argparse
import json
import os
import sys
import requests
from tabulate import tabulate

CONFIG_DIR = os.path.expanduser("~/.config/porkbun-cli")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
API_BASE = "https://api.porkbun.com/api/json/v3"

class PorkbunAPI:
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
        
        if not self.api_key or not self.secret_api_key:
            # Only critical if we are trying to use the API, but for now we'll just warn or let request fail
            pass

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

    # DNS methods
    def dns_retrieve(self, domain):
        return self._request(f"dns/retrieve/{domain}")

    def dns_create(self, domain, type, content, name=None, prio=None, ttl=None):
        data = {
            "type": type,
            "content": content
        }
        if name:
            data["name"] = name
        if prio:
            data["prio"] = prio
        if ttl:
            data["ttl"] = ttl
        return self._request(f"dns/create/{domain}", data)

    def dns_edit(self, domain, record_id, type, content, name=None, prio=None, ttl=None):
        data = {
            "type": type,
            "content": content
        }
        if name:
            data["name"] = name
        if prio:
            data["prio"] = prio
        if ttl:
            data["ttl"] = ttl
        return self._request(f"dns/edit/{domain}/{record_id}", data)

    def dns_delete(self, domain, record_id):
        return self._request(f"dns/delete/{domain}/{record_id}")

    # Domain methods
    def domain_check(self, domain):
         # The pricing endpoint is typically used to check availability/price
        return self._request(f"pricing/check/{domain}")

    def domain_create(self, domain, registration_type="personal", admin_filing_type="", whois_privacy=False, auto_renew=False):
        data = {
            "registrationType": registration_type,
            "adminFilingType": admin_filing_type,
            "whoisPrivacy": "yes" if whois_privacy else "no",
            "autoRenew": "yes" if auto_renew else "no"
        }
    # URL Forwarding methods
    def url_retrieve(self, domain):
        return self._request(f"domain/getUrlForwarding/{domain}")

    def url_create(self, domain, location, subdomain="", type="temporary", wildcard=False, include_path=False):
        data = {
            "location": location,
            "type": type,
            "includePath": "yes" if include_path else "no",
            "wildcard": "yes" if wildcard else "no"
        }
        if subdomain:
            data["subdomain"] = subdomain
        return self._request(f"domain/addUrlForwarding/{domain}", data)

    def url_delete(self, domain, record_id):
        return self._request(f"domain/deleteUrlForwarding/{domain}/{record_id}")
    
    # DNS Upsert
    def dns_upsert(self, domain, type, content, name=None, prio=None, ttl=None):
        # 1. Retrieve existing records
        res = self.dns_retrieve(domain)
        records = res.get('records', [])
        
        # 2. Find matching record (same name and type)
        # Note: 'name' from API is full FQDN usually, but let's check how input is handled.
        # If user provides sub 'www', API might return 'www.domain.com'. 
        # For simplicity, we compare if the record name starts with the subdomain or is exact.
        
        target_name = f"{name}.{domain}" if name else domain
        
        existing_id = None
        for r in records:
            if r.get('type') == type and r.get('name') == target_name:
                existing_id = r.get('id')
                break
        
        if existing_id:
            print(f"Updating existing record {existing_id}...", file=sys.stderr)
            return self.dns_edit(domain, existing_id, type, content, name, prio, ttl)
        else:
            print("Creating new record...", file=sys.stderr)
            return self.dns_create(domain, type, content, name, prio, ttl)

def cmd_domain_search(args):
    api = PorkbunAPI()
    try:
        res = api.domain_check(args.domain)
        # Typical response has "domain", "status", "price"
        domain_name = res.get("domain", args.domain)
        status = res.get("status", "unknown")
        price = res.get("price", "N/A")
        print(f"Domain: {domain_name}")
        print(f"Status: {status}")
        print(f"Price: {price}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def cmd_domain_buy(args):
    api = PorkbunAPI()
    print(f"PREPARING TO BUY DOMAIN: {args.domain}")
    print("This will charge your account.")
    confirm = input("Are you sure? Type 'YES' to confirm: ")
    if confirm != 'YES':
        print("Aborted.")
        sys.exit(0)
    
    try:
        # Defaults for now, can extend args later
        res = api.domain_create(args.domain, whois_privacy=True, auto_renew=True)
        print(f"Success! Invoice ID: {res.get('invoiceId')}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_configure(args):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    
    print("This will overwrite your current configuration.")
    apikey = input("Enter API Key: ").strip()
    secretapikey = input("Enter Secret API Key: ").strip()
    
    config = {
        "apikey": apikey,
        "secretapikey": secretapikey
    }
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)
    print(f"Configuration saved to {CONFIG_FILE}")

def cmd_ping(args):
    api = PorkbunAPI()
    try:
        res = api.ping()
        print(f"Success! IP: {res.get('yourIp')}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def cmd_dns_list(args):
    api = PorkbunAPI()
    try:
        res = api.dns_retrieve(args.domain)
        records = res.get('records', [])
        if not records:
            print("No records found.")
            return

        # Simple table output
        # Tabulate output
        table = []
        for r in records:
            table.append([
                r.get('id', ''),
                r.get('type', ''),
                r.get('name', ''),
                r.get('content', '')[:50], # Truncate long content
                r.get('prio', ''),
                r.get('ttl', '')
            ])
        print(tabulate(table, headers=["ID", "Type", "Name", "Content", "Prio", "TTL"], tablefmt="simple"))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def cmd_dns_create(args):
    api = PorkbunAPI()
    try:
        api.dns_create(args.domain, args.type, args.content, args.name, args.prio, args.ttl)
        print("Record created successfully.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def cmd_dns_delete(args):
    api = PorkbunAPI()
    try:
        api.dns_delete(args.domain, args.id)
        print("Record deleted successfully.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def cmd_dns_upsert(args):
    api = PorkbunAPI()
    try:
        api.dns_upsert(args.domain, args.type, args.content, args.name, args.prio, args.ttl)
        print("Record upserted successfully.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def cmd_url_list(args):
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
                r.get('wildcard', ''),
                r.get('includePath', '')
            ])
        print(tabulate(table, headers=["ID", "Subdomain", "Location", "Type", "Wildcard", "Path"], tablefmt="simple"))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def cmd_url_set(args):
    api = PorkbunAPI()
    try:
        api.url_create(args.domain, args.location, args.subdomain, args.type, args.wildcard, args.path)
        print("URL forward set successfully.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def cmd_url_delete(args):
    api = PorkbunAPI()
    try:
        api.url_delete(args.domain, args.id)
        print("URL forward deleted successfully.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Porkbun CLI")
    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Configure
    subparsers.add_parser('configure', help='Configure API credentials')

    # Ping
    subparsers.add_parser('ping', help='Test API connection')

    # Domain
    domain_parser = subparsers.add_parser('domain', help='Manage domains')
    domain_sub = domain_parser.add_subparsers(dest='domain_command')
    
    # Domain Search
    search_p = domain_sub.add_parser('search', help='Check domain availability and price')
    search_p.add_argument('domain', help='Domain name')

    # Domain Buy
    buy_p = domain_sub.add_parser('buy', help='Buy a domain')
    buy_p.add_argument('domain', help='Domain name')

    # DNS
    dns_parser = subparsers.add_parser('dns', help='Manage DNS records')
    dns_sub = dns_parser.add_subparsers(dest='dns_command')

    # DNS List
    list_p = dns_sub.add_parser('list', help='List DNS records')
    list_p.add_argument('domain', help='Domain name')

    # DNS Create
    create_p = dns_sub.add_parser('create', help='Create DNS record')
    create_p.add_argument('domain', help='Domain name')
    create_p.add_argument('type', help='Record type (A, CNAME, TXT, etc)')
    create_p.add_argument('content', help='Record content')
    create_p.add_argument('--name', help='Subdomain (optional)')
    create_p.add_argument('--prio', help='Priority (optional)')
    create_p.add_argument('--ttl', help='TTL (optional)')

    # DNS Delete
    delete_p = dns_sub.add_parser('delete', help='Delete DNS record')
    delete_p.add_argument('domain', help='Domain name')
    delete_p.add_argument('id', help='Record ID')
    
    # DNS Upsert
    upsert_p = dns_sub.add_parser('upsert', help='Upsert DNS record (Create or Update)')
    upsert_p.add_argument('domain', help='Domain name')
    upsert_p.add_argument('type', help='Record type (A, CNAME, TXT, etc)')
    upsert_p.add_argument('content', help='Record content')
    upsert_p.add_argument('--name', help='Subdomain (optional)')
    upsert_p.add_argument('--prio', help='Priority (optional)')
    upsert_p.add_argument('--ttl', help='TTL (optional)')
    
    # URL Forwarding
    url_parser = subparsers.add_parser('url', help='Manage URL Forwarding')
    url_sub = url_parser.add_subparsers(dest='url_command')
    
    # URL List
    url_list = url_sub.add_parser('list', help='List URL forwards')
    url_list.add_argument('domain', help='Domain name')
    
    # URL Set
    url_set = url_sub.add_parser('set', help='Set URL forward')
    url_set.add_argument('domain', help='Domain name')
    url_set.add_argument('location', help='Destination URL')
    url_set.add_argument('--subdomain', help='Subdomain (optional)')
    url_set.add_argument('--type', choices=['301', '302', '307'], default='302', help='Redirect type')
    url_set.add_argument('--wildcard', action='store_true', help='Wildcard include')
    url_set.add_argument('--path', action='store_true', help='Include path')
    
    # URL Delete
    url_del = url_sub.add_parser('delete', help='Delete URL forward')
    url_del.add_argument('domain', help='Domain name')
    url_del.add_argument('id', help='Record ID')

    args = parser.parse_args()

    if args.command == 'configure':
        cmd_configure(args)
    elif args.command == 'ping':
        cmd_ping(args)
    elif args.command == 'domain':
        if args.domain_command == 'search':
            cmd_domain_search(args)
        elif args.domain_command == 'buy':
            cmd_domain_buy(args)
        else:
            domain_parser.print_help()
    elif args.command == 'dns':
         if args.dns_command == 'list':
             cmd_dns_list(args)
         elif args.dns_command == 'create':
             cmd_dns_create(args)
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
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Configure
    subparsers.add_parser('configure', help='Configure API credentials')

    # Ping
    subparsers.add_parser('ping', help='Test API connection')

    # Domain
    domain_parser = subparsers.add_parser('domain', help='Manage domains')
    domain_sub = domain_parser.add_subparsers(dest='domain_command')
    
    # Domain Search
    search_p = domain_sub.add_parser('search', help='Check domain availability and price')
    search_p.add_argument('domain', help='Domain name')

    # Domain Buy
    buy_p = domain_sub.add_parser('buy', help='Buy a domain')
    buy_p.add_argument('domain', help='Domain name')

    # DNS
    dns_parser = subparsers.add_parser('dns', help='Manage DNS records')
    dns_sub = dns_parser.add_subparsers(dest='dns_command')

    # DNS List
    list_p = dns_sub.add_parser('list', help='List DNS records')
    list_p.add_argument('domain', help='Domain name')

    # DNS Create
    create_p = dns_sub.add_parser('create', help='Create DNS record')
    create_p.add_argument('domain', help='Domain name')
    create_p.add_argument('type', help='Record type (A, CNAME, TXT, etc)')
    create_p.add_argument('content', help='Record content')
    create_p.add_argument('--name', help='Subdomain (optional)')
    create_p.add_argument('--prio', help='Priority (optional)')
    create_p.add_argument('--ttl', help='TTL (optional)')

    # DNS Delete
    delete_p = dns_sub.add_parser('delete', help='Delete DNS record')
    delete_p.add_argument('domain', help='Domain name')
    delete_p.add_argument('id', help='Record ID')

    args = parser.parse_args()

    if args.command == 'configure':
        cmd_configure(args)
    elif args.command == 'ping':
        cmd_ping(args)
    elif args.command == 'domain':
        if args.domain_command == 'search':
            cmd_domain_search(args)
        elif args.domain_command == 'buy':
            cmd_domain_buy(args)
        else:
            domain_parser.print_help()
    elif args.command == 'dns':
         if args.dns_command == 'list':
             cmd_dns_list(args)
         elif args.dns_command == 'create':
             cmd_dns_create(args)
         elif args.dns_command == 'delete':
             cmd_dns_delete(args)
         else:
             dns_parser.print_help()
    else:
    # DNS Upsert
    upsert_p = dns_sub.add_parser('upsert', help='Upsert DNS record (Create or Update)')
    upsert_p.add_argument('domain', help='Domain name')
    upsert_p.add_argument('type', help='Record type (A, CNAME, TXT, etc)')
    upsert_p.add_argument('content', help='Record content')
    upsert_p.add_argument('--name', help='Subdomain (optional)')
    upsert_p.add_argument('--prio', help='Priority (optional)')
    upsert_p.add_argument('--ttl', help='TTL (optional)')
    
    # URL Forwarding
    url_parser = subparsers.add_parser('url', help='Manage URL Forwarding')
    url_sub = url_parser.add_subparsers(dest='url_command')
    
    # URL List
    url_list = url_sub.add_parser('list', help='List URL forwards')
    url_list.add_argument('domain', help='Domain name')
    
    # URL Set
    url_set = url_sub.add_parser('set', help='Set URL forward')
    url_set.add_argument('domain', help='Domain name')
    url_set.add_argument('location', help='Destination URL')
    url_set.add_argument('--subdomain', help='Subdomain (optional)')
    url_set.add_argument('--type', choices=['301', '302', '307'], default='302', help='Redirect type')
    url_set.add_argument('--wildcard', action='store_true', help='Wildcard include')
    url_set.add_argument('--path', action='store_true', help='Include path')
    
    # URL Delete
    url_del = url_sub.add_parser('delete', help='Delete URL forward')
    url_del.add_argument('domain', help='Domain name')
    url_del.add_argument('id', help='Record ID')

    # DNS Upsert
    upsert_p = dns_sub.add_parser('upsert', help='Upsert DNS record (Create or Update)')
    upsert_p.add_argument('domain', help='Domain name')
    upsert_p.add_argument('type', help='Record type (A, CNAME, TXT, etc)')
    upsert_p.add_argument('content', help='Record content')
    upsert_p.add_argument('--name', help='Subdomain (optional)')
    upsert_p.add_argument('--prio', help='Priority (optional)')
    upsert_p.add_argument('--ttl', help='TTL (optional)')
    
    # URL Forwarding
    url_parser = subparsers.add_parser('url', help='Manage URL Forwarding')
    url_sub = url_parser.add_subparsers(dest='url_command')
    
    # URL List
    url_list = url_sub.add_parser('list', help='List URL forwards')
    url_list.add_argument('domain', help='Domain name')
    
    # URL Set
    url_set = url_sub.add_parser('set', help='Set URL forward')
    url_set.add_argument('domain', help='Domain name')
    url_set.add_argument('location', help='Destination URL')
    url_set.add_argument('--subdomain', help='Subdomain (optional)')
    url_set.add_argument('--type', choices=['301', '302', '307'], default='302', help='Redirect type')
    url_set.add_argument('--wildcard', action='store_true', help='Wildcard include')
    url_set.add_argument('--path', action='store_true', help='Include path')
    
    # URL Delete
    url_del = url_sub.add_parser('delete', help='Delete URL forward')
    url_del.add_argument('domain', help='Domain name')
    url_del.add_argument('id', help='Record ID')

    args = parser.parse_args()

    if args.command == 'configure':
        cmd_configure(args)
    elif args.command == 'ping':
        cmd_ping(args)
    elif args.command == 'domain':
        if args.domain_command == 'search':
            cmd_domain_search(args)
        elif args.domain_command == 'buy':
            cmd_domain_buy(args)
        else:
            domain_parser.print_help()
    elif args.command == 'dns':
         if args.dns_command == 'list':
             cmd_dns_list(args)
         elif args.dns_command == 'create':
             cmd_dns_create(args)
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
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
