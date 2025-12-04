#!/usr/bin/env python3
"""
Python Test Builder
Specialized builder for generating Python test files
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from ....template_engine import GeneratedCode
from ...base import BaseBuilder
from .utils import generate_default_test_cases


class PythonTestBuilder(BaseBuilder):
    """Builder for Python test files"""

    def __init__(self, template_engine, workspace_root: Path):
        super().__init__(template_engine)
        self.workspace_root: Path = workspace_root

    def build(self, name: str, options: Dict[str, Any]) -> GeneratedCode:
        """
        Build a Python test file

        Args:
            name: Name of the test subject
            options: Test generation options

        Returns:
            Generated code object
        """
        variables = self.get_common_variables(name, options)

        # Extract test-specific options
        variables.update(
            {
                "description": options.get("description", f"Tests for {name}"),
                "test_framework": options.get("test_framework", "pytest"),
                "test_type": options.get("test_type", "unit"),
                "additional_imports": options.get("additional_imports", []),
                "additional_fixtures": options.get("additional_fixtures", {}),
                "setup_code": options.get("setup_code", ""),
                "test_cases": options.get("test_cases", []),
                "parametrized_tests": options.get("parametrized_tests", {}),
                "fixtures": options.get("fixtures", []),
                "mock_objects": options.get("mock_objects", []),
            }
        )

        # Add default test cases if none provided
        if not variables["test_cases"]:
            subject_type = options.get("subject_type", "function")
            variables["test_cases"] = generate_default_test_cases(name, subject_type)

        # Add default fixtures if none provided and needed
        if not variables["fixtures"] and variables["test_framework"] == "pytest":
            variables["fixtures"] = self._generate_default_fixtures(name, options)

        # Render the test template
        template = '''"""
{{ description }}
{{ test_framework or "pytest" }} tests with comprehensive coverage
Generated on: {{ timestamp }}
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
        {% if mock_objects %}
        # Mock objects
        {% for mock_obj in mock_objects %}
        self.{{ mock_obj.name }} = Mock(spec={{ mock_obj.spec or mock_obj.name }})
        {% endfor %}
        {% endif %}

    {% if test_framework == "unittest" %}
    def tearDown(self):
    {% else %}
    def teardown_method(self):
    {% endif %}
        """Clean up after each test method"""
        # TODO: Add cleanup code if needed
        pass

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
        {% if test_case.setup %}
        # Arrange
        {{ test_case.setup }}
        {% endif %}

        {% if test_case.action %}
        # Act
        {{ test_case.action }}
        {% endif %}

        {% if test_case.assertion %}
        # Assert
        {{ test_case.assertion }}
        {% else %}
        assert True  # Replace with actual test
        {% endif %}

    {% endfor %}
    {% endif %}
    {% if parametrized_tests and parametrized_tests.param_names %}
    @pytest.mark.parametrize("{{ parametrized_tests.param_names }}", [
        {% for test_data in parametrized_tests.test_data %}
        {{ test_data }},
        {% endfor %}
    ])
    def test_{{ name_snake }}_parametrized(self, {{ parametrized_tests.param_names }}):
        """Parametrized test for {{ name }}"""
        # TODO: Implement parametrized test
        assert True  # Replace with actual test

    {% endif %}
    {% if test_type == "integration" %}
    @pytest.mark.integration
    def test_{{ name_snake }}_integration(self):
        """Integration test for {{ name }}"""
        # TODO: Implement integration test
        assert True  # Replace with actual test

    {% endif %}
    {% if test_type == "performance" %}
    @pytest.mark.performance
    def test_{{ name_snake }}_performance(self):
        """Performance test for {{ name }}"""
        import time

        start_time = time.time()
        # TODO: Add performance test code
        end_time = time.time()

        # Assert that operation completes within acceptable time
        assert (end_time - start_time) < 1.0  # Replace with actual threshold

    {% endif %}

{% if fixtures %}
# Fixtures
{% for fixture in fixtures %}
@pytest.fixture{% if fixture.scope %}(scope="{{ fixture.scope }}"){% endif %}
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

        content = self.render_string(template, variables)

        # Determine file path
        file_path = self._get_file_path(name, options)

        return GeneratedCode(
            content=content, file_path=file_path, language="python", purpose=f"{name} tests"
        )

    def _generate_default_fixtures(
        self, name: str, options: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate default pytest fixtures"""
        fixtures = [
            {
                "name": f"sample_{self.to_snake_case(name)}_data",
                "description": f"Fixture providing sample {name} data",
                "return_value": """{
        "name": "Test Item",
        "description": "Test description",
        "is_active": True
    }""",
            }
        ]

        subject_type = options.get("subject_type", "function")
        if subject_type in ["class", "service"]:
            fixtures.append(
                {
                    "name": f"{self.to_snake_case(name)}_instance",
                    "description": f"Fixture providing {name} instance",
                    "body": f"""# TODO: Create and configure {name} instance
    return Mock(spec={name})""",
                }
            )

        return fixtures

    def _get_file_path(self, name: str, options: Optional[Dict[str, Any]]) -> Optional[Path]:
        """Get the file path for the test file"""
        if options is None:
            return None
        if "file_path" in options:
            file_path = options["file_path"]
            if isinstance(file_path, Path):
                return file_path
            elif isinstance(file_path, str):
                return Path(file_path)
            else:
                raise TypeError(f"file_path must be str or Path, got {type(file_path)})")
        # Generate default path relative to workspace
        test_type = options.get("test_type", "unit")
        if not isinstance(test_type, str):
            test_type = "unit"
        test_name = f"test_{self.to_snake_case(name)}"
        if test_type == "unit":
            rel_path = Path("tests") / f"{test_name}.py"
        else:
            rel_path = Path("tests") / test_type / f"{test_name}_{test_type}.py"
        return Path(self.workspace_root / rel_path)

    def generate_integration_test(
        self, name: str, components: List[str], options: Optional[Dict[str, Any]] = None
    ) -> GeneratedCode:
        """
        Generate an integration test file

        Args:
            name: Name of the integration test
            components: List of components being tested together
            options: Additional options

        Returns:
            Generated code object
        """
        options = options or {}

        # Add integration-specific options
        test_cases = [
            {
                "name": f"{self.to_snake_case(name)}_integration_flow",
                "description": f"Test complete {name} integration flow",
                "setup": "# TODO: Set up integration environment",
                "action": "# TODO: Execute integration flow",
                "assertion": "# TODO: Assert end-to-end functionality",
            }
        ]

        for component in components:
            test_cases.append(
                {
                    "name": f"{self.to_snake_case(component)}_integration",
                    "description": f"Test {component} integration in {name}",
                    "setup": f"# TODO: Set up {component} for integration",
                    "action": f"# TODO: Test {component} integration",
                    "assertion": f"# TODO: Assert {component} works correctly",
                }
            )

        options.update(
            {
                "test_type": "integration",
                "test_cases": test_cases,
                "additional_imports": ["import pytest", "# TODO: Add component imports"],
                "description": (
                    f"Integration tests for {name} with components: " f"{', '.join(components)}"
                ),
            }
        )

        return self.build(name, options)

    def generate_performance_test(
        self, name: str, metrics: List[str], options: Optional[Dict[str, Any]] = None
    ) -> GeneratedCode:
        """
        Generate a performance test file

        Args:
            name: Name of the performance test
            metrics: List of metrics to measure
            options: Additional options

        Returns:
            Generated code object
        """
        options = options or {}

        # Add performance-specific test cases
        test_cases = []
        for metric in metrics:
            test_cases.append(
                {
                    "name": f"{self.to_snake_case(name)}_{metric}_performance",
                    "description": f"Test {name} {metric} performance",
                    "setup": f"# TODO: Set up {metric} measurement",
                    "action": f"# TODO: Execute operation to measure {metric}",
                    "assertion": f"# TODO: Assert {metric} meets requirements",
                }
            )

        options.update(
            {
                "test_type": "performance",
                "test_cases": test_cases,
                "additional_imports": ["import time", "import psutil", "import pytest"],
                "description": f'Performance tests for {name} measuring: {", ".join(metrics)}',
            }
        )

        return self.build(name, options)

    def generate_mock_test(
        self, name: str, dependencies: List[str], options: Optional[Dict[str, Any]] = None
    ) -> GeneratedCode:
        """
        Generate a test file with extensive mocking

        Args:
            name: Name of the test subject
            dependencies: List of dependencies to mock
            options: Additional options

        Returns:
            Generated code object
        """
        options = options or {}

        # Set up mock objects
        mock_objects = []
        for dep in dependencies:
            mock_objects.append({"name": f"mock_{self.to_snake_case(dep)}", "spec": dep})

        # Add mock-specific setup
        setup_lines = []
        for dep in dependencies:
            setup_lines.extend(
                [
                    f"# Configure {dep} mock",
                    f"self.mock_{self.to_snake_case(dep)}.configure_mock(**{{}})",
                ]
            )
        setup_code = "\n".join(setup_lines)

        options.update(
            {
                "mock_objects": mock_objects,
                "setup_code": setup_code,
                "additional_imports": [
                    "from unittest.mock import Mock, patch, MagicMock",
                    "# TODO: Add dependency imports for mocking",
                ],
                "description": (
                    f"Tests for {name} with mocked dependencies: " f"{', '.join(dependencies)}"
                ),
            }
        )

        return self.build(name, options)
