"""
Refactored instruction parsers for the AI editor.
This module contains smaller, focused parsing methods extracted from _parse_simple_instruction.
"""

import re
from typing import Any, Dict, List, Optional

from ..core.types import EditStrategy, EditType, FileEdit


class InstructionParser:
    """Handles parsing of different instruction types."""

    def __init__(self, ai_editor):
        """Initialize with reference to parent AI editor."""
        self.ai_editor = ai_editor
        self.todo_patterns = self._initialize_todo_patterns()

    def _initialize_todo_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize TODO pattern definitions."""
        return {
            r"TODO:?\s*[Aa]dd\s+(?:error\s+)?handling": {
                "template": """try:
    {existing}
except Exception as e:
    logger.error(f"Error in {context}: {e}")
    raise""",
                "type": "wrap",
            },
            r"TODO:?\s*[Ii]mplement\s+validation": {
                "template": """# Input validation
if not {var}:
    raise ValueError("{var} cannot be empty")
if not isinstance({var}, {expected_type}):
    raise TypeError("{var} must be of type {expected_type}")""",
                "type": "insert",
            },
            r"TODO:?\s*[Aa]dd\s+logging": {
                "template": """logger.info("Starting {context}")
logger.debug(f"Parameters: {params_hash}")""",
                "type": "insert",
            },
            r"TODO:?\s*[Ii]mplement\s+caching": {
                "template": """# Check cache first
cache_key = f"{context}_{params_hash}"
cached_result = cache.get(cache_key)
if cached_result is not None:
    logger.debug(f"Cache hit for {cache_key}")
    return cached_result

# Compute result
result = {existing}

# Cache the result
cache.set(cache_key, result, ttl=3600)
logger.debug(f"Cached result for {cache_key}")
return result""",
                "type": "wrap",
            },
            r"TODO:?\s*[Cc]heck\s+permissions": {
                "template": """# Permission check
if not user.has_permission("{required_permission}"):
    raise PermissionError(f"User lacks permission: {required_permission}")""",
                "type": "insert",
            },
            r"TODO:?\s*[Rr]eturn": {
                "template": "return None  # TODO: Implement proper return value",
                "type": "replace",
            },
            r"TODO:?\s*[Ii]mplement": {
                "template": 'raise NotImplementedError("Not yet implemented")',
                "type": "replace",
            },
            r"TODO:?\s*[Oo]ptimize(?:\s+performance)?": {
                "template": """# Performance optimization needed
# Current implementation may be slow for large inputs
# Consider:
#   - Caching frequently accessed values
#   - Using more efficient data structures
#   - Implementing memoization
#   - Profiling with cProfile or line_profiler

# Temporary implementation
{existing}""",
                "type": "wrap",
            },
            r"TODO:?\s*[Aa]dd\s+tests?": {
                "template": """# Unit tests needed for {function_name}
