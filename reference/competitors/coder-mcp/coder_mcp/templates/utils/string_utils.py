import re

__all__ = [
    "to_snake_case",
    "to_camel_case",
    "to_pascal_case",
    "to_kebab_case",
    "capitalize_first",
]


def to_snake_case(text: str) -> str:
    """Convert text to snake_case"""
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", text)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def to_camel_case(text: str) -> str:
    """Convert text to camelCase"""
    components = text.replace("-", "_").split("_")
    return components[0].lower() + "".join(word.capitalize() for word in components[1:])


def to_pascal_case(text: str) -> str:
    """Convert text to PascalCase"""
    components = text.replace("-", "_").split("_")
    return "".join(word.capitalize() for word in components)


def to_kebab_case(text: str) -> str:
    """Convert text to kebab-case"""
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1-\2", text)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", s1).lower()


def capitalize_first(text: str) -> str:
    """Capitalize first letter of text"""
    return text[0].upper() + text[1:] if text else text
