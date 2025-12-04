"""
Test data builders using the Builder pattern.

These builders help create consistent test data across all tests.
"""

import random
from typing import Any, Dict, List

from faker import Faker

fake = Faker()


class FileBuilder:
    """Builder for creating test files with various characteristics."""

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset builder to default state."""
        self._name = "test_file.py"
        self._content = ""
        self._size = None
        self._language = "python"
        self._has_errors = False
        self._complexity = "low"
        return self

    def with_name(self, name: str):
        """Set file name."""
        self._name = name
        return self

    def with_content(self, content: str):
        """Set specific content."""
        self._content = content
        self._size = None  # Override size-based generation
        return self

    def with_size(self, size_bytes: int):
        """Generate content of specific size."""
        self._size = size_bytes
        self._content = None  # Override content
        return self

    def with_language(self, language: str):
        """Set programming language."""
        self._language = language
        return self

    def with_syntax_errors(self):
        """Add syntax errors to the file."""
        self._has_errors = True
        return self

    def with_complexity(self, complexity: str):
        """Set code complexity: low, medium, high."""
        self._complexity = complexity
        return self

    def build(self) -> Dict[str, Any]:
        """Build the file data."""
        if self._content:
            content = self._content
        elif self._size:
            content = self._generate_content_by_size(self._size)
        else:
            content = self._generate_content_by_language()

        if self._has_errors:
            content = self._add_syntax_errors(content)

        return {
            "name": self._name,
            "content": content,
            "language": self._language,
            "size": len(content.encode("utf-8")),
            "has_errors": self._has_errors,
            "complexity": self._complexity,
        }

    def _generate_content_by_language(self) -> str:
        """Generate content based on language and complexity."""
        if self._language == "python":
            return self._generate_python_code()
        elif self._language == "javascript":
            return self._generate_javascript_code()
        elif self._language == "markdown":
            return self._generate_markdown()
        else:
            return self._generate_text()

    def _generate_python_code(self) -> str:
        """Generate Python code with specified complexity."""
        if self._complexity == "low":
            return '''
def simple_function(x, y):
    """Add two numbers."""
    return x + y

def greet(name):
    """Greet a person."""
    return f"Hello, {name}!"
'''
        elif self._complexity == "medium":
            return '''
class DataProcessor:
    def __init__(self, data):
        self.data = data
        self.processed = False

    def process(self):
        """Process the data."""
        if self.processed:
            return self.data

        result = []
        for item in self.data:
            if self._validate(item):
                result.append(self._transform(item))

        self.processed = True
        return result

    def _validate(self, item):
        return isinstance(item, (int, float)) and item > 0

    def _transform(self, item):
        return item * 2 if item < 100 else item * 1.5
'''
        else:  # high complexity
            return """
import asyncio
from typing import List, Dict, Optional, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class ComplexData:
    id: int
    value: Union[int, float]
    metadata: Dict[str, Any]

class AbstractProcessor(ABC):
    @abstractmethod
    async def process(self, data: ComplexData) -> ComplexData:
        pass

class ComplexProcessor(AbstractProcessor):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cache = {}
        self.metrics = {"processed": 0, "errors": 0}

    async def process(self, data: ComplexData) -> ComplexData:
        try:
            # Complex nested logic
            if data.id in self.cache:
                cached = self.cache[data.id]
                if self._is_cache_valid(cached):
                    return cached

            result = data
            for transformer in self._get_transformers():
                result = await transformer(result)

            self.cache[data.id] = result
            self.metrics["processed"] += 1
            return result

        except Exception as e:
            self.metrics["errors"] += 1
            raise ProcessingError(f"Failed to process {data.id}: {e}")

    def _is_cache_valid(self, cached_data):
        # Complex validation logic
        return True

    def _get_transformers(self):
        # Dynamic transformer selection
        return []
"""

    def _generate_javascript_code(self) -> str:
        """Generate JavaScript code."""
        return """
class UserService {
    constructor(database) {
        this.db = database;
        this.cache = new Map();
    }

    async getUser(id) {
        if (this.cache.has(id)) {
            return this.cache.get(id);
        }

        const user = await this.db.users.findOne({ id });
        this.cache.set(id, user);
        return user;
    }
}

module.exports = UserService;
"""

    def _generate_markdown(self) -> str:
        """Generate Markdown content."""
        return f"""
# {fake.sentence()}

{fake.paragraph()}

## {fake.sentence()}

{fake.paragraph()}

### Features

- {fake.sentence()}
- {fake.sentence()}
- {fake.sentence()}

### Code Example

```python
{self._generate_python_code()}
```

### {fake.sentence()}