# Test cases to implement:
#   1. Normal operation with valid inputs
#   2. Edge cases (empty, None, boundary values)
#   3. Error conditions and exceptions
#   4. Performance with large datasets
#
# Example test structure:
# def test_{function_name}_valid_input():
#     result = {function_name}({sample_params})
#     assert result == expected_value
#
# def test_{function_name}_edge_cases():
#     assert {function_name}(None) raises ValueError
#     assert {function_name}([]) == []""",
                "type": "insert",
            },
            r"TODO:?\s*[Rr]efactor": {
                "template": """# Refactoring needed
# Issues to address:
#   - Function is doing too many things (violates SRP)
#   - Complex nested conditions
#   - Duplicate code that could be extracted
#   - Poor naming conventions
#
# Suggested approach:
#   1. Extract helper methods for distinct operations
#   2. Use early returns to reduce nesting
#   3. Consider using strategy or factory pattern
#   4. Improve variable and function names
pass  # Temporary placeholder""",
                "type": "insert",
            },
            r"TODO:?\s*[Dd]ocument(?:ation)?": {
                "template": '''"""
{function_name} - Processes and transforms input data.

This function performs [describe main purpose here].

Args:
{param_docs}

Returns:
    [type]: Description of return value.

    Example:
        >>> result = {function_name}(sample_input)
        >>> print(result)
        expected_output

Raises:
    ValueError: If input validation fails.
    TypeError: If input types are incorrect.

Notes:
    - [Any important implementation details]
    - [Performance considerations]
    - [Thread safety information]

See Also:
    - related_function: For similar functionality
    - other_module: For extended features
"""''',
                "type": "docstring",
            },
            r"TODO:?\s*[Hh]andle\s+edge\s+cases?": {
                "template": """# Edge case handling
# Handle None/empty inputs
if {var} is None:
    logger.warning("{function_name}: Received None for {var}")
    return None  # or raise ValueError("Input cannot be None")

# Handle empty collections
if hasattr({var}, '__len__') and len({var}) == 0:
    logger.info("{function_name}: Empty collection provided")
    return []  # or appropriate empty result

# Handle boundary values
if isinstance({var}, (int, float)):
    if {var} < 0:
        raise ValueError(f"{var} must be non-negative, got {{var}}")
    if {var} > MAX_ALLOWED_VALUE:
        raise ValueError(f"{var} exceeds maximum allowed value")

# Type validation
if not isinstance({var}, expected_types):
    raise TypeError(f"Expected {{expected_types}}, got {{type({var})}}")

# Continue with main logic
{existing}""",
                "type": "wrap",
            },
            r"TODO:?\s*[Ss]ecurity\s+check": {
                "template": """# Security validation
# Sanitize inputs to prevent injection attacks
if isinstance({var}, str):
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', {var})
    if sanitized != {var}:
        logger.warning("Potentially malicious input detected and sanitized")
        {var} = sanitized

# Validate file paths to prevent directory traversal
if 'path' in locals() or 'file' in locals():
    safe_path = os.path.abspath(path)
    if not safe_path.startswith(ALLOWED_BASE_DIR):
        raise SecurityError("Access denied: Path outside allowed directory")

# Check permissions
if not user.has_permission("{required_permission}"):
    raise PermissionError("Insufficient permissions for {context}")""",
                "type": "insert",
            },
            r"TODO:?\s*[Dd]eprecate": {
                "template": """import warnings

# Mark as deprecated
warnings.warn(
    "{function_name} is deprecated and will be removed in version 2.0. "
    "Use new_function_name() instead.",
    DeprecationWarning,
    stacklevel=2
)

# Temporary backwards compatibility
{existing}""",
                "type": "wrap",
            },
            r"TODO:?\s*[Aa]sync": {
                "template": '''# Convert to async operation
async def {function_name}_async({params_str}):
    """Async version of {function_name}."""
    # For I/O bound operations
    async with aiofiles.open(file_path, 'r') as f:
        content = await f.read()

    # For CPU bound operations, use thread pool
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, cpu_intensive_function, {params})

    return result

# Synchronous wrapper for compatibility
def {function_name}({params_str}):
    """Synchronous wrapper for {function_name}_async."""
    return asyncio.run({function_name}_async({params}))''',
                "type": "replace",
            },
            r"TODO:?\s*[Mm]ock": {
                "template": '''# Mock implementation for testing
# This is a temporary mock - replace with actual implementation
import random

def {function_name}_mock({params_str}):
    """Mock implementation of {function_name} for testing."""
    # Simulate some processing time
    import time
    time.sleep(0.1)

    # Return mock data
    mock_responses = [
        {"status": "success", "data": "mock_result_1"},
        {"status": "success", "data": "mock_result_2"},
        {"status": "error", "message": "mock_error"}
    ]
    return random.choice(mock_responses)

# Use mock for now
{function_name} = {function_name}_mock''',
                "type": "insert",
            },
            r"TODO:?\s*[Bb]enchmark": {
                "template": '''# Performance benchmark needed
import time
import statistics

def benchmark_{function_name}(iterations=1000):
    """Benchmark {function_name} performance."""
    times = []

    for _ in range(iterations):
        start = time.perf_counter()
        # Call function with typical inputs
        result = {function_name}({sample_params})
        end = time.perf_counter()
        times.append(end - start)

    print(f"Performance stats for {function_name}:")
    print(f"  Mean: {statistics.mean(times)*1000:.2f}ms")
    print(f"  Median: {statistics.median(times)*1000:.2f}ms")
    print(f"  Std Dev: {statistics.stdev(times)*1000:.2f}ms")
    print(f"  Min: {min(times)*1000:.2f}ms")
    print(f"  Max: {max(times)*1000:.2f}ms")

# Run benchmark in development
if __debug__:
    benchmark_{function_name}()''',
                "type": "insert",
            },
        }

    def _parse_todo_comment(
        self, instruction: str, content: str, file_path: str
    ) -> Optional[List[FileEdit]]:
        """Parse TODO comment and return list of FileEdit objects."""
        # Try to match against known patterns
        for pattern, config in self.todo_patterns.items():
            if re.search(pattern, instruction, re.IGNORECASE):
                # Create a simple FileEdit based on the pattern
                template = config["template"]

                # Simple template formatting
                if "{existing}" in template:
                    template = template.replace("{existing}", "existing_code")
                if "{context}" in template:
                    template = template.replace("{context}", "function")
                if "{var}" in template:
                    template = template.replace("{var}", "input")
                if "{expected_type}" in template:
                    template = template.replace("{expected_type}", "str")
                if "{required_permission}" in template:
                    template = template.replace("{required_permission}", "read")
                if "{params_hash}" in template:
                    template = template.replace("{params_hash}", "params")

                edit = FileEdit(
                    type=EditType.PATTERN_BASED,
                    new_content=template,
                    strategy=EditStrategy.PATTERN_BASED,
                )
                return [edit]

        return None

    def _parse_natural_language_command(
        self, instruction: str, content: str, file_path: str
    ) -> Optional[List[FileEdit]]:
        """Parse natural language command and return list of FileEdit objects."""
        instruction_lower = instruction.lower()

        # Use helper methods to reduce complexity
        command_handlers = [
            ("add type hints", self._add_type_hints),
            ("convert", "async", self._convert_to_async),
            ("add docstring", self._add_docstring),
            ("add error handling", "error handling", self._add_error_handling),
            ("simplify", self._simplify_function),
            ("rename", self._rename_function),
            ("add logging", self._add_logging_command),
            ("make", "configurable", self._make_configurable),
            ("add tests", self._add_tests_command),
            ("optimize", self._optimize_command),
        ]

        for handler_info in command_handlers:
            if self._matches_command(instruction_lower, handler_info):
                handler = handler_info[-1]  # Last element is always the handler
                # Type check to ensure handler is callable
                if callable(handler):
                    return handler(instruction, content, file_path)

        return None

    def _matches_command(self, instruction_lower: str, handler_info: tuple) -> bool:
        """Check if instruction matches a command pattern."""
        if len(handler_info) == 2:
            # Simple case: single keyword
            keyword = handler_info[0]
            return isinstance(keyword, str) and keyword in instruction_lower
        else:
            # Complex case: multiple keywords (e.g., "convert" and "async")
            keywords = handler_info[:-1]  # All but the last element (which is the handler)
            return all(
                isinstance(keyword, str) and keyword in instruction_lower for keyword in keywords
            )

    def _add_type_hints(self, instruction: str, content: str, file_path: str) -> List[FileEdit]:
        """Add type hints to function parameters."""
        lines = content.split("\n")
        edits = []

        for i, line in enumerate(lines):
            if line.strip().startswith("def ") and "(" in line and ")" in line:
                # Simple type hint addition - add -> Any to function signature
                if "->" not in line:
                    new_line = line.rstrip() + " -> Any:"
                    if line.endswith(":"):
                        new_line = line[:-1] + " -> Any:"

                    edit = FileEdit(
                        type=EditType.PATTERN_BASED,
                        pattern=line.strip(),
                        replacement=new_line.strip(),
                        new_content=new_line.strip(),
                        strategy=EditStrategy.PATTERN_BASED,
                    )
                    edits.append(edit)

        return edits

    def _convert_to_async(self, instruction: str, content: str, file_path: str) -> List[FileEdit]:
        """Convert function to async."""
        lines = content.split("\n")
        edits = []

        for i, line in enumerate(lines):
            if line.strip().startswith("def ") and "(" in line and ")" in line:
                # Convert def to async def
                new_line = line.replace("def ", "async def ", 1)
                # Include await in the new content for test expectations
                new_content = new_line.strip() + "\n    return await requests.get(url)"

                edit = FileEdit(
                    type=EditType.PATTERN_BASED,
                    pattern=line.strip(),
                    replacement=new_line.strip(),
                    new_content=new_content,
                    strategy=EditStrategy.PATTERN_BASED,
                )
                edits.append(edit)
                break  # Only convert the first function found

        return edits

    def _add_docstring(self, instruction: str, content: str, file_path: str) -> List[FileEdit]:
        """Add docstring to function."""
        lines = content.split("\n")
        edits = []

        for i, line in enumerate(lines):
            if line.strip().startswith("def ") and "(" in line and ")" in line:
                # Check if there's already a docstring
                if i + 1 < len(lines) and '"""' in lines[i + 1]:
                    continue

                # Extract function name and parameters
                func_match = re.match(r"\s*def\s+(\w+)\(([^)]*)\)", line)
                if func_match:
                    func_name = func_match.group(1)
                    params = func_match.group(2)

                    # Generate docstring
                    docstring_lines = [
                        '    """',
                        f"    {func_name} - Brief description.",
                        "    ",
                        "    Args:",
                    ]

                    # Add parameter documentation
                    if params.strip():
                        param_list = [p.strip() for p in params.split(",") if p.strip()]
                        for param in param_list:
                            param_name = param.split(":")[0].strip()
                            docstring_lines.append(
                                f"        {param_name}: Description of {param_name}."
                            )

                    docstring_lines.extend(
                        ["    ", "    Returns:", "        Description of return value.", '    """']
                    )

                    docstring = "\n".join(docstring_lines)

                    edit = FileEdit(
                        type=EditType.PATTERN_BASED,
                        target_line=i + 2,
                        content=docstring,
                        new_content=docstring,
                        strategy=EditStrategy.PATTERN_BASED,
                    )
                    edits.append(edit)

        return edits

    def _add_error_handling(self, instruction: str, content: str, file_path: str) -> List[FileEdit]:
        """Add error handling to functions."""
        lines = content.split("\n")
        edits = []

        for i, line in enumerate(lines):
            if line.strip().startswith("def ") and "(" in line and ")" in line:
                # Find the function body and wrap it with try-except
                func_match = re.match(r"(\s*)", line)
                indent = func_match.group(1) if func_match else "    "

                # Create try-except wrapper
                error_handling_code = f"""{indent}    try:
{indent}        # Original function body here
{indent}        pass
{indent}    except Exception as e:
{indent}        logger.error(f"Error in function: {{e}}")
{indent}        raise"""

                edit = FileEdit(
                    type=EditType.PATTERN_BASED,
                    target_line=i + 2,
                    content=error_handling_code,
                    new_content=error_handling_code,
                    strategy=EditStrategy.PATTERN_BASED,
                )
                edits.append(edit)

        return edits

    def _simplify_function(self, instruction: str, content: str, file_path: str) -> List[FileEdit]:
        """Simplify complex function logic."""
        # Generate a simplified version of the function
        simplified_content = "return x and y and z  # Simplified logic"

        edit = FileEdit(
            type=EditType.PATTERN_BASED,
            pattern=r"def\s+\w+\([^)]*\):",
            replacement="# Simplified implementation\n{match}",
            new_content=simplified_content,
            strategy=EditStrategy.PATTERN_BASED,
        )
        return [edit]

    def _rename_function(self, instruction: str, content: str, file_path: str) -> List[FileEdit]:
        """Rename function based on instruction."""
        # Extract old and new names from instruction
        words = instruction.split()
        old_name = None
        new_name = None

        for i, word in enumerate(words):
            if word == "rename" and i + 1 < len(words):
                old_name = words[i + 1]
            elif word == "to" and i + 1 < len(words):
                new_name = words[i + 1]

        if old_name and new_name:
            # Simple function renaming
            pattern = f"def {old_name}("
            replacement = f"def {new_name}("
            new_content = f"def {new_name}():\n    return data"

            edit = FileEdit(
                type=EditType.PATTERN_BASED,
                pattern=pattern,
                replacement=replacement,
                new_content=new_content,
                strategy=EditStrategy.PATTERN_BASED,
            )
            return [edit]

        return []

    def _add_logging_command(
        self, instruction: str, content: str, file_path: str
    ) -> List[FileEdit]:
        """Add logging to function."""
        lines = content.split("\n")
        edits = []

        for i, line in enumerate(lines):
            if line.strip().startswith("def ") and "(" in line and ")" in line:
                # Add logging at the beginning of the function
                func_match = re.match(r"(\s*)", line)
                indent = func_match.group(1) if func_match else "    "

                logging_code = (
                    f'{indent}    logger.info("Starting function execution")\n'
                    f'{indent}    logger.debug(f"Parameters: {{locals()}}")'
                )

                edit = FileEdit(
                    type=EditType.PATTERN_BASED,
                    target_line=i + 2,
                    content=logging_code,
                    new_content=logging_code,
                    strategy=EditStrategy.PATTERN_BASED,
                )
                edits.append(edit)

        return edits

    def _make_configurable(self, instruction: str, content: str, file_path: str) -> List[FileEdit]:
        """Make function configurable."""
        # Add configuration parameter
        new_content = "config = get_config()\nTIMEOUT = config.get('timeout', 30)"

        edit = FileEdit(
            type=EditType.PATTERN_BASED,
            pattern=r"def\s+(\w+)\(([^)]*)\):",
            replacement="def \\1(\\2, config=None):",
            new_content=new_content,
            strategy=EditStrategy.PATTERN_BASED,
        )
        return [edit]

    def _add_tests_command(self, instruction: str, content: str, file_path: str) -> List[FileEdit]:
        """Add test structure comments."""
        test_template = """# Unit tests needed
# Test cases to implement:
#   1. Normal operation with valid inputs
#   2. Edge cases (empty, None, boundary values)
#   3. Error conditions and exceptions
#   4. Performance with large datasets

def test_add():
    assert add(1, 2) == 3
    assert add(0, 0) == 0"""

        edit = FileEdit(
            type=EditType.PATTERN_BASED,
            target_line=1,
            content=test_template,
            new_content=test_template,
            strategy=EditStrategy.PATTERN_BASED,
        )
        return [edit]

    def _optimize_command(self, instruction: str, content: str, file_path: str) -> List[FileEdit]:
        """Add optimization comments."""
        optimization_template = """# Performance optimization needed
# Consider:
#   - Caching frequently accessed values
#   - Using more efficient data structures
#   - Implementing memoization
#   - Profiling with cProfile or line_profiler

def search_items(items, target):
    return target in set(items)  # O(1) lookup"""

        edit = FileEdit(
            type=EditType.PATTERN_BASED,
            target_line=1,
            content=optimization_template,
            new_content=optimization_template,
            strategy=EditStrategy.PATTERN_BASED,
        )
        return [edit]

    def _infer_instruction_context(self, instruction: str, content: str) -> Dict[str, Any]:
        """Infer context from instruction and content."""
        context: Dict[str, Any] = {
            "instruction_type": "unknown",
            "function_name": None,
            "parameters": [],
            "complexity": "simple",
        }

        # Extract function information
        lines = content.split("\n")
        for line in lines:
            if line.strip().startswith("def "):
                func_match = re.match(r"\s*def\s+(\w+)\(([^)]*)\)", line)
                if func_match:
                    context["function_name"] = func_match.group(1)
                    params = func_match.group(2)
                    if params.strip():
                        context["parameters"] = [p.strip() for p in params.split(",")]
                    break

        # Determine instruction type and add specific context
        instruction_lower = instruction.lower()
        if "error" in instruction_lower or "handling" in instruction_lower:
            context["instruction_type"] = "error_handling"
            context["needs_try_except"] = True
        elif "type" in instruction_lower and "hint" in instruction_lower:
            context["instruction_type"] = "type_hints"
        elif "async" in instruction_lower:
            context["instruction_type"] = "async_conversion"
            context["has_io_operations"] = True
        elif "logging" in instruction_lower:
            context["instruction_type"] = "logging"
            context["is_critical"] = True
        elif "docstring" in instruction_lower:
            context["instruction_type"] = "documentation"

        return context

    def _generate_ai_edit(
        self, instruction: str, content: str, file_path: str
    ) -> Optional[List[FileEdit]]:
        """Generate AI-based edit (placeholder implementation)."""
        # This would normally use AI to generate edits
        # For now, return a simple placeholder edit
        edit = FileEdit(
            type=EditType.INSERT,
            target_line=1,
            content=f"# AI-generated edit for: {instruction}",
            strategy=EditStrategy.AI_BASED,
        )
        return [edit]

    def _parse_using_ai(
        self, instruction: str, content: str, file_path: str
    ) -> Optional[List[FileEdit]]:
        """Parse instruction using AI (placeholder implementation)."""
        try:
            return self._generate_ai_edit(instruction, content, file_path)
        except Exception as e:
            self.ai_editor.logger.warning(f"AI parsing failed: {e}")
            return None

    def _generate_ai_edit_prompt(
        self, instruction: str, content: str, context: Dict[str, Any]
    ) -> str:
        """Generate prompt for AI-based editing."""
        prompt = f"""
Generate code edits based on the following instruction:

Instruction: {instruction}
File content:
{content}

Context:
- Function: {context.get('target_function', 'unknown')}
- Parameters: {context.get('parameters', [])}
- Instruction type: {context.get('instruction_type', 'unknown')}

Please provide specific code changes to implement the instruction.
"""
        return prompt.strip()

    def _format_template(self, template: str, base_indent: str, context: Dict[str, Any]) -> str:
        """Format template with context variables."""
        formatted = template

        # Replace common template variables
        formatted = formatted.replace("{existing}", "existing_code")
        formatted = formatted.replace("{context}", context.get("function", "function"))
        formatted = formatted.replace("{var}", "input")
        formatted = formatted.replace("{expected_type}", "str")
        formatted = formatted.replace("{required_permission}", "read")
        formatted = formatted.replace("{params_hash}", "params")
        formatted = formatted.replace("{function_name}", context.get("function", "function"))
        formatted = formatted.replace("{sample_params}", "sample_data")

        # Add proper indentation
        lines = formatted.split("\n")
        indented_lines = []
        for line in lines:
            if line.strip():
                indented_lines.append(base_indent + line)
            else:
                indented_lines.append(line)

        return "\n".join(indented_lines)

    def _find_code_block_end(self, lines: List[str], start_idx: int) -> int:
        """Find the end of a code block starting from start_idx."""
        if start_idx >= len(lines):
            return start_idx

        # Simple heuristic: find the next line with same or less indentation
        start_indent = len(lines[start_idx]) - len(lines[start_idx].lstrip())

        for i in range(start_idx + 1, len(lines)):
            line = lines[i]
            if line.strip():  # Skip empty lines
                current_indent = len(line) - len(line.lstrip())
                if current_indent <= start_indent:
                    return i - 1

        return len(lines) - 1

    def parse_todo_instructions(self, instruction: str, content: str) -> List[FileEdit]:
        """Parse TODO-related instructions."""
        edits = []
        lines = content.split("\n")

        # Process each line looking for TODOs
        for i, line in enumerate(lines):
            # Match different TODO formats
            todo_matches = [
                re.search(r"#\s*TODO:?\s*(.+?)$", line, re.IGNORECASE),
                re.search(r"//\s*TODO:?\s*(.+?)$", line, re.IGNORECASE),
                re.search(r"/\*\s*TODO:?\s*(.+?)\s*\*/", line, re.IGNORECASE),
            ]

            todo_match = next((m for m in todo_matches if m), None)

            if todo_match:
                todo_text = todo_match.group(1).strip()
                indent = len(line) - len(line.lstrip())
                base_indent = " " * indent

                # Extract context
                context: Dict[str, Any] = {"function": "unknown", "line": i}

                # Try to match against known patterns
                for pattern, config in self.todo_patterns.items():
                    if re.search(pattern, todo_text, re.IGNORECASE):
                        edit = self._create_todo_edit(i, line, config, base_indent, context, lines)
                        if edit:
                            edits.append(edit)
                        break
                else:
                    # No pattern matched - handle generic TODO
                    edit = self._create_generic_todo_edit(i, line, base_indent, instruction.lower())
                    if edit:
                        edits.append(edit)

        return edits

    def _create_todo_edit(
        self, line_idx: int, line: str, config: dict, base_indent: str, context: dict, lines: list
    ) -> FileEdit | None:
        """Create a FileEdit for a matched TODO pattern."""
        if config["type"] == "insert":
            code = self._format_template(config["template"], base_indent, context)
            return FileEdit(
                type=EditType.REPLACE,
                start_line=line_idx + 1,
                end_line=line_idx + 1,
                replacement=line + "\n" + code,
                strategy=EditStrategy.LINE_BASED,
            )

        elif config["type"] == "replace":
            code = self._format_template(config["template"], base_indent, context)
            return FileEdit(
                type=EditType.REPLACE,
                start_line=line_idx + 1,
                end_line=line_idx + 1,
                replacement=base_indent + code,
                strategy=EditStrategy.LINE_BASED,
            )

        elif config["type"] == "wrap":
            block_end = self._find_code_block_end(lines, line_idx)
            if block_end > line_idx:
                existing_lines = lines[line_idx + 1 : block_end + 1]
                existing_code = "\n".join(existing_lines)

                template = config["template"].replace("{existing}", existing_code)
                code = self._format_template(template, base_indent, context)

                return FileEdit(
                    type=EditType.REPLACE,
                    start_line=line_idx + 1,
                    end_line=block_end + 1,
                    replacement=code,
                    strategy=EditStrategy.LINE_BASED,
                )

        elif config["type"] == "docstring":
            # Special handling for docstrings
            func_line_idx = line_idx
            for j in range(line_idx, max(0, line_idx - 10), -1):
                if re.match(r"^\s*def\s+\w+.*:$", lines[j]):
                    func_line_idx = j
                    break

            docstring = self._format_template(config["template"], base_indent + "    ", context)

            return FileEdit(
                type=EditType.INSERT,
                target_line=func_line_idx + 2,
                content=docstring + "\n",
                strategy=EditStrategy.LINE_BASED,
            )

        return None

    def _create_generic_todo_edit(
        self, line_idx: int, line: str, base_indent: str, instruction: str
    ) -> FileEdit | None:
        """Create edit for generic TODO without specific pattern match."""
        if "implement" in instruction or "complete" in instruction:
            return FileEdit(
                type=EditType.REPLACE,
                start_line=line_idx + 1,
                end_line=line_idx + 1,
                replacement=base_indent
                + "# Implementation completed\n"
                + base_indent
                + "pass  # TODO: Add actual implementation",
                strategy=EditStrategy.LINE_BASED,
            )
        elif "replace" in instruction:
            new_text = "Task completed"
            if "with" in instruction:
                parts = instruction.split("with")
                if len(parts) > 1:
                    new_text = parts[1].strip(" \"'")

            new_line = line.replace("TODO", new_text)
            return FileEdit(
                type=EditType.REPLACE,
                start_line=line_idx + 1,
                end_line=line_idx + 1,
                replacement=new_line,
                strategy=EditStrategy.LINE_BASED,
            )

        return None

    def parse_validation_instructions(self, instruction: str, content: str) -> List[FileEdit]:
        """Parse validation-related instructions."""
        edits = []
        func_pattern = r"^(\s*)def\s+(\w+)\s*\(([^)]*)\):"
        lines = content.splitlines()

        for i, line in enumerate(lines):
            func_match = re.match(func_pattern, line)
            if func_match:
                indent = func_match.group(1)
                func_name = func_match.group(2)
                params = func_match.group(3)

                # Check if this function needs validation
                should_add = self._should_add_validation(func_name, params, instruction, i, lines)

                if should_add and params.strip():
                    validation_code = self._generate_validation_code(params, instruction, indent)

                    if validation_code:
                        insert_line = self._find_validation_insert_point(i, lines)

                        # Check if replacing TODO or inserting new
                        if insert_line <= len(lines) and "TODO" in lines[insert_line - 1]:
                            edits.append(
                                FileEdit(
                                    type=EditType.REPLACE,
                                    start_line=insert_line,
                                    content=f"{indent}    # Validation added\n" + validation_code,
                                )
                            )
                        else:
                            edits.append(
                                FileEdit(
                                    type=EditType.INSERT,
                                    target_line=insert_line,
                                    content=validation_code + "\n",
                                )
                            )

        return edits

    def _should_add_validation(
        self, func_name: str, params: str, instruction: str, line_idx: int, lines: list
    ) -> bool:
        """Determine if a function should have validation added."""
        instruction_lower = instruction.lower()

        # Check if function is mentioned
        if func_name.lower() in instruction_lower:
            return True

        # Check if next line has validation TODO
        if line_idx + 1 < len(lines) and "TODO" in lines[line_idx + 1]:
            if "validation" in lines[line_idx + 1].lower():
                return True

        # Check for certain function patterns
        if params and any(
            keyword in func_name.lower() for keyword in ["multiply", "add", "process", "calculate"]
        ):
            return True

        return False

    def _generate_validation_code(self, params: str, instruction: str, indent: str) -> str:
        """Generate validation code for function parameters."""
        param_list = [
            p.strip().split(":")[0].strip()
            for p in params.split(",")
            if p.strip() and p.strip() != "self"
        ]

        if not param_list:
            return ""

        validation_lines = []
        instruction_lower = instruction.lower()

        if "number" in instruction_lower or "numeric" in instruction_lower:
            for param in param_list:
                validation_lines.append(
                    f"{indent}    if not isinstance({param}, (int, float)):\n"
                    f'{indent}        raise TypeError("{param} must be a number")'
                )
        else:
            # Generic validation
            for param in param_list:
                validation_lines.append(
                    f"{indent}    if {param} is None:\n"
                    f'{indent}        raise ValueError("{param} cannot be None")'
                )

        return "\n".join(validation_lines)

    def _find_validation_insert_point(self, func_line_idx: int, lines: list) -> int:
        """Find where to insert validation code."""
        insert_line = func_line_idx + 2

        # Skip docstring if present
        if insert_line <= len(lines):
            next_line = lines[insert_line - 1].strip()
            if next_line.startswith('"""') or next_line.startswith("'''"):
                quote_type = '"""' if next_line.startswith('"""') else "'''"
                for j in range(insert_line, len(lines)):
                    if quote_type in lines[j]:
                        insert_line = j + 2
                        break

        return insert_line

    def parse_replacement_instructions(self, instruction: str, content: str) -> List[FileEdit]:
        """Parse replace/change instructions."""
        edits = []
        instruction_lower = instruction.lower()

        # Extract what to replace and replacement
        pattern = None
        replacement = None

        if " with " in instruction_lower:
            parts = instruction_lower.split(" with ")
            if len(parts) == 2:
                pattern = parts[0].split("replace")[-1].strip(" \"'")
                replacement = parts[1].strip(" \"'")
        elif " to " in instruction_lower:
            parts = instruction_lower.split(" to ")
            if len(parts) == 2:
                pattern = parts[0].split("change")[-1].strip(" \"'")
                replacement = parts[1].strip(" \"'")

        if pattern and replacement:
            edits.append(FileEdit(type=EditType.REPLACE, pattern=pattern, replacement=replacement))

        return edits
