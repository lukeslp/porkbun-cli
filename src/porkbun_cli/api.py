"""
Porkbun API wrapper
Author: Luke Steuber
"""
import json
import os
import sys

import requests

CONFIG_DIR = os.path.expanduser("~/.config/porkbun-cli")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
API_BASE = "https://api.porkbun.com/api/json/v3"

# DNS record types supported by Porkbun
DNS_TYPES = [
    "A", "AAAA", "CNAME", "ALIAS", "MX", "TXT",
    "NS", "SRV", "TLSA", "CAA", "HTTPS", "SVCB", "SSHFP"
]


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
            # Try to parse JSON even on error responses
            try:
                result = response.json()
            except ValueError:
                response.raise_for_status()
                raise Exception(f"Non-JSON response from {endpoint}")

            if result.get('status') == 'ERROR':
                raise Exception(result.get('message', 'Unknown API error'))

            return result
        except requests.exceptions.ConnectionError as e:
            raise Exception(f"Connection error: {e}")
        except requests.exceptions.Timeout as e:
            raise Exception(f"Request timed out: {e}")

    def ping(self):
        return self._request("ping")

    # Domain methods
    def domain_list(self):
        """List all domains in account"""
        return self._request("domain/listAll")

    def pricing_get(self, tld=None):
        """Get pricing for all TLDs or a specific TLD.
        Returns dict of TLD -> {registration, renewal, transfer, coupons}
        """
        result = self._request("pricing/get")
        pricing = result.get('pricing', {})
        if tld:
            tld = tld.lstrip('.')
            return pricing.get(tld)
        return pricing

    def domain_check(self, domain):
        """Check domain availability via WHOIS and pricing lookup.
        Returns dict with 'available' bool and 'pricing' if available.
        """
        import subprocess
        tld = domain.split('.', 1)[1] if '.' in domain else domain

        # Get pricing for this TLD
        pricing = self.pricing_get(tld)

        # Check availability via whois
        available = None
        try:
            result = subprocess.run(
                ['whois', domain], capture_output=True, text=True, timeout=10
            )
            output = result.stdout.lower()
            if any(s in output for s in ['no match', 'not found', 'no object', 'domain not found', 'no entries']):
                available = True
            elif result.stdout.strip():
                available = False
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # For .app/.dev and others where whois is unreliable, try RDAP
        if available is None:
            try:
                import requests as req
                resp = req.get(f"https://rdap.org/domain/{domain}", timeout=5)
                if resp.status_code == 404:
                    available = True
                elif resp.status_code == 200:
                    available = False
            except Exception:
                pass

        return {
            'domain': domain,
            'available': available,
            'pricing': pricing,
        }

    def domain_create(self, domain, whois_privacy=True, auto_renew=True, years=1):
        """Register a new domain. Automatically looks up cost."""
        tld = domain.split('.', 1)[1] if '.' in domain else domain
        pricing = self.pricing_get(tld)
        if not pricing:
            raise Exception(f"TLD .{tld} not available on Porkbun")

        # Cost is in pennies (integer), pricing is dollars (string)
        cost_dollars = float(pricing['registration']) * years
        cost_pennies = int(round(cost_dollars * 100))

        data = {
            "whoisPrivacy": "yes" if whois_privacy else "no",
            "autoRenew": "yes" if auto_renew else "no",
            "years": years,
            "cost": cost_pennies,
            "agreeToTerms": "yes",
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
