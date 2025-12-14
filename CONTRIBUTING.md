# Contributing to Porkbun CLI

Thank you for your interest in contributing to Porkbun CLI!

## How to Contribute

I welcome contributions that enhance the CLI tool while maintaining its simplicity and reliability. Here are some ways you can help:

### Bug Reports

If you find a bug, please open an issue with:
- A clear description of the problem
- Steps to reproduce the issue
- Expected vs. actual behavior
- Your Python version and operating system

### Feature Suggestions

I'm open to suggestions that:
- Enhance domain and DNS management capabilities
- Improve user experience
- Add useful Porkbun API features
- Maintain the tool's simplicity

### Code Contributions

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes**
4. **Test thoroughly** with real Porkbun API credentials
5. **Commit with clear messages**: `git commit -m "Add feature: description"`
6. **Push to your fork**: `git push origin feature/your-feature-name`
7. **Open a Pull Request**

### Code Style

- Use consistent indentation (4 spaces for Python)
- Follow PEP 8 style guidelines
- Write clear, descriptive variable and function names
- Add docstrings for functions and classes
- Keep functions focused and single-purpose

### Testing

Before submitting a PR:
- Test all commands with your Porkbun API credentials
- Verify table output formatting
- Test error handling (invalid domains, API errors, etc.)
- Ensure config file handling works correctly
- Test on both Python 3.8+ versions

### Areas for Contribution

**High Priority**:
- Bug fixes
- Error handling improvements
- Additional Porkbun API features
- Documentation improvements

**Medium Priority**:
- Output formatting options (JSON, CSV)
- Batch operations
- Domain search functionality
- SSL certificate management

**Low Priority**:
- Shell completion scripts
- Configuration management improvements
- Colored output options

### What I'm Not Looking For

To keep the tool simple and focused:
- Web UI or GUI
- Features unrelated to Porkbun API
- Complex dependencies
- Breaking changes to existing commands

## Development Setup

```bash
# Clone the repository
git clone https://github.com/lukeslp/porkbun-cli.git
cd porkbun-cli

# Install dependencies
pip install -r requirements.txt

# Set up API credentials
# Create ~/.porkbun_config with your API key and secret
```

### API Credentials

You'll need Porkbun API credentials for testing:
1. Log in to your Porkbun account
2. Go to API Access section
3. Generate API key and secret
4. Save them in `~/.porkbun_config`:
   ```
   api_key=your_api_key_here
   api_secret=your_api_secret_here
   ```

## Command Structure

The CLI follows this pattern:
```bash
python porkbun.py <command> [arguments] [options]
```

Commands:
- `list` - List all domains
- `view <domain>` - View domain details
- `dns-list <domain>` - List DNS records
- `dns-create <domain> <type> <content>` - Create DNS record
- `dns-delete <domain> <id>` - Delete DNS record
- `check <domain>` - Check domain availability

## Questions?

Feel free to open an issue for any questions about contributing.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Author**: Luke Steuber (dr.eamer.dev)
**Project**: Porkbun CLI
