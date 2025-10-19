# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Security Best Practices

### Production Deployment

1. **Change the Secret Key**: Always set a strong, random `SECRET_KEY` in production
2. **Use HTTPS**: Configure SSL/TLS certificates for encrypted communication
3. **Firewall Configuration**: Restrict access to server ports (5000, 8080)
4. **Regular Updates**: Keep all dependencies up to date
5. **Input Validation**: All user inputs are validated and sanitized
6. **Database Security**: SQLite databases should have appropriate file permissions

### Environment Variables

Never commit `.env` files to version control. Always use `.env.example` as a template.

### Dependency Scanning

Run security checks regularly:

```bash
# Install security tools
pip install safety bandit

# Check for known vulnerabilities
safety check

# Run security linter
bandit -r src/
```

## Reporting a Vulnerability

Please report security vulnerabilities to: security@example.com

We will respond within 48 hours and provide updates every 72 hours until resolution.