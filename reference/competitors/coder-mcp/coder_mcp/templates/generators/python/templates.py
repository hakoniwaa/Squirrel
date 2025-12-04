#!/usr/bin/env python3
"""
Python Templates
Collection of Jinja2 templates for Python code generation
"""


class PythonTemplates:
    """Collection of Python code templates"""

    # Class template
    CLASS_TEMPLATE = '''"""
{{ description or name + " class" }}
{{ purpose or "Generated class for " + name }}
"""

{% if imports %}
{% for import_line in imports %}
{{ import_line }}
{% endfor %}

{% endif %}
class {{ name_pascal }}{% if base_class %}({{ base_class }}){% endif %}:
    """
    {{ description or name + " class" }}

    {% if docstring %}{{ docstring }}{% endif %}
    """

    {% if class_attributes %}
    # Class attributes
    {% for attr_name, attr_value in class_attributes.items() %}
    {{ attr_name }} = {{ attr_value }}
    {% endfor %}

    {% endif %}
    def __init__(self{%- if init_params -%}
        {%- for param in init_params -%}, {{ param }}{%- endfor -%}
    {%- endif -%}):
        """Initialize {{ name_pascal }} instance"""
        {% if base_class %}super().__init__(){% endif %}
        {% if init_params %}
        {% for param in init_params %}
        self.{{ param.split(':')[0].strip() }} = {{ param.split(':')[0].strip() }}
        {% endfor %}
        {% else %}
        pass
        {% endif %}

    {% if methods %}
    {% for method in methods %}
    def {{ method.name }}(self{%- if method.params -%}
        {%- for param in method.params -%}, {{ param }}{%- endfor -%}
    {%- endif -%}){%- if method.return_type %} -> {{ method.return_type }}{% endif %}:
        """{{ method.description or method.name }}"""
        {% if method.body %}
        {{ method.body }}
        {% else %}
        pass
        {% endif %}

    {% endfor %}
    {% endif %}
    def __str__(self) -> str:
        """String representation of {{ name_pascal }}"""
        return f"<{{ name_pascal }}()>"

    def __repr__(self) -> str:
        """Detailed representation of {{ name_pascal }}"""
        return self.__str__()
'''

    # Function template
    FUNCTION_TEMPLATE = '''{% if docstring_style == "google" %}
def {{ name_snake }}({%- if params -%}
    {%- for param in params -%}{{ param }}{%- if not loop.last -%}, {%- endif -%}{%- endfor -%}
{%- endif -%}){%- if return_type %} -> {{ return_type }}{% endif %}:
    """{{ description or name + " function" }}

    {% if params %}
    Args:
    {% for param in params %}
        {{ param.split(':')[0].strip() }}: {{ param_descriptions.get(
            param.split(':')[0].strip(), 'Parameter description') }}
    {% endfor %}

    {% endif %}
    {% if return_type and return_type != "None" %}
    Returns:
        {{ return_description or return_type + ": Return value description" }}

    {% endif %}
    {% if exceptions %}
    Raises:
    {% for exception in exceptions %}
        {{ exception }}: {{ exception_descriptions.get(
            exception, 'Exception description') }}
    {% endfor %}
    {% endif %}
    """
{% else %}
def {{ name_snake }}({%- if params -%}
    {%- for param in params -%}{{ param }}{%- if not loop.last -%}, {%- endif -%}{%- endfor -%}
{%- endif -%}){%- if return_type %} -> {{ return_type }}{% endif %}:
    """
    {{ description or name + " function" }}

    {% if params %}
    Parameters:
    {% for param in params %}
    {{ param.split(':')[0].strip() }} : {{ param.split(':')[1].strip()
        if ':' in param else 'type' }}
        {{ param_descriptions.get(
            param.split(':')[0].strip(), 'Parameter description') }}
    {% endfor %}

    {% endif %}
    {% if return_type and return_type != "None" %}
    Returns:
    {{ return_type }}
        {{ return_description or "Return value description" }}
    {% endif %}
    """
{% endif %}
    {% if function_body %}
    {{ function_body }}
    {% else %}
    # TODO: Implement function logic
    {% if return_type and return_type != "None" %}
    {% if return_type == "str" %}
    return ""
    {% elif return_type == "int" %}
    return 0
    {% elif return_type == "bool" %}
    return False
    {% elif return_type == "list" or return_type.startswith("List") %}
    return []
    {% elif return_type == "dict" or return_type.startswith("Dict") %}
    return {}
    {% else %}
    return None
    {% endif %}
    {% else %}
    pass
    {% endif %}
    {% endif %}
'''

    # Test template
    TEST_TEMPLATE = '''"""
Tests for {{ name }}
{{ test_framework or "pytest" }} tests with comprehensive coverage
"""

import pytest
{% if test_framework == "unittest" %}
import unittest
from unittest.mock import Mock, patch, MagicMock
{% else %}
from unittest.mock import Mock, patch, MagicMock
{% endif %}
{% if additional_imports %}
{% for import_line in additional_imports %}
{{ import_line }}
{% endfor %}
{% endif %}


{% if test_framework == "unittest" %}
class Test{{ name_pascal }}(unittest.TestCase):
{% else %}
class Test{{ name_pascal }}:
{% endif %}
    """{{ test_framework or "pytest" }} tests for {{ name }}"""

    {% if test_framework == "unittest" %}
    def setUp(self):
    {% else %}
    def setup_method(self):
    {% endif %}
        """Set up test fixtures before each test method"""
        self.sample_data = {
            "name": "Test{{ name_pascal }}",
            "description": "Test description",
            {% if additional_fixtures %}
            {% for key, value in additional_fixtures.items() %}
            "{{ key }}": {{ value }},
            {% endfor %}
            {% endif %}
        }
        {% if setup_code %}
        {{ setup_code }}
        {% endif %}

    def test_{{ name_snake }}_creation(self):
        """Test {{ name }} creation with valid data"""
        # Arrange
        # TODO: Add test setup

        # Act
        # TODO: Add test execution

        # Assert
        assert True  # Replace with actual test

    def test_{{ name_snake }}_validation(self):
        """Test {{ name }} input validation"""
        # TODO: Test validation logic
        assert True  # Replace with actual test

    {% if test_cases %}
    {% for test_case in test_cases %}
    def test_{{ test_case.name }}(self):
        """{{ test_case.description }}"""
        {{ test_case.body or "assert True  # Replace with actual test" }}

    {% endfor %}
    {% endif %}
    {% if parametrized_tests %}
    @pytest.mark.parametrize("{{ parametrized_tests.param_names }}", [
        {% for test_data in parametrized_tests.test_data %}
        {{ test_data }},
        {% endfor %}
    ])
    def test_{{ name_snake }}_parametrized(
        self, {{ parametrized_tests.param_names }}
    ):
        """Parametrized test for {{ name }}"""
        # TODO: Implement parametrized test
        assert True  # Replace with actual test

    {% endif %}

{% if fixtures %}
# Fixtures
{% for fixture in fixtures %}
@pytest.fixture
def {{ fixture.name }}():
    """{{ fixture.description }}"""
    {% if fixture.body %}
    {{ fixture.body }}
    {% else %}
    return {{ fixture.return_value or "None" }}
    {% endif %}

{% endfor %}
{% endif %}
'''

    # Configuration file templates
    SETUP_PY_TEMPLATE = '''"""
Setup configuration for {{ package_name }}
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="{{ package_name }}",
    version="{{ version or "0.1.0" }}",
    author="{{ author or "Your Name" }}",
    author_email="{{ author_email or "your.email@example.com" }}",
    description="{{ description or "A Python package" }}",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="{{ url or "https://github.com/coder-mcp/" + package_name }}",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        {% if dependencies %}
        {% for dep in dependencies %}
        "{{ dep }}",
        {% endfor %}
        {% endif %}
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov",
            "black",
            "isort",
            "flake8",
            "mypy",
        ],
    },
)
'''

    # Requirements template
    REQUIREMENTS_TEMPLATE = """# Core dependencies
{% if dependencies %}
{% for dep in dependencies %}
{{ dep }}
{% endfor %}
{% else %}
# Add your project dependencies here
{% endif %}

# Development dependencies (install with: pip install -r requirements-dev.txt)
{% if dev_dependencies %}
{% for dep in dev_dependencies %}
{{ dep }}
{% endfor %}
{% endif %}
"""

    # Makefile template
    MAKEFILE_TEMPLATE = """# {{ package_name }} Makefile

.PHONY: help install install-dev test test-coverage lint format clean build upload

help:  ## Show this help message
\t@echo "Available commands:"
\t@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \\
\t\tawk 'BEGIN {FS = ":.*?## "}; {printf "  \\033[36m%-15s\\033[0m %s\\n", $$1, $$2}'

install:  ## Install package
\tpip install -e .

install-dev:  ## Install package with development dependencies
\tpip install -e ".[dev]"

test:  ## Run tests
\tpytest

test-coverage:  ## Run tests with coverage
\tpytest --cov={{ package_name }} --cov-report=html --cov-report=term

lint:  ## Run linting
\tflake8 {{ package_name }}
\tmypy {{ package_name }}

format:  ## Format code
\tblack {{ package_name }}
\tisort {{ package_name }}

clean:  ## Clean build artifacts
\trm -rf build/
\trm -rf dist/
\trm -rf *.egg-info/
\tfind . -type d -name __pycache__ -delete
\tfind . -type f -name "*.pyc" -delete

build:  ## Build package
\tpython -m build

upload:  ## Upload to PyPI
\tpython -m twine upload dist/*
"""

    @classmethod
    def get_template(cls, template_name: str) -> str:
        """
        Get a template by name

        Args:
            template_name: Name of the template to retrieve

        Returns:
            Template string

        Raises:
            ValueError: If template name is not found
        """
        template_map = {
            "class": cls.CLASS_TEMPLATE,
            "function": cls.FUNCTION_TEMPLATE,
            "test": cls.TEST_TEMPLATE,
            "setup_py": cls.SETUP_PY_TEMPLATE,
            "requirements": cls.REQUIREMENTS_TEMPLATE,
            "makefile": cls.MAKEFILE_TEMPLATE,
        }

        if template_name not in template_map:
            available = ", ".join(template_map.keys())
            raise ValueError(f"Template '{template_name}' not found. Available: {available}")

        return template_map[template_name]

    @classmethod
    def list_templates(cls) -> list:
        """
        List all available template names

        Returns:
            List of template names
        """
        return ["class", "function", "test", "setup_py", "requirements", "makefile"]
