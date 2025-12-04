"""
Shared utilities for Python code builders.
"""

from typing import Dict, List


def generate_default_test_cases(name: str, subject_type: str) -> List[Dict[str, str]]:
    """Generate default test cases based on the subject type."""

    def to_snake_case(text: str) -> str:
        import re

        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", text)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    if subject_type == "class":
        return [
            {
                "name": f"{to_snake_case(name)}_initialization",
                "description": f"Test {name} initialization with valid parameters",
                "setup": "# TODO: Set up initialization parameters",
                "action": "# TODO: Create instance",
                "assertion": "# TODO: Assert proper initialization",
            },
            {
                "name": f"{to_snake_case(name)}_str_representation",
                "description": f"Test {name} string representation",
                "setup": "# TODO: Create instance",
                "action": "result = str(instance)",
                "assertion": "assert isinstance(result, str) and len(result) > 0",
            },
        ]
    elif subject_type == "function":
        return [
            {
                "name": f"{to_snake_case(name)}_with_valid_input",
                "description": f"Test {name} with valid input",
                "setup": "# TODO: Set up valid input",
                "action": "# TODO: Call function",
                "assertion": "# TODO: Assert expected result",
            },
            {
                "name": f"{to_snake_case(name)}_with_invalid_input",
                "description": f"Test {name} with invalid input",
                "setup": "# TODO: Set up invalid input",
                "action": "# TODO: Call function expecting exception",
                "assertion": "# TODO: Assert exception is raised",
            },
        ]
    elif subject_type == "api":
        return [
            {
                "name": f"{to_snake_case(name)}_success_response",
                "description": f"Test {name} successful response",
                "setup": "# TODO: Set up valid request data",
                "action": "# TODO: Make API call",
                "assertion": "# TODO: Assert successful response",
            },
            {
                "name": f"{to_snake_case(name)}_error_response",
                "description": f"Test {name} error response",
                "setup": "# TODO: Set up invalid request data",
                "action": "# TODO: Make API call",
                "assertion": "# TODO: Assert error response",
            },
        ]
    return []
