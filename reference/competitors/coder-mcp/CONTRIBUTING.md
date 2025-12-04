# Contributing to coder-mcp

Thank you for your interest in contributing to coder-mcp! This guide will help you get started.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct:

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive criticism
- Respect differing viewpoints and experiences

## How to Contribute

### Reporting Issues

1. **Check existing issues** first to avoid duplicates
2. **Use issue templates** when available
3. **Include all relevant information**:
   - Clear description of the issue
   - Steps to reproduce
   - Expected vs actual behavior
   - System information
   - Error messages and logs

Example issue:
```markdown
**Description**
Search function returns empty results for valid queries

**Steps to Reproduce**
1. Initialize context with `initialize_context`
2. Create file with content "def test_function(): pass"
3. Search for "test_function"
4. No results returned

**Expected Behavior**
Should find the function definition

**System Information**
- OS: macOS 13.4
- Python: 3.11.5
- coder-mcp: 5.0.0
- Redis: 7.0.11

**Error Logs**
```
[ERROR] Vector search failed: index not found
```
```

### Suggesting Features

1. **Open a discussion** first for major features
2. **Provide use cases** and examples
3. **Consider implementation** complexity
4. **Check roadmap** for planned features

Feature request template:
```markdown
**Feature Description**
Add support for GraphQL schema analysis

**Use Case**
When working with GraphQL APIs, I want to analyze schema definitions
to understand the API structure and generate type definitions.

**Proposed Implementation**
- Add GraphQL parser to language analyzers
- Extract schema types and relationships
- Generate TypeScript/Python types

**Alternatives Considered**
- Using external GraphQL tools
- Manual schema documentation
```

### Making Changes

#### 1. Fork and Clone

```bash
# Fork on GitHub, then:
git clone https://github.com/coder-mcp/coder-mcp.git
cd coder-mcp
git remote add upstream https://github.com/coder-mcp/coder-mcp.git
```

#### 2. Set Up Development Environment

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install --with dev,test

# Install pre-commit hooks
poetry run pre-commit install

# Create branch
git checkout -b feature/your-feature-name
```

#### 3. Make Your Changes

Follow these guidelines:

- **Write tests first** (TDD approach)
- **Follow code style** (Black, isort, flake8)
- **Add docstrings** to all public functions
- **Update documentation** as needed
- **Keep commits focused** and atomic

#### 4. Test Your Changes

```bash
# Run all tests
poetry run pytest

# Run specific tests
poetry run pytest tests/unit/test_your_feature.py

# Check code style
poetry run black --check .
poetry run isort --check .
poetry run flake8
poetry run mypy coder_mcp

# Run pre-commit checks
poetry run pre-commit run --all-files
```

#### 5. Submit Pull Request

1. **Push your branch**:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create PR** on GitHub with:
   - Clear title and description
   - Reference related issues
   - List of changes made
   - Screenshots if applicable

3. **PR Description Template**:
   ```markdown
   ## Summary
   Brief description of changes

   ## Changes Made
   - Added new feature X
   - Fixed bug in Y
   - Improved performance of Z

   ## Testing
   - [ ] Unit tests added/updated
   - [ ] Integration tests added/updated
   - [ ] Manual testing completed

   ## Related Issues
   Fixes #123
   Relates to #456

   ## Screenshots
   (if applicable)
   ```

### Code Style Guide

#### Python Style

```python
# Imports - grouped and sorted
import asyncio
import json
from pathlib import Path
from typing import Dict, List, Optional

import pytest
from pydantic import BaseModel

from coder_mcp.core import ConfigManager
from coder_mcp.tools import tool_handler


# Classes - PascalCase
class MyAnalyzer(BaseAnalyzer):
    """
    Analyzer for specific language.

    This analyzer provides comprehensive analysis including:
    - Syntax validation
    - Complexity metrics
    - Pattern detection
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize analyzer.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}

    async def analyze(self, content: str) -> AnalysisResult:
        """
        Analyze code content.

        Args:
            content: Source code to analyze

        Returns:
            Analysis results with metrics

        Raises:
            AnalysisError: If analysis fails
        """
        # Implementation


# Functions - snake_case
def calculate_complexity(ast_node: Node) -> float:
    """
    Calculate cyclomatic complexity.

    Uses the standard formula: M = E - N + 2P
    where E = edges, N = nodes, P = connected components
    """
    # Implementation


# Constants - UPPER_CASE
DEFAULT_TIMEOUT = 30
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


# Type hints everywhere
async def process_files(
    files: List[Path],
    options: Optional[ProcessOptions] = None,
) -> Dict[str, AnalysisResult]:
    """Process multiple files concurrently."""
    # Implementation
```

#### Documentation Style

```python
def complex_function(
    param1: str,
    param2: Optional[int] = None,
    *args: str,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Brief one-line description.

    Longer description explaining the function's purpose,
    behavior, and any important details. Can span multiple
    lines and include examples.

    Args:
        param1: Description of param1
        param2: Description of param2. Defaults to None.
        *args: Variable positional arguments
        **kwargs: Variable keyword arguments

    Returns:
        Dictionary containing:
        - key1: Description of key1
        - key2: Description of key2

    Raises:
        ValueError: If param1 is empty
        TypeError: If param2 is not numeric

    Example:
        >>> result = complex_function("test", param2=42)
        >>> print(result["status"])
        "success"

    Note:
        This function is thread-safe but not async-safe.

    See Also:
        simple_function: A simpler version
        other_function: Related functionality
    """
```

### Testing Guidelines

#### Test Structure

```python
# tests/unit/test_feature.py
import pytest
from unittest.mock import Mock, patch

