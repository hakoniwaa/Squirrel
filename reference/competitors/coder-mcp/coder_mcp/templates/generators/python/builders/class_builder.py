#!/usr/bin/env python3
"""
Python Class Builder
Specialized builder for generating Python classes
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from ....template_engine import GeneratedCode
from ...base import BaseBuilder


class ClassBuilder(BaseBuilder):
    """Builder for Python classes"""

    def __init__(self, template_engine, workspace_root: Path):
        super().__init__(template_engine)
        self.workspace_root: Path = workspace_root

    def build(self, name: str, options: Dict[str, Any]) -> GeneratedCode:
        """
        Build a Python class

        Args:
            name: Name of the class
            options: Class generation options

        Returns:
            Generated code object
        """
        variables = self.get_common_variables(name, options)

        # Extract class-specific options
        variables.update(
            {
                "base_class": options.get("base_class"),
                "description": options.get("description", f"{name} class"),
                "purpose": options.get("purpose", f"Generated class for {name}"),
                "imports": options.get("imports", []),
                "class_attributes": options.get("class_attributes", {}),
                "init_params": options.get("init_params", []),
                "methods": options.get("methods", []),
                "docstring": options.get("docstring", ""),
            }
        )

        # Add default imports if base class is specified
        if variables["base_class"]:
            base_imports = self._get_base_class_imports(variables["base_class"])
            variables["imports"].extend(base_imports)

        # Remove duplicates from imports
        variables["imports"] = list(dict.fromkeys(variables["imports"]))

        # Add default methods if none specified
        if not variables["methods"]:
            variables["methods"] = self._get_default_methods(options)

        # Render the class template
        template = (
            '''"""
{{ description }}
{{ purpose }}
Generated on: {{ timestamp }}
"""

{% if imports %}
{% for import_line in imports %}
{{ import_line }}
{% endfor %}

{% endif %}
class {{ name_pascal }}{% if base_class %}({{ base_class }}){% endif %}:
    """
    {{ description }}

    {% if docstring %}{{ docstring }}{% endif %}
    """

    {% if class_attributes %}
    # Class attributes
    {% for attr_name, attr_value in class_attributes.items() %}
    {{ attr_name }} = {{ attr_value }}
    {% endfor %}

    {% endif %}
    def __init__(self'''
            + """{% if init_params %}"""
            + """{% for param in init_params %}, {{ param }}{% endfor %}"""
            + '''{% endif %}):
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
    def {{ method.name }}(self'''
            + """{% if method.params %}"""
            + """{% for param in method.params %}, {{ param }}{% endfor %}"""
            + """{% endif %})"""
            + '''{% if method.return_type %} -> {{ method.return_type }}{% endif %}:
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
        )

        content = self.render_string(template, variables)

        # Determine file path
        file_path = self._get_file_path(name, options)

        return GeneratedCode(
            content=content, file_path=file_path, language="python", purpose=f"{name} class"
        )

    def _get_base_class_imports(self, base_class: str) -> List[str]:
        """Get required imports for common base classes"""
        import_map = {
            "ABC": ["from abc import ABC, abstractmethod"],
            "BaseModel": ["from pydantic import BaseModel"],
            "Enum": ["from enum import Enum"],
            "IntEnum": ["from enum import IntEnum"],
            "NamedTuple": ["from typing import NamedTuple"],
            "TypedDict": ["from typing import TypedDict"],
            "unittest.TestCase": ["import unittest"],
            "Exception": [],  # Built-in, no import needed
            "ValueError": [],  # Built-in, no import needed
            "object": [],  # Built-in, no import needed
        }

        return import_map.get(base_class, [])

    def _get_default_methods(self, options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get default methods based on class type"""
        class_type = options.get("class_type", "basic")

        if class_type == "data_class":
            return [
                {
                    "name": "to_dict",
                    "params": [],
                    "return_type": "Dict[str, Any]",
                    "description": "Convert instance to dictionary",
                    "body": "return self.__dict__",
                },
                {
                    "name": "from_dict",
                    "params": ["cls", "data: Dict[str, Any]"],
                    "return_type": f'{options.get("name", "Class")}',
                    "description": "Create instance from dictionary",
                    "body": "return cls(**data)",
                },
            ]
        elif class_type == "service":
            return [
                {
                    "name": "initialize",
                    "params": [],
                    "return_type": "None",
                    "description": "Initialize the service",
                    "body": "pass",
                },
                {
                    "name": "cleanup",
                    "params": [],
                    "return_type": "None",
                    "description": "Cleanup resources",
                    "body": "pass",
                },
            ]
        elif class_type == "builder":
            return [
                {
                    "name": "build",
                    "params": [],
                    "return_type": "Any",
                    "description": "Build the object",
                    "body": 'raise NotImplementedError("Subclasses must implement build method")',
                },
                {
                    "name": "reset",
                    "params": [],
                    "return_type": "None",
                    "description": "Reset the builder state",
                    "body": "pass",
                },
            ]

        return []

    def _get_file_path(self, name: str, options: Dict[str, Any]) -> Optional[Path]:
        """Get the file path for the class"""
        if "file_path" in options:
            return Path(options["file_path"])
        # Use explicit directory if provided
        if "directory" in options:
            base_dir = self.workspace_root / options["directory"]
        else:
            src_dir = self.workspace_root / "src"
            if src_dir.exists():
                base_dir = src_dir
            else:
                base_dir = self.workspace_root
        module_name = self.to_snake_case(name)
        return Path(base_dir) / f"{module_name}.py"

    def generate_dataclass(
        self, name: str, fields: List[Dict[str, Any]], options: Optional[Dict[str, Any]] = None
    ) -> GeneratedCode:
        """
        Generate a Python dataclass

        Args:
            name: Name of the dataclass
            fields: List of field definitions
            options: Additional options

        Returns:
            Generated code object
        """
        options = options or {}

        # Add dataclass-specific imports
        imports = ["from dataclasses import dataclass"]
        if any(field.get("default_factory") for field in fields):
            imports.append("from dataclasses import field")

        # Add typing imports if needed
        typing_imports = set()
        for field_def in fields:
            field_type = field_def.get("type", "Any")
            if any(t in field_type for t in ["List", "Dict", "Optional", "Union"]):
                typing_imports.update(["List", "Dict", "Optional", "Union", "Any"])

        if typing_imports:
            imports.append(f"from typing import {', '.join(sorted(typing_imports))}")

        options.update(
            {
                "imports": imports,
                "class_type": "dataclass",
                "decorators": ["@dataclass"],
                "fields": fields,
            }
        )

        # Override template for dataclass
        variables = self.get_common_variables(name, options)
        variables.update(options)

        template = (
            '''"""
{{ description or name + " dataclass" }}
{{ purpose or "Generated dataclass for " + name }}
"""

{% if imports %}
{% for import_line in imports %}
{{ import_line }}
{% endfor %}

{% endif %}
{% if decorators %}
{% for decorator in decorators %}
{{ decorator }}
{% endfor %}
{% endif %}
class {{ name_pascal }}:
    """
    {{ description or name + " dataclass" }}

    {% if docstring %}{{ docstring }}{% endif %}
    """

    {% for field in fields %}
    {{ field.name }}: {{ field.type }}'''
            + """{% if field.default is defined %} = {{ field.default }}"""
            + """{% elif field.default_factory %}"""
            + """ = field(default_factory={{ field.default_factory }})"""
            + """{% endif %}
    {% endfor %}

    {% if methods %}
    {% for method in methods %}
    def {{ method.name }}(self"""
            + """{% if method.params %}"""
            + """{% for param in method.params %}, {{ param }}{% endfor %}"""
            + """{% endif %})"""
            + '''{% if method.return_type %} -> {{ method.return_type }}{% endif %}:
        """{{ method.description or method.name }}"""
        {% if method.body %}
        {{ method.body }}
        {% else %}
        pass
        {% endif %}

    {% endfor %}
    {% endif %}
'''
        )

        content = self.render_string(template, variables)
        file_path = self._get_file_path(name, options)

        return GeneratedCode(
            content=content, file_path=file_path, language="python", purpose=f"{name} dataclass"
        )

    def generate_enum(
        self, name: str, values: List[str], options: Optional[Dict[str, Any]] = None
    ) -> GeneratedCode:
        """
        Generate a Python enum

        Args:
            name: Name of the enum
            values: List of enum values
            options: Additional options

        Returns:
            Generated code object
        """
        options = options or {}

        enum_type = options.get("enum_type", "Enum")
        imports = [f"from enum import {enum_type}"]

        variables = self.get_common_variables(name, options)
        variables.update(
            {
                "imports": imports,
                "enum_type": enum_type,
                "values": values,
                "description": options.get("description", f"{name} enumeration"),
            }
        )

        template = '''"""
{{ description }}
{{ purpose or "Generated enum for " + name }}
"""

{% if imports %}
{% for import_line in imports %}
{{ import_line }}
{% endfor %}

{% endif %}
class {{ name_pascal }}({{ enum_type }}):
    """{{ description }}"""

    {% for value in values %}
    {% if value is string %}
    {{ value.upper() }} = "{{ value.lower() }}"
    {% else %}
    {{ value.name.upper() }} = {{ value.value }}
    {% endif %}
    {% endfor %}
'''

        content = self.render_string(template, variables)
        file_path = self._get_file_path(name, options)

        return GeneratedCode(
            content=content, file_path=file_path, language="python", purpose=f"{name} enum"
        )
