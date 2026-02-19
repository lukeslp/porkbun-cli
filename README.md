<<<<<<< HEAD
# porkbun-cli

![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)
![PyPI](https://img.shields.io/pypi/v/porkbun-cli.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

A command-line tool for managing domains and DNS records through the [Porkbun API](https://porkbun.com/api/json/v3/documentation).

```
$ porkbun dns list example.com

ID          Type  Name               Content         Prio  TTL
----------  ----  -----------------  --------------  ----  -----
123456789   A     example.com        203.0.113.1           600
123456790   MX    example.com        mail.example.com  10  3600
123456791   TXT   example.com        v=spf1 ...            3600
```

## Install

```bash
pip install porkbun-cli

# With interactive menu support
pip install porkbun-cli[interactive]
```

## Setup

Get your API keys from [porkbun.com/account/api](https://porkbun.com/account/api). You need to enable API access per-domain in your Porkbun account settings.

Then run:

```bash
porkbun configure
```

This prompts for your API key and secret, then saves them to `~/.config/porkbun-cli/config.json` with `600` permissions.

To verify the connection works:

```bash
porkbun ping
# Success! Your IP: 203.0.113.42
```

## Commands

### Domains

```bash
# List all domains in your account
porkbun domain list

# Check availability and pricing for a domain
porkbun domain search coolname.com

# Register a domain (prompts for confirmation before charging)
porkbun domain buy coolname.com

# View nameservers
porkbun domain ns example.com

# Set custom nameservers
porkbun domain ns-set example.com ns1.host.com ns2.host.com

# Download SSL certificate bundle
porkbun domain ssl example.com --output ./certs/example
# Writes example.crt, example.key, example.ca
```

### DNS Records

```bash
# List all records
porkbun dns list example.com

# Filter by type
porkbun dns list example.com --type TXT

# Create records
porkbun dns create example.com A 203.0.113.1 --name www
porkbun dns create example.com MX mail.example.com --prio 10
porkbun dns create example.com TXT "v=spf1 include:example.com ~all"
porkbun dns create example.com CNAME target.example.com --name blog

# Edit a record by its ID
porkbun dns edit example.com 123456789 A 203.0.113.2 --name www

# Upsert — creates the record if it doesn't exist, updates it if it does
porkbun dns upsert example.com A 203.0.113.1 --name www

# Delete by ID
porkbun dns delete example.com 123456789
```

Supported record types: `A`, `AAAA`, `CNAME`, `ALIAS`, `MX`, `TXT`, `NS`, `SRV`, `TLSA`, `CAA`, `HTTPS`, `SVCB`, `SSHFP`

### URL Forwarding

```bash
# List URL forwards
porkbun url list example.com

# Set a redirect (302 by default)
porkbun url set example.com https://destination.com

# Set a permanent 301 redirect from a subdomain
porkbun url set example.com https://destination.com --subdomain blog --type 301

# Wildcard redirect with path passthrough
porkbun url set example.com https://destination.com --wildcard --path

# Delete a forward
porkbun url delete example.com 987654321
```

### Bulk Export / Import

Good for backups or migrating DNS between domains.

```bash
# Export all DNS records to JSON
porkbun bulk export example.com -o records.json

# Export as CSV
porkbun bulk export example.com --format csv -o records.csv

# Print to stdout (pipe-friendly)
porkbun bulk export example.com

# Preview what an import would do without changing anything
porkbun bulk import records.json --dry-run

# Import to original domain (reads domain from JSON file)
porkbun bulk import records.json

# Import to a different domain
porkbun bulk import records.json --domain newdomain.com
```

The JSON format supports an optional `action` field per record: `create` (default), `upsert`, or `delete`.

### Interactive Mode

Install with `[interactive]` to get a menu-driven interface instead of remembering all the flags:

```bash
porkbun interactive
# or shorthand:
porkbun i
```

Fetches your domain list on startup so you can pick from a menu — handy when you manage several domains.

## Config File

Credentials are stored at `~/.config/porkbun-cli/config.json`:

```json
{
    "apikey": "pk1_...",
    "secretapikey": "sk1_..."
}
```

The file is created with `600` permissions by `porkbun configure`. Do not commit it.

You can also pass keys directly via environment or by instantiating `PorkbunAPI` programmatically — see the `api.py` module if you want to use the client in your own scripts.

## Requirements

- Python 3.8+
- `requests`
- `tabulate`
- `questionary` (only for `porkbun interactive`, installed via `pip install porkbun-cli[interactive]`)

## License

MIT — see [LICENSE](LICENSE).

## Author

[Luke Steuber](https://lukesteuber.com) · [GitHub](https://github.com/lukeslp/porkbun-cli) · [Bluesky](https://bsky.app/profile/lukesteuber.com)
=======
# Porkbun CLI

![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Status: Active](https://img.shields.io/badge/status-active-success.svg)

A command-line interface for managing domains and DNS records through the [Porkbun API](https://porkbun.com/api/json/v3/documentation).

## Features

- **Domain Management** - List and view domain information
- **DNS Records** - Full CRUD operations (Create, Read, Update, Delete)
- **Availability Check** - Check if domains are available for registration
- **Table Output** - Clean, formatted table display
- **Secure Config** - Credentials stored in local config file

## Installation

```bash
# Clone the repository
git clone https://github.com/lukeslp/porkbun-cli.git
cd porkbun-cli

# Install dependencies
pip install -r requirements.txt

# Make executable (optional)
chmod +x porkbun.py
```

## Configuration

### Get API Keys

1. Log in to [Porkbun.com](https://porkbun.com)
2. Navigate to **Account > API Access**
3. Generate API key and secret key
4. Enable API access for your account

### Configure CLI

```bash
# Interactive setup
./porkbun.py configure

# Or create config manually
mkdir -p ~/.config/porkbun-cli
cat > ~/.config/porkbun-cli/config.json << EOF
{
  "apikey": "pk1_your_api_key_here",
  "secretapikey": "sk1_your_secret_key_here"
}
EOF
```

## Usage

### Domain Commands

```bash
# List all domains
./porkbun.py list

# Get domain info
./porkbun.py info example.com

# Check domain availability
./porkbun.py available example.com
```

### DNS Commands

```bash
# List DNS records
./porkbun.py records example.com

# Add A record
./porkbun.py add-record example.com A www 192.0.2.1

# Add CNAME record
./porkbun.py add-record example.com CNAME blog target.example.com

# Add MX record with priority
./porkbun.py add-record example.com MX @ mail.example.com --prio 10

# Delete record by ID
./porkbun.py delete-record example.com 123456789
```

### Test Connection

```bash
# Verify API credentials
./porkbun.py ping
```

## Dependencies

- `requests` - HTTP client
- `tabulate` - Table formatting

## File Structure

```
porkbun-cli/
├── porkbun.py         # Main CLI script
├── requirements.txt   # Python dependencies
├── LICENSE            # MIT License
└── README.md          # This file
```

## Security

- API keys stored in `~/.config/porkbun-cli/config.json`
- Config file permissions should be `600` (user-only)
- Never commit credentials to version control
- All API calls use HTTPS

## API Reference

Uses Porkbun API v3:
- Base URL: `https://api.porkbun.com/api/json/v3`
- [Official Documentation](https://porkbun.com/api/json/v3/documentation)

## License

MIT License - see [LICENSE](LICENSE) file

## Author

**Luke Steuber**

- Website: [dr.eamer.dev](https://dr.eamer.dev)
- Bluesky: [@dr.eamer.dev](https://bsky.app/profile/dr.eamer.dev)
>>>>>>> origin/master
