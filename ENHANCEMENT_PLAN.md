# Porkbun CLI Enhancement Plan

## Executive Summary

The Porkbun CLI is a functional domain and DNS management tool that needs three key enhancements:
1. **Interactive CLI mode** for user-friendly guided operations
2. **Bulk operations** for efficient DNS management
3. **Extended API coverage** for full Porkbun API feature set

## Current State Analysis

### What We Have (416 lines)
- ✅ DNS record management (list, create, edit, delete, upsert)
- ✅ URL forwarding (list, set, delete)
- ✅ Domain search/availability checking
- ✅ Domain purchase functionality
- ✅ Configuration management
- ✅ Basic auth and error handling

### Known Issues
- 🐛 **domain_create()** method incomplete (lines 99-105) - builds payload but never sends request
- ⚠️ No validation for DNS record types
- ⚠️ No batch/bulk operations
- ⚠️ Missing several API features

## Complete Porkbun API V3 Capabilities

### Currently Implemented
| Category | Feature | Status |
|----------|---------|--------|
| DNS | Create/Edit/Delete/Retrieve records | ✅ Implemented |
| URL Forwarding | Add/Delete/Retrieve forwards | ✅ Implemented |
| Domain | Check availability/pricing | ✅ Implemented |
| Domain | Purchase domain | ⚠️ Buggy (incomplete) |
| Auth | Ping endpoint | ✅ Implemented |

### Missing API Features
| Category | Feature | Priority | API Endpoint |
|----------|---------|----------|--------------|
| DNS | Edit by subdomain/type (not just ID) | High | `/dns/editByNameType/{domain}` |
| DNS | Delete by subdomain/type | High | `/dns/deleteByNameType/{domain}` |
| DNS | Retrieve specific record types | Medium | `/dns/retrieve/{domain}?type=A` |
| DNSSEC | Retrieve DNSSEC records | Medium | `/dns/retrieveDnssec/{domain}` |
| DNSSEC | Create DNSSEC records | Medium | `/dns/createDnssec/{domain}` |
| DNSSEC | Delete DNSSEC records | Low | `/dns/deleteDnssec/{domain}` |
| SSL | Retrieve SSL bundle | High | `/ssl/retrieve/{domain}` |
| Nameservers | Update nameservers | High | `/domain/updateNs/{domain}` |
| Nameservers | Get nameservers | High | `/domain/getNs/{domain}` |
| Domain | List all domains | High | `/domain/listAll` |
| Pricing | Get pricing for all TLDs | Low | `/pricing/get` |

### API Record Type Support
- A, AAAA (IPv4/IPv6 addresses)
- CNAME, ALIAS (domain aliases)
- MX (mail servers)
- TXT (text records)
- NS (nameservers)
- SRV (service records)
- TLSA (TLS authentication)
- CAA (certificate authority authorization)
- HTTPS, SVCB (HTTP service bindings)
- SSHFP (SSH fingerprints)

## Interactive CLI Library Evaluation

### Recommended: Questionary

**Why Questionary:**
- ✅ Actively maintained (v2.1.1, August 2025)
- ✅ Modern prompt_toolkit 3.0.0+ support
- ✅ Cross-platform (Unix, Windows, macOS)
- ✅ Minimal dependencies
- ✅ Clean, simple API
- ✅ Good documentation
- ✅ Requires Python 3.9+ (we're on 3.10+)

**Alternative: InquirerPy**
- More features and customization
- Slightly heavier dependency
- Better for complex UIs

**Decision:** Start with Questionary for simplicity, can upgrade to InquirerPy if needed.

### Interactive Patterns to Implement

#### 1. Main Menu Mode
```
$ ./porkbun.py interactive

What would you like to do?
❯ Manage DNS Records
  Manage URL Forwarding
  Manage Domains
  View SSL Certificates
  Configure Settings
  Exit
```

#### 2. Guided Operations
```
$ ./porkbun.py dns interactive

Select domain: example.com
What would you like to do?
❯ Add new DNS record
  Edit existing record
  Delete record
  View all records

[Add new record selected]
Record type: [A ▼]
Subdomain: www
IP Address: 192.0.2.1
TTL (optional): [600]
Priority (optional): []

✓ Created A record for www.example.com → 192.0.2.1
```

#### 3. Bulk Operations
```
$ ./porkbun.py dns bulk --from-file records.json
$ ./porkbun.py dns bulk --from-csv records.csv

Processing 15 records...
✓ Created A record: www → 192.0.2.1
✓ Created A record: mail → 192.0.2.2
✓ Created MX record: @ → mail.example.com
...
Summary: 15 created, 0 failed
```

## Architecture Design

### File Structure (Single File Maintained)
Keep the single-file design for simplicity:
```
porkbun-cli/
├── porkbun.py (enhanced, ~800 lines estimated)
├── requirements.txt (add questionary)
├── CLAUDE.md
├── ENHANCEMENT_PLAN.md (this file)
└── examples/
    ├── bulk_records.json
    └── bulk_records.csv
```

### Code Organization Within porkbun.py
```python
# 1. Imports and constants
# 2. PorkbunAPI class (enhanced with new methods)
# 3. Interactive UI helper functions (questionary-based)
# 4. Command handlers (existing + new)
# 5. Bulk operation handlers
# 6. Main parser setup
# 7. Entry point
```

### New Classes/Functions

#### Interactive UI Helpers
```python
def interactive_main_menu():
    """Show main interactive menu"""

def interactive_domain_selector(api):
    """Let user select from their domains"""

def interactive_dns_manager(api, domain):
    """Interactive DNS record management"""

def interactive_record_builder(record_type):
    """Build DNS record interactively"""
```

#### Bulk Operations
```python
def bulk_dns_from_file(api, filepath, format='json'):
    """Load and process bulk DNS operations from file"""

def bulk_dns_from_stdin(api):
    """Process bulk operations from stdin (pipe-friendly)"""

def validate_bulk_records(records):
    """Validate bulk record format before processing"""
```

#### New API Methods
```python
class PorkbunAPI:
    # Domain management
    def domain_list_all(self):
    def nameserver_get(self, domain):
    def nameserver_update(self, domain, nameservers):

    # SSL
    def ssl_retrieve(self, domain):

    # Enhanced DNS
    def dns_retrieve_by_type(self, domain, record_type):
    def dns_edit_by_name_type(self, domain, subdomain, record_type, ...):
    def dns_delete_by_name_type(self, domain, subdomain, record_type):

    # DNSSEC
    def dnssec_retrieve(self, domain):
    def dnssec_create(self, domain, ...):
    def dnssec_delete(self, domain, record_id):
```

## Implementation Phases

### Phase 1: Bug Fixes & Core Enhancements (1-2 hours)
1. Fix domain_create bug (add missing API call)
2. Add validation for DNS record types
3. Add domain_list_all method
4. Add nameserver management
5. Add SSL certificate retrieval

### Phase 2: Interactive Mode (2-3 hours)
1. Add questionary dependency
2. Implement main interactive menu
3. Implement interactive DNS manager
4. Implement interactive URL forward manager
5. Implement guided domain operations
6. Add `--interactive` or `-i` flag to existing commands

### Phase 3: Bulk Operations (2-3 hours)
1. Design JSON/CSV format for bulk records
2. Implement file parser (JSON and CSV)
3. Implement bulk DNS record creation
4. Implement bulk record deletion
5. Add validation and dry-run mode
6. Add progress reporting
7. Create example files

### Phase 4: Polish & Documentation (1 hour)
1. Update CLAUDE.md with new features
2. Create example files
3. Add usage examples to help text
4. Test all new features
5. Update requirements.txt

## Bulk Operation Format Design

### JSON Format
```json
{
  "domain": "example.com",
  "records": [
    {
      "action": "create",
      "type": "A",
      "name": "www",
      "content": "192.0.2.1",
      "ttl": 600
    },
    {
      "action": "create",
      "type": "MX",
      "name": "",
      "content": "mail.example.com",
      "prio": 10
    },
    {
      "action": "delete",
      "id": "12345"
    }
  ]
}
```

### CSV Format
```csv
action,type,name,content,prio,ttl
create,A,www,192.0.2.1,,600
create,A,mail,192.0.2.2,,600
create,MX,,mail.example.com,10,
create,TXT,_dmarc,v=DMARC1; p=none,,
delete,,,,,12345
```

## Command Line Interface Design

### New Commands
```bash
# Interactive mode
./porkbun.py interactive
./porkbun.py dns interactive [domain]
./porkbun.py url interactive [domain]
./porkbun.py domain interactive

# Bulk operations
./porkbun.py dns bulk --file records.json [--dry-run]
./porkbun.py dns bulk --csv records.csv [--dry-run]
./porkbun.py dns export example.com --format json > records.json

# New features
./porkbun.py domain list
./porkbun.py ssl get example.com
./porkbun.py nameserver get example.com
./porkbun.py nameserver set example.com ns1.example.com ns2.example.com
```

### Enhanced Existing Commands
```bash
# Add interactive mode to existing commands
./porkbun.py dns list example.com --interactive  # Shows menu after listing
./porkbun.py configure --interactive  # Guided configuration
```

## User Experience Examples

### Example 1: Interactive DNS Management
```
$ ./porkbun.py dns interactive example.com

Current DNS records for example.com:
  1. A     www        → 192.0.2.1
  2. A     mail       → 192.0.2.2
  3. MX    @          → mail.example.com (priority: 10)
  4. TXT   _dmarc     → v=DMARC1; p=none

What would you like to do?
❯ Add new record
  Edit existing record
  Delete record
  Refresh list
  Switch domain
  Exit

[Add new record]
Record type: [Use arrows to select]
❯ A
  AAAA
  CNAME
  MX
  TXT
  NS
  SRV
  CAA

Subdomain (blank for root): www2
IP Address: 192.0.2.3
TTL (leave blank for default):

✓ Created A record: www2.example.com → 192.0.2.3
```

### Example 2: Bulk DNS Import
```
$ cat records.json
{
  "domain": "example.com",
  "records": [
    {"action": "create", "type": "A", "name": "app1", "content": "192.0.2.10"},
    {"action": "create", "type": "A", "name": "app2", "content": "192.0.2.11"},
    {"action": "create", "type": "A", "name": "app3", "content": "192.0.2.12"}
  ]
}

$ ./porkbun.py dns bulk --file records.json
Processing 3 records for example.com...
✓ Created A record: app1 → 192.0.2.10
✓ Created A record: app2 → 192.0.2.11
✓ Created A record: app3 → 192.0.2.12

Summary:
  ✓ 3 created
  ✗ 0 failed
  ⊘ 0 skipped
```

### Example 3: Domain List with Interactive Follow-up
```
$ ./porkbun.py domain list --interactive

Your domains:
  1. example.com (expires: 2026-12-01)
  2. test.com (expires: 2026-06-15)
  3. mysite.org (expires: 2025-12-30)

Select a domain to manage:
❯ example.com
  test.com
  mysite.org
  [Exit]

[example.com selected]
What would you like to do with example.com?
❯ View DNS records
  Manage URL forwarding
  Get SSL certificate
  View nameservers
  Back to domain list
```

## Testing Strategy

### Manual Tests
- [ ] Interactive mode flows (all menus)
- [ ] Bulk import from JSON
- [ ] Bulk import from CSV
- [ ] Error handling in interactive mode
- [ ] Dry-run mode for bulk operations

### Edge Cases
- [ ] Empty domain list
- [ ] Invalid bulk file format
- [ ] API errors during bulk operations
- [ ] Keyboard interrupts (Ctrl+C) in interactive mode
- [ ] Invalid record types
- [ ] Missing required fields

### Cross-Platform
- [ ] Test on Linux (primary)
- [ ] Test on macOS (if available)
- [ ] Test on Windows (if available)

## Dependencies Update

### Current
```
requests
tabulate
```

### Enhanced
```
requests>=2.31.0
tabulate>=0.9.0
questionary>=2.1.0
```

## Backward Compatibility

All existing commands will continue to work exactly as before. New features are:
- Additive (new commands)
- Optional (--interactive flags)
- Non-breaking (enhanced existing commands maintain same interface)

## Security Considerations

1. **Bulk operations**: Add confirmation prompts for destructive operations
2. **Dry-run mode**: Always available for bulk operations
3. **API key handling**: No changes to existing secure storage
4. **Input validation**: Validate all bulk import data before API calls

## Success Criteria

1. ✅ All existing functionality works unchanged
2. ✅ Interactive mode provides guided experience for all operations
3. ✅ Bulk operations handle 100+ records efficiently
4. ✅ All documented Porkbun API features are accessible
5. ✅ Error messages are clear and actionable
6. ✅ Documentation is complete and accurate
7. ✅ Code remains maintainable (single file, clear organization)

## Timeline Estimate

- Phase 1 (Bug fixes & core): 1-2 hours
- Phase 2 (Interactive mode): 2-3 hours
- Phase 3 (Bulk operations): 2-3 hours
- Phase 4 (Documentation): 1 hour

**Total: 6-9 hours of development work**

## Questions Answered

### 1. What can the Porkbun API actually do?
The API supports:
- ✅ DNS record management (all common types)
- ✅ URL forwarding
- ✅ Domain registration and availability checking
- ✅ SSL certificate retrieval
- ✅ Nameserver management
- ✅ DNSSEC management
- ✅ Pricing information

Missing from API: Domain renewals, transfers, auto-renew settings (must use web interface)

### 2. What interactive CLI patterns would work well?
- Main menu → category menu → operation flow
- Domain selector (from account domains)
- Record type selector with validation
- Confirmation prompts for destructive actions
- Table display → action menu pattern
- Breadcrumb navigation (show current context)

### 3. Should we use questionary/inquirer?
**Yes, use Questionary** because:
- Actively maintained (2025)
- Modern and lightweight
- Cross-platform
- Simple API
- Python 3.9+ compatible

## Next Steps

1. Review this plan with user
2. Get approval for approach
3. Begin Phase 1 implementation
4. Iterate based on feedback

---

**Author:** Luke Steuber
**Date:** 2025-12-12
**Project:** Porkbun CLI Enhancement
