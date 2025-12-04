import json


def load_inputs(json_file_path: str, limit: int | None = None) -> list[str]:
    """
    Load test inputs from JSON file and return as a list of strings.

    Args:
        json_file_path: Path to the JSON file
        limit: Optional limit on number of inputs to load (None = load all)

    Returns:
        List of user input strings
    """
    with open(json_file_path) as f:
        data = json.load(f)

    user_inputs = data.get("user_input", {})

    # Sort by numeric key and return just the values
    sorted_keys = sorted(user_inputs.keys(), key=lambda x: int(x))

    # Apply limit if specified
    if limit is not None and limit > 0:
        sorted_keys = sorted_keys[:limit]

    return [user_inputs[key] for key in sorted_keys]
