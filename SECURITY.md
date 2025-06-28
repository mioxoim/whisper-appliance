# Security Policy

## Supported Versions

We actively support the following versions of WhisperS2T Appliance:

| Version | Supported          |
| ------- | ------------------ |
| 0.6.x   | :white_check_mark: |
| 0.5.x   | :x:                |
| < 0.5   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security vulnerability in WhisperS2T Appliance, please report it responsibly.

### How to Report

1. **Do NOT** create a public GitHub issue for security vulnerabilities
2. **Do NOT** disclose the vulnerability publicly until it has been addressed
3. **DO** send details to the project maintainers via private communication

### What to Include

Please include the following information in your report:

- **Description** of the vulnerability
- **Steps to reproduce** the issue
- **Potential impact** assessment
- **Suggested fix** (if you have one)
- **Your contact information** for follow-up

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Varies based on severity and complexity

### Severity Guidelines

#### Critical
- Remote code execution
- Authentication bypass
- Data exposure of sensitive information

#### High
- Local privilege escalation
- Container escape
- Service disruption

#### Medium
- Information disclosure
- Denial of service
- Input validation issues

#### Low
- Configuration issues
- Minor information leaks

## Security Best Practices

### Container Deployment
- Keep base OS updated (`apt update && apt upgrade`)
- Use non-root user for application (`whisper` user)
- Enable firewall (`ufw enable`)
- Regular security updates
- Monitor container resources

### Network Security
- Use HTTPS in production (nginx SSL termination)
- Restrict network access with firewall rules
- Use strong authentication for SSH access
- Consider VPN for remote access

### File Security
- Validate uploaded audio files
- Implement file size limits
- Clean up temporary files
- Secure file permissions

### Service Security
- Run services with minimal privileges
- Use systemd security features
- Monitor service logs
- Regular backup of configurations

## Security Considerations

### Audio File Uploads
- Files are temporarily stored and processed
- Automatic cleanup after processing
- File type and size validation
- No persistent storage of user data

### Container Security
- Privileged containers may be required for some features
- GPU access requires additional permissions
- Network isolation recommended
- Regular container updates needed

### API Security
- No authentication by default (add nginx auth if needed)
- Rate limiting recommended for production
- Input validation on all endpoints
- Secure error handling

## Known Security Limitations

1. **No Built-in Authentication**: The web interface has no user authentication by default
2. **File Upload Security**: Basic validation only - consider additional scanning
3. **Network Exposure**: Service binds to all interfaces by default
4. **Container Privileges**: Some deployments may require privileged containers

## Recommended Production Hardening

```bash
# Firewall configuration
ufw default deny incoming
ufw allow ssh
ufw allow 5000/tcp
ufw enable

# Service security
systemctl enable fail2ban  # if available
systemctl enable unattended-upgrades  # automatic security updates

# Nginx security headers (add to config)
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header X-XSS-Protection "1; mode=block";
```

---

**Remember**: Security is a shared responsibility. Keep your systems updated and follow security best practices for your deployment environment.