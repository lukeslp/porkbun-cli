# Porkbun CLI

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

- Website: [lukesteuber.com](https://lukesteuber.com)
- GitHub: [@lukeslp](https://github.com/lukeslp)
- Bluesky: [@lukesteuber.com](https://bsky.app/profile/lukesteuber.com)