from coder_mcp.module import MyClass


class TestMyClass:
    """Test MyClass functionality."""

    @pytest.fixture
    def instance(self):
        """Create instance for testing."""
        return MyClass()

    def test_initialization(self):
        """Test proper initialization."""
        instance = MyClass(param="value")
        assert instance.param == "value"

    def test_method_success(self, instance):
        """Test method succeeds with valid input."""
        result = instance.method("input")
        assert result == "expected"

    def test_method_error(self, instance):
        """Test method handles errors correctly."""
        with pytest.raises(ValueError, match="Invalid input"):
            instance.method("")

    @pytest.mark.parametrize("input,expected", [
        ("test1", "result1"),
        ("test2", "result2"),
        ("test3", "result3"),
    ])
    def test_multiple_cases(self, instance, input, expected):
        """Test method with multiple inputs."""
        assert instance.method(input) == expected

    @patch("coder_mcp.module.external_function")
    def test_with_mock(self, mock_func, instance):
        """Test with mocked dependency."""
        mock_func.return_value = "mocked"
        result = instance.method_using_external()
        assert result == "mocked"
        mock_func.assert_called_once_with("expected_arg")
```

#### Integration Test Example

```python
# tests/integration/test_workflow.py
@pytest.mark.integration
class TestCompleteWorkflow:
    """Test complete user workflows."""

    @pytest.mark.asyncio
    async def test_analysis_workflow(self, mcp_server, sample_project):
        """Test complete code analysis workflow."""
        # Initialize project
        await mcp_server.handle_tool_call(
            "initialize_context",
            {"force_refresh": True}
        )

        # Create and analyze file
        await mcp_server.handle_tool_call(
            "write_file",
            {
                "path": "calculator.py",
                "content": "def add(a, b): return a + b"
            }
        )

        analysis = await mcp_server.handle_tool_call(
            "analyze_code",
            {"path": "calculator.py"}
        )

        # Verify results
        assert analysis["data"]["metrics"]["functions"] == 1
        assert analysis["data"]["language"] == "python"
```

### Documentation Guidelines

#### Adding Documentation

1. **API Documentation**: Update docstrings and API_REFERENCE.md
2. **User Guides**: Add examples and tutorials
3. **Architecture**: Update ARCHITECTURE.md for design changes
4. **Configuration**: Document new configuration options

#### Documentation Style

```markdown
# Feature Name

Brief description of the feature.

## Overview

Longer explanation of what the feature does and why it's useful.

## Usage

### Basic Example

```python
# Code example with comments
from coder_mcp import feature

result = feature.do_something("input")
print(result)
```

### Advanced Example

```python
# More complex example
from coder_mcp import feature

# Configure options
options = {
    "setting1": "value1",
    "setting2": "value2"
}

# Use feature with options
result = feature.do_something("input", **options)
```

## Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| setting1 | str | "default" | Controls behavior X |
| setting2 | int | 10 | Limits operation Y |

## API Reference

### `feature.do_something(input, **options)`

Detailed function documentation.

**Parameters:**
- `input` (str): The input to process
- `**options`: Additional options

**Returns:**
- `Result`: The processed result

## Troubleshooting

### Common Issues

**Issue**: Feature returns unexpected results
**Solution**: Check that input format matches requirements
```

### Commit Guidelines

#### Commit Message Format

```
type(scope): subject

body

footer
```

#### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code refactoring
- **perf**: Performance improvements
- **test**: Test additions or changes
- **build**: Build system changes
- **ci**: CI/CD changes
- **chore**: Other changes

#### Examples

```bash
# Feature
git commit -m "feat(analysis): add support for TypeScript analysis"

# Bug fix
git commit -m "fix(search): correct vector similarity calculation"

# Documentation
git commit -m "docs(api): update tool handler documentation"

# With body
git commit -m "feat(templates): add React component generator

- Add template for functional components
- Add template for class components
- Include prop types generation
- Support TypeScript variants

Closes #123"
```

### Review Process

#### For Contributors

1. **Self-review** your PR first
2. **Respond to feedback** constructively
3. **Update PR** based on reviews
4. **Keep PR updated** with main branch

#### For Reviewers

1. **Be constructive** and specific
2. **Test the changes** locally
3. **Check tests** pass
4. **Verify documentation** is updated
5. **Consider performance** impact

Review comment examples:

```python
# Helpful
"""
This could cause issues with large files. Consider:
```python
# Stream file instead of loading entirely
with open(file_path) as f:
    for line in f:
        process_line(line)
```
"""

# Not helpful
"This is wrong"
```

### Release Process

#### Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

#### Release Steps

1. **Update version** in `pyproject.toml`
2. **Update CHANGELOG.md**
3. **Create release PR**
4. **Get approval** from maintainers
5. **Merge and tag**
6. **Publish release**

### Getting Help

#### Resources

- **Documentation**: Read all docs first
- **Issues**: Search existing issues
- **Discussions**: Ask questions
- **Discord/Slack**: Join community chat

#### Asking Questions

Good question example:
```markdown
I'm trying to add support for Ruby analysis but running into issues
with the AST parser. Here's what I've tried:

1. Created RubyAnalyzer class following Python example
2. Added ruby parser dependency
3. Implemented analyze method

Getting error: "Parser not found"

Code: [link to branch]
Error log: [gist link]

Any guidance on integrating new language parsers?
```

### Recognition

Contributors are recognized in:

- **CONTRIBUTORS.md**: All contributors listed
- **Release notes**: Feature contributors mentioned
- **Documentation**: Author attribution
- **Code**: Author in file headers

Thank you for contributing to coder-mcp! 🚀
