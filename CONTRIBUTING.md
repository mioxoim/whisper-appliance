# Contributing to WhisperS2T Appliance

We welcome contributions to the WhisperS2T Appliance project! This document provides guidelines for contributing.

## 🎯 How to Contribute

### 1. Reporting Issues
- Use GitHub Issues to report bugs
- Provide clear reproduction steps
- Include system information (OS, container environment)
- Add logs when relevant

### 2. Feature Requests
- Open a GitHub Issue with the "enhancement" label
- Describe the use case and expected behavior
- Consider the impact on container deployment

### 3. Pull Requests
- Fork the repository
- Create a feature branch (`git checkout -b feature/amazing-feature`)
- Make your changes
- Test with `./test-container.sh`
- Commit with clear messages
- Push to your fork
- Open a Pull Request

## 🧪 Development Setup

### Container Development
```bash
# Clone repository
git clone https://github.com/yourusername/whisper-appliance.git
cd whisper-appliance

# Test in container
./install-container.sh
./test-container.sh
```

### Local Development
```bash
# Setup development environment
./dev.sh dev start
```

## 📋 Code Standards

### Python Code
- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Add docstrings for functions and classes
- Keep functions focused and small

### Shell Scripts
- Use `#!/bin/bash` shebang
- Include error handling (`set -e`)
- Add comments for complex operations
- Test scripts before committing

### Documentation
- Update README.md for major changes
- Add inline comments for complex logic
- Update CHANGELOG.md for user-facing changes
- Include examples in documentation

## 🔍 Testing

### Required Tests
- Container installation must pass `./test-container.sh`
- Web interface accessibility
- Health check endpoints
- Core transcription functionality

### Test Environments
- Ubuntu 22.04 LXC containers (primary)
- Debian 12 LXC containers (secondary)
- Docker containers (alternative)

## 📦 Release Process

### Version Numbering
- Follow semantic versioning (MAJOR.MINOR.PATCH)
- Update version in README.md and CHANGELOG.md
- Tag releases in Git

### Release Checklist
- [ ] All tests pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version numbers updated
- [ ] Container deployment tested
- [ ] Create GitHub release with notes

## 🎯 Contribution Focus Areas

### High Priority
- Container optimization and performance
- Additional Linux distribution support
- GPU acceleration implementation
- Multi-model selection UI

### Medium Priority
- HTTPS/TLS support
- User authentication system
- Batch processing features
- Monitoring and metrics

### Low Priority
- Alternative deployment methods
- UI/UX improvements
- Additional audio format support

## 🤝 Community Guidelines

### Code of Conduct
- Be respectful and inclusive
- Welcome newcomers and different perspectives
- Focus on constructive feedback
- Help others learn and grow

### Communication
- Use GitHub Issues for bugs and features
- Tag maintainers when needed (@username)
- Provide context in discussions
- Be patient with response times

## 🔧 Development Tips

### Container-First Development
- Always test changes in containers
- Consider resource constraints
- Optimize for startup time
- Test with different Whisper models

### Performance Considerations
- Monitor memory usage with large models
- Test transcription speed and accuracy
- Consider CPU vs GPU tradeoffs
- Optimize file upload and processing

## 📚 Resources

- **OpenAI Whisper:** https://github.com/openai/whisper
- **Flask Documentation:** https://flask.palletsprojects.com/
- **Proxmox VE:** https://www.proxmox.com/en/proxmox-ve
- **Container Best Practices:** https://docs.docker.com/develop/dev-best-practices/

---

Thank you for contributing to WhisperS2T Appliance! 🎤