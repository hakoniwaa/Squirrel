# Contributing to Claude Cache

Thank you for your interest in contributing to Claude Cache! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to be respectful and constructive in all interactions.

## How to Contribute

### Reporting Issues

- Check existing issues before creating a new one
- Provide clear description and steps to reproduce
- Include relevant log excerpts if applicable
- Specify your environment (OS, Python version, etc.)

### Suggesting Features

- Open a discussion first for major features
- Explain the use case and benefits
- Consider implementation complexity

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow existing code style
   - Add tests for new functionality
   - Update documentation as needed

4. **Test your changes**
   ```bash
   # Install development dependencies
   pip install -e ".[dev]"

   # Run tests
   pytest

   # Check code style
   black src/
   isort src/
   ```

5. **Commit with clear messages**
   ```bash
   git commit -m "Add: Feature description"
   ```

6. **Push and create PR**
   - Reference any related issues
   - Describe what changes you made
   - Include screenshots if UI changes

## Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/claude-cache.git
cd claude-cache

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with all features
pip install -e ".[all,dev]"
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=claude_cache

# Run specific test
pytest tests/test_success_detector.py
```

## Code Style

- Use Black for formatting (line length: 88)
- Use isort for import sorting
- Follow PEP 8 guidelines
- Add type hints where beneficial

## Documentation

- Update README for user-facing changes
- Add docstrings to new functions/classes
- Include examples in docstrings
- Update wiki for major features

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create release PR
4. Tag release after merge
5. Push tag to trigger automatic PyPI deployment

## Areas for Contribution

### High Priority
- Test coverage improvements
- Performance optimizations
- Documentation improvements
- Bug fixes

### Feature Ideas
- Enhanced MCP tools
- Team collaboration features
- Web dashboard
- Additional pattern detection algorithms
- Integration with other AI tools
- Visualization capabilities

## Questions?

Feel free to:
- Open a discussion on GitHub
- Ask in issues
- Reach out to maintainers

Thank you for contributing!