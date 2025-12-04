#!/usr/bin/env python3
"""
Python Function Builder
Specialized builder for generating Python functions
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from ....template_engine import GeneratedCode
from ...base import BaseBuilder


class FunctionBuilder(BaseBuilder):
    """Builder for Python functions"""

    def __init__(self, template_engine, workspace_root: Path):
        super().__init__(template_engine)
        self.workspace_root: Path = workspace_root

    def build(self, name: str, options: Dict[str, Any]) -> GeneratedCode:
        """
        Build a Python function

        Args:
            name: Name of the function
            options: Function generation options

        Returns:
            Generated code object
        """
        variables = self.get_common_variables(name, options)

        # Extract function-specific options
        variables.update(
            {
                "description": options.get("description", f"{name} function"),
                "params": options.get("params", []),
                "return_type": options.get("return_type"),
                "return_description": options.get("return_description"),
                "param_descriptions": options.get("param_descriptions", {}),
                "exceptions": options.get("exceptions", []),
                "exception_descriptions": options.get("exception_descriptions", {}),
                "function_body": options.get("function_body"),
                "docstring_style": options.get("docstring_style", "google"),
                "imports": options.get("imports", []),
                "decorators": options.get("decorators", []),
                "is_async": options.get("is_async", False),
                "is_generator": options.get("is_generator", False),
            }
        )

        # Add typing imports if needed
        if variables["return_type"] or any(":" in param for param in variables["params"]):
            typing_imports = self._get_typing_imports(variables)
            variables["imports"].extend(typing_imports)
            variables["imports"] = list(dict.fromkeys(variables["imports"]))

        # Render the function template
        template = '''{% if imports %}
{% for import_line in imports %}
{{ import_line }}
{% endfor %}

{% endif %}
{% if decorators %}
{% for decorator in decorators %}
{{ decorator }}
{% endfor %}
{% endif %}
{% if is_async %}async {% endif %}def {{ name_snake }}(
    {% if params %}
        {% for param in params %}
            {{ param }}{% if not loop.last %}, {% endif %}
        {% endfor %}
    {% endif %}
){% if return_type %} -> {{ return_type }}{% endif %}:
{% if docstring_style == "google" %}    """{{ description }}

    {% if params %}
    Args:
    {% for param in params %}
        {{ param.split(':')[0].strip() }}: \
        {{ param_descriptions.get(param.split(':')[0].strip(), 'Parameter description') }}
    {% endfor %}

    {% endif %}
    {% if return_type and return_type != "None" %}
    Returns:
        {{ return_description or return_type + ": Return value description" }}

    {% endif %}
    {% if exceptions %}
    Raises:
    {% for exception in exceptions %}
        {{ exception }}: {{ exception_descriptions.get(exception, 'Exception description') }}
    {% endfor %}
    {% endif %}
    """
{% else %}    """
    {{ description }}

    {% if params %}
    Parameters:
    {% for param in params %}
        {{ param.split(':')[0].strip() }} : \
        {{ param.split(':')[1].strip() if ':' in param else 'type' }}
        {{ param_descriptions.get(param.split(':')[0].strip(), 'Parameter description') }}
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
    {% if is_generator %}
    yield  # Generator function
    {% elif return_type and return_type != "None" %}
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
    {% elif return_type.startswith("Optional") %}
    return None
    {% else %}
    return None
    {% endif %}
    {% else %}
    pass
    {% endif %}
    {% endif %}
'''

        content = self.render_string(template, variables)

        # Determine file path
        file_path = self._get_file_path(name, options)

        return GeneratedCode(
            content=content, file_path=file_path, language="python", purpose=f"{name} function"
        )

    def _get_typing_imports(self, variables: Dict[str, Any]) -> List[str]:
        """Get required typing imports"""
        imports = []
        typing_types = set()

        # Check return type
        return_type = variables.get("return_type", "")
        if return_type:
            typing_types.update(self._extract_typing_types(return_type))

        # Check parameter types
        for param in variables.get("params", []):
            if ":" in param:
                param_type = param.split(":", 1)[1].strip()
                typing_types.update(self._extract_typing_types(param_type))

        # Add imports for typing types
        if typing_types:
            imports.append(f"from typing import {', '.join(sorted(typing_types))}")

        return imports

    def _extract_typing_types(self, type_annotation: str) -> set:
        """Extract typing module types from type annotation"""
        typing_types = set()
        common_types = [
            "List",
            "Dict",
            "Tuple",
            "Set",
            "Optional",
            "Union",
            "Any",
            "Callable",
            "Iterator",
            "Generator",
            "AsyncIterator",
            "AsyncGenerator",
            "TypeVar",
            "Generic",
            "Protocol",
            "Literal",
            "Final",
            "ClassVar",
        ]

        for t in common_types:
            if t in type_annotation:
                typing_types.add(t)

        return typing_types

    def _get_file_path(self, name: str, options: Dict[str, Any]) -> Optional[Path]:
        """Get the file path for the function"""
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
        module_name = options.get("module_name", self.to_snake_case(name))
        return Path(base_dir / f"{module_name}.py")

    def generate_api_function(
        self, name: str, options: Optional[Dict[str, Any]] = None
    ) -> GeneratedCode:
        """
        Generate an API endpoint function

        Args:
            name: Name of the function
            options: Additional options

        Returns:
            Generated code object
        """
        options = options or {}

        method = options.get("method", "GET").upper()
        auth_required = options.get("auth_required", True)

        # Set up function parameters based on HTTP method
        params = []
        if method in ["POST", "PUT", "PATCH"]:
            params.append("request: Dict[str, Any]")
        if auth_required:
            params.append("current_user: Optional[Dict[str, Any]] = None")

        # Set up imports
        imports = [
            "from typing import Dict, Any, Optional",
            "from fastapi import HTTPException, status",
            "import logging",
        ]

        # Generate function body
        function_body = f"""logger = logging.getLogger(__name__)

    try:
        # TODO: Implement {method} {name} logic
        logger.info(f"Processing {method} request for {name}")

        result = {{
            "message": "{method} {name} successful",
            "data": {{}},
            "status": "success"
        }}

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid data: {{str(e)}}"
        )
    except Exception as e:
        logger.error(f"Error in {name} endpoint: {{e}}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )"""

        options.update(
            {
                "description": f"{method} endpoint for {name}",
                "params": params,
                "return_type": "Dict[str, Any]",
                "imports": imports,
                "function_body": function_body,
                "is_async": True,
            }
        )

        return self.build(name, options)

    def generate_utility_function(
        self, name: str, purpose: str, options: Optional[Dict[str, Any]] = None
    ) -> GeneratedCode:
        """
        Generate a utility function

        Args:
            name: Name of the function
            purpose: Purpose of the utility function
            options: Additional options

        Returns:
            Generated code object
        """
        options = options or {}

        utility_templates = {
            "validator": {
                "params": ["data: Any"],
                "return_type": "bool",
                "function_body": """if not isinstance(data, (dict, list, str, int, float, bool)):
        return False

    # TODO: Implement validation logic
    return True""",
                "description": f"Validate {name} data",
            },
            "formatter": {
                "params": ["value: Any"],
                "return_type": "str",
                "function_body": """# TODO: Implement formatting logic
    return str(value)""",
                "description": f"Format {name} value",
            },
            "converter": {
                "params": ["input_data: Any"],
                "return_type": "Any",
                "function_body": """# TODO: Implement conversion logic
    return input_data""",
                "description": f"Convert {name} data",
            },
            "calculator": {
                "params": ["values: List[float]"],
                "return_type": "float",
                "imports": ["from typing import List"],
                "function_body": """if not values:
        return 0.0

    # TODO: Implement calculation logic
    return sum(values) / len(values)""",
                "description": f"Calculate {name} result",
            },
        }

        template_config = utility_templates.get(purpose, {})
        options.update(template_config)

        return self.build(name, options)

    def generate_property_method(
        self, name: str, property_type: str = "getter", options: Optional[Dict[str, Any]] = None
    ) -> GeneratedCode:
        """
        Generate a property method (getter, setter, or deleter)

        Args:
            name: Name of the property
            property_type: Type of property method ('getter', 'setter', 'deleter')
            options: Additional options

        Returns:
            Generated code object
        """
        options = options or {}

        if property_type == "getter":
            decorators = ["@property"]
            params = []
            return_type = options.get("return_type", "Any")
            function_body = f"return self._{name}"
        elif property_type == "setter":
            decorators = [f"@{name}.setter"]
            params = [f'value: {options.get("value_type", "Any")}']
            return_type = "None"
            function_body = f"""# TODO: Add validation if needed
    self._{name} = value"""
        elif property_type == "deleter":
            decorators = [f"@{name}.deleter"]
            params = []
            return_type = "None"
            function_body = f"del self._{name}"
        else:
            raise ValueError(f"Invalid property_type: {property_type}")

        options.update(
            {
                "decorators": decorators,
                "params": params,
                "return_type": return_type,
                "function_body": function_body,
                "description": f"{property_type.title()} for {name} property",
            }
        )

        return self.build(name, options)
