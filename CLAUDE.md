# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Porkbun CLI** is a command-line interface for managing domains and DNS records through the Porkbun API. This tool provides easy domain management from the terminal.

## Quick Start

```bash
cd /home/coolhand/projects/porkbun-cli

# Install dependencies
pip install -r requirements.txt

# Configure API credentials
./porkbun.py configure

# List domains
./porkbun.py list

# Show help
./porkbun.py --help
```

## Installation

```bash
# Install required packages
pip install -r requirements.txt

# Make executable
chmod +x porkbun.py
```

## Configuration

### Initial Setup

Run the configure command to set up API credentials:

```bash
./porkbun.py configure
```

This will prompt for:
- API Key
- Secret API Key

Credentials are stored in: `~/.config/porkbun-cli/config.json`

### Manual Configuration

Alternatively, create config file manually:

```bash
mkdir -p ~/.config/porkbun-cli
cat > ~/.config/porkbun-cli/config.json << EOF
{
  "apikey": "pk1_your_api_key_here",
  "secretapikey": "sk1_your_secret_key_here"
}
EOF
```

### Getting API Keys

1. Log in to Porkbun.com
2. Navigate to Account > API Access
3. Generate API key and secret key
4. Enable API access for your account

## Usage

### List Domains

```bash
./porkbun.py list
```

Shows all domains in your account in table format.

### DNS Record Management

```bash
# List DNS records for a domain
./porkbun.py records example.com

# Add DNS record
./porkbun.py add-record example.com A www 192.0.2.1

# Delete DNS record
./porkbun.py delete-record example.com RECORD_ID
```

### Domain Information

```bash
# Get domain info
./porkbun.py info example.com

# Check domain availability
./porkbun.py available example.com
```

## Features

- Domain listing and management
- DNS record CRUD operations (Create, Read, Update, Delete)
- Domain availability checking
- Table-formatted output for easy reading
- Configuration storage for credentials
- Error handling and validation

## API Endpoints

Uses Porkbun API v3:
- Base URL: `https://api.porkbun.com/api/json/v3`
- Authentication via API key and secret key in request payload

## Dependencies

- **requests** - HTTP client for API calls
- **tabulate** - Formatted table output

See `requirements.txt` for complete list.

## File Structure

```
porkbun-cli/
├── porkbun.py          # Main CLI script
└── requirements.txt    # Python dependencies
```

## Configuration File Location

- Linux/Mac: `~/.config/porkbun-cli/config.json`
- Windows: `%USERPROFILE%\.config\porkbun-cli\config.json`

## Error Handling

The CLI handles common errors:
- Missing API credentials
- Invalid domain names
- API request failures
- Network connectivity issues

## Security Notes

- API keys are stored locally in config file
- Never commit config.json to version control
- Config file permissions should be user-only (600)
- Use HTTPS for all API communication

## Current Status

**Active** - Working Porkbun domain management CLI

## Related Tools

- Porkbun web interface: https://porkbun.com
- Porkbun API documentation: https://porkbun.com/api/json/v3/documentation

## Troubleshooting

### "API key and Secret key are required"
Run `./porkbun.py configure` to set up credentials.

### "Error loading config"
Check config file exists and is valid JSON:
```bash
cat ~/.config/porkbun-cli/config.json
```

### API errors
- Verify API keys are correct
- Check API access is enabled in Porkbun account
- Ensure domain is in your account

## Future Enhancements

Potential features:
- Domain registration via CLI
- Bulk DNS record operations
- DNS record templates
- Domain renewal management
- SSL certificate management

## Notes

- Requires active Porkbun account
- API access must be enabled
- Respects Porkbun API rate limits
- All operations are real-time (no caching)