{fake.paragraph()}
"""

    def _generate_text(self) -> str:
        """Generate plain text content."""
        return "\n".join(fake.paragraph() for _ in range(5))

    def _generate_content_by_size(self, size: int) -> str:
        """Generate content of specific size."""
        # Generate slightly less to account for encoding
        target_chars = int(size * 0.9)

        if self._language == "python":
            # Generate Python code
            content = "# Generated file\n"
            while len(content) < target_chars:
                content += f"\ndef function_{len(content)}():\n    return {len(content)}\n"
        else:
            # Generate text
            content = ""
            while len(content) < target_chars:
                content += fake.paragraph() + "\n\n"

        return content[:size]

    def _add_syntax_errors(self, content: str) -> str:
        """Add syntax errors to content."""
        if self._language == "python":
            # Add various Python syntax errors
            errors = [
                "\n    def broken_function(\n",  # Missing closing paren
                "\n    if True\n        pass\n",  # Missing colon
                "\n    return\n",  # Unexpected indent
                "\n    import sys os\n",  # Invalid import
            ]

            # Insert random error
            lines = content.split("\n")
            insert_pos = random.randint(1, len(lines) - 1)
            lines.insert(insert_pos, random.choice(errors))
            return "\n".join(lines)

        return content


class ProjectBuilder:
    """Builder for creating complete project structures."""

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset to default state."""
        self._name = "test_project"
        self._type = "python"
        self._size = "small"
        self._include_tests = True
        self._include_docs = True
        self._files = {}
        return self

    def with_name(self, name: str):
        """Set project name."""
        self._name = name
        return self

    def with_type(self, project_type: str):
        """Set project type: python, javascript, mixed."""
        self._type = project_type
        return self

    def with_size(self, size: str):
        """Set project size: small, medium, large."""
        self._size = size
        return self

    def with_tests(self, include: bool = True):
        """Include test files."""
        self._include_tests = include
        return self

    def with_docs(self, include: bool = True):
        """Include documentation."""
        self._include_docs = include
        return self

    def with_file(self, path: str, content: str):
        """Add a specific file."""
        self._files[path] = content
        return self

    def build(self) -> Dict[str, str]:
        """Build the project structure."""
        files = {}

        # Add base files
        if self._type == "python":
            files.update(self._build_python_project())
        elif self._type == "javascript":
            files.update(self._build_javascript_project())

        # Add custom files
        files.update(self._files)

        return files

    def _build_python_project(self) -> Dict[str, str]:
        """Build Python project structure."""
        file_builder = FileBuilder()
        files = {
            "README.md": f"# {self._name}\n\nA test Python project.",
            "pyproject.toml": self._generate_pyproject_toml(),
            ".gitignore": "*.pyc\n__pycache__/\n.venv/\n.pytest_cache/\n",
            "src/__init__.py": "",
        }

        # Add source files based on size
        if self._size == "small":
            files["src/main.py"] = file_builder.reset().with_complexity("low").build()["content"]
            files["src/utils.py"] = file_builder.reset().with_complexity("low").build()["content"]
        elif self._size == "medium":
            for i in range(5):
                files[f"src/module_{i}.py"] = (
                    file_builder.reset().with_complexity("medium").build()["content"]
                )
        else:  # large
            for i in range(20):
                files[f"src/module_{i}.py"] = (
                    file_builder.reset().with_complexity("high").build()["content"]
                )

        # Add tests
        if self._include_tests:
            files["tests/__init__.py"] = ""
            files["tests/conftest.py"] = "import pytest\n"
            files[
                "tests/test_main.py"
            ] = """
import pytest
from src.main import *

def test_example():
    assert True
"""

        # Add docs
        if self._include_docs:
            files["docs/index.md"] = f"# {self._name} Documentation\n"
            files["docs/api.md"] = "# API Reference\n"

        return files

    def _build_javascript_project(self) -> Dict[str, str]:
        """Build JavaScript project structure."""
        files = {
            "README.md": f"# {self._name}\n\nA test JavaScript project.",
            "package.json": self._generate_package_json(),
            ".gitignore": "node_modules/\n.env\ndist/\n",
            "index.js": "console.log('Hello, World!');",
        }

        return files

    def _generate_pyproject_toml(self) -> str:
        """Generate pyproject.toml content."""
        return f"""[tool.poetry]
name = "{self._name}"
version = "0.1.0"
description = "A test project"

[tool.poetry.dependencies]
python = "^3.8"

[tool.poetry.dev-dependencies]
pytest = "^7.0"
"""

    def _generate_package_json(self) -> str:
        """Generate package.json content."""
        return f"""{{
  "name": "{self._name}",
  "version": "1.0.0",
  "description": "A test project",
  "main": "index.js",
  "scripts": {{
    "test": "jest"
  }}
}}"""


class TestDataGenerator:
    """Generate various types of test data."""

    @staticmethod
    def generate_code_with_issues(issue_types: List[str]) -> str:
        """Generate code with specific issues for testing."""
        code_parts = []

        if "long_function" in issue_types:
            code_parts.append(
                """
def very_long_function(data):
    # This function is too long
"""
                + "\n".join(f"    line_{i} = {i}" for i in range(100))
            )

        if "duplicate_code" in issue_types:
            duplicate = """
def process_user_data(user):
    if user.age > 18:
        user.status = "adult"
        user.permissions = ["read", "write"]
    return user
"""
            code_parts.extend([duplicate, duplicate.replace("user", "customer")])

        if "security_issue" in issue_types:
            code_parts.append(
                """
import os
def unsafe_function(user_input):
    # SQL injection vulnerability
    query = f"SELECT * FROM users WHERE id = {user_input}"

    # Command injection
    os.system(f"echo {user_input}")

    # Hardcoded secret
    api_key = "sk-1234567890abcdef"
"""
            )

        return "\n\n".join(code_parts)

    @staticmethod
    def generate_test_cases(function_name: str, num_cases: int = 5) -> List[Dict[str, Any]]:
        """Generate test cases for a function."""
        test_cases = []

        for i in range(num_cases):
            test_case = {
                "name": f"test_{function_name}_{i}",
                "input": fake.pydict(nb_elements=3, value_types=["str", "int", "float"]),
                "expected": fake.random_element([True, False, None, fake.pyint()]),
                "description": fake.sentence(),
            }
            test_cases.append(test_case)

        return test_cases
