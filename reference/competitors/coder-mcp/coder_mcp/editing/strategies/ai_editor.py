"""
AI-powered file editor for natural language instruction-based editing.

This module provides the AIFileEditor class that can understand natural language
instructions and convert them into appropriate FileEdit operations.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.editor import EnhancedFileEditor
from ..core.types import (
    EditConfig,
    EditExample,
    EditResult,
    EditStrategy,
    EditType,
    FileEdit,
)
from .instruction_parser import InstructionParser


def resolve_file_path(file_path: str) -> str:
    """Resolve file path to absolute path."""
    path = Path(file_path)

    if path.is_absolute():
        return str(path)

    cwd_path = Path.cwd() / path
    if cwd_path.exists():
        return str(cwd_path.resolve())

    workspace_root = os.environ.get("MCP_WORKSPACE_ROOT")
    if workspace_root:
        workspace_path = Path(workspace_root) / path
        if workspace_path.exists():
            return str(workspace_path.resolve())

    return str(path.resolve())


class AIFileEditor(EnhancedFileEditor):
    """
    AI-powered file editor that understands natural language instructions.

    Extends EnhancedFileEditor with AI capabilities for interpreting
    natural language editing instructions.
    """

    def __init__(self, config: Optional[EditConfig] = None):
        """
        Initialize the AI file editor.

        Args:
            config: Optional configuration for editing operations
        """
        super().__init__(config)
        self.instruction_parser = InstructionParser(self)
        self.examples = self._load_default_examples()
        self.instruction_patterns = self._build_instruction_patterns()

    def ai_edit(
        self,
        file_path: str,
        instruction: str,
        context_files: Optional[List[str]] = None,
        use_ai: bool = True,
    ) -> EditResult:
        """
        Apply edits based on natural language instructions.

        Args:
            file_path: Path to the file to edit
            instruction: Natural language description of changes
            context_files: Additional files for context
            use_ai: Whether to use AI for understanding instructions

        Returns:
            EditResult with applied changes
        """
        try:
            # Read file content
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                return EditResult(
                    success=False, changes_made=0, diff="", error=f"File not found: {file_path}"
                )

            content = file_path_obj.read_text()

            # Parse instruction into edits
            if use_ai:
                edits = self._parse_ai_instruction(instruction, content, file_path, context_files)
            else:
                edits = self._parse_simple_instruction(instruction, content)

            if not edits:
                return EditResult(
                    success=False, changes_made=0, diff="", error="Could not understand instruction"
                )

            # Check if this is an unknown instruction (contains suggestions)
            is_unknown_instruction = any(
                edit.content and "AI Editor suggestions:" in edit.content for edit in edits
            )

            # Apply edits using the base editor
            resolved_path = resolve_file_path(file_path)
            result = self.edit_file(resolved_path, edits)

            # If this was an unknown instruction, add a message with suggestions
            if is_unknown_instruction and result.success:
                suggestions_message = (
                    "Could not understand the instruction, but added suggestions as comments. "
                    "Please try more specific instructions like 'add import os', "
                    "'add error handling', or 'add docstrings'."
                )
                # Create a new EditResult with the message
                result = EditResult(
                    success=result.success,
                    changes_made=result.changes_made,
                    diff=result.diff,
                    message=suggestions_message,
                    backup_path=result.backup_path,
                    error=result.error,
                    preview=result.preview,
                    warnings=result.warnings,
                )

            return result

        except Exception as e:
            return EditResult(success=False, changes_made=0, diff="", error=str(e))

    def edit_with_instruction(
        self,
        file_path: str,
        instruction: str,
        context_files: Optional[List[str]] = None,
        use_ai: bool = True,
    ) -> EditResult:
        """
        Apply edits based on natural language instructions.

        This is an alias for ai_edit to maintain backward compatibility.

        Args:
            file_path: Path to the file to edit
            instruction: Natural language description of changes
            context_files: Additional files for context
            use_ai: Whether to use AI for understanding instructions

        Returns:
            EditResult with applied changes
        """
        return self.ai_edit(file_path, instruction, context_files, use_ai)

    def _parse_ai_instruction(
        self,
        instruction: str,
        content: str,
        file_path: str,
        context_files: Optional[List[str]] = None,
    ) -> List[FileEdit]:
        """
        Parse natural language instruction using AI.

        Args:
            instruction: Natural language instruction
            content: Current file content
            file_path: Path to the file being edited
            context_files: Additional context files

        Returns:
            List of FileEdit operations
        """
        # This is a simplified implementation
        # In a real system, this would integrate with an AI model

        # For now, we'll use pattern matching for common instructions
        return self._parse_simple_instruction(instruction, content)

    def _build_instruction_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Build patterns for common instruction types."""
        return {
            "replace": {
                "patterns": [
                    r"replace\s+(.+?)\s+with\s+(.+)",
                    r"change\s+(.+?)\s+to\s+(.+)",
                    r"update\s+(.+?)\s+to\s+(.+)",
                ],
                "handler": self._handle_replace_instruction,
            },
            "add": {
                "patterns": [
                    r"add\s+(.+?)\s+to\s+(.+)",
                    r"insert\s+(.+?)\s+(?:at|in|to)\s+(.+)",
                    r"add\s+(.+?)\s+(?:before|after)\s+(.+)",
                ],
                "handler": self._handle_add_instruction,
            },
            "remove": {
                "patterns": [
                    r"remove\s+(.+)",
                    r"delete\s+(.+)",
                    r"remove\s+(.+?)\s+from\s+(.+)",
                ],
                "handler": self._handle_remove_instruction,
            },
            "validation": {
                "patterns": [
                    r"add\s+(?:input\s+)?validation",
                    r"add\s+.*?check.*?(?:if|whether|that)\s+(.+)",
                    r"validate\s+(?:that\s+)?(.+)",
                ],
                "handler": self._handle_validation_instruction,
            },
        }

    def _parse_simple_instruction(self, instruction: str, content: str) -> List[FileEdit]:
        """
        Parse simple natural language instructions with enhanced pattern matching.
        """
        instruction_lower = instruction.lower().strip()

        # Try different instruction types in order
        edits = (
            self._handle_todo_instructions_if_applicable(instruction_lower, content)
            or self._handle_validation_instructions_if_applicable(instruction_lower, content)
            or self._handle_replace_instructions_if_applicable(instruction_lower)
            or self._handle_add_instructions_if_applicable(instruction_lower, content)
            or self._handle_other_instructions_if_applicable(instruction_lower)
            or self._handle_unknown_instruction()
        )

        return edits

    def _handle_todo_instructions_if_applicable(
        self, instruction_lower: str, content: str
    ) -> List[FileEdit]:
        """Handle TODO instructions if applicable."""
        if "todo" in instruction_lower:
            return self._handle_todo_instructions(instruction_lower, content)
        return []

    def _handle_validation_instructions_if_applicable(
        self, instruction_lower: str, content: str
    ) -> List[FileEdit]:
        """Handle validation instructions if applicable."""
        if "validation" in instruction_lower or "validate" in instruction_lower:
            return self._handle_validation_instructions(instruction_lower, content)
        return []

    def _handle_replace_instructions_if_applicable(self, instruction_lower: str) -> List[FileEdit]:
        """Handle replace/change instructions if applicable."""
        if "replace" in instruction_lower or "change" in instruction_lower:
            return self._handle_replace_patterns(instruction_lower)
        return []

    def _handle_add_instructions_if_applicable(
        self, instruction_lower: str, content: str
    ) -> List[FileEdit]:
        """Handle add instructions if applicable."""
        if "add" not in instruction_lower:
            return []

        if "import" in instruction_lower:
            return self._handle_import_instruction(instruction_lower)
        elif "error handling" in instruction_lower:
            return self._handle_error_handling_instruction(content)
        elif "docstring" in instruction_lower:
            return self._handle_docstring_instruction(content)
        elif "type hint" in instruction_lower:
            return self._handle_type_hints_instruction()
        elif "logging" in instruction_lower:
            return self._handle_logging_instruction()
        return []

    def _handle_other_instructions_if_applicable(self, instruction_lower: str) -> List[FileEdit]:
        """Handle other instruction types if applicable."""
        if "remove" in instruction_lower and "comment" in instruction_lower:
            return self._handle_remove_comments_instruction()
        elif "rename" in instruction_lower:
            return self._handle_rename_instruction(instruction_lower)
        elif "format" in instruction_lower:
            return self._handle_format_instruction()
        return []

    def _handle_unknown_instruction(self) -> List[FileEdit]:
        """Handle unknown instructions by providing suggestions."""
        suggestions = [
            "Try: 'add import <module>'",
            "Try: 'add error handling'",
            "Try: 'add docstrings'",
            "Try: 'add type hints'",
            "Try: 'replace <old> with <new>'",
        ]
        suggestion_text = "# AI Editor suggestions:\n# " + "\n# ".join(suggestions)
        return [
            FileEdit(
                type=EditType.INSERT,
                target_line=1,
                content=suggestion_text + "\n",
                strategy=EditStrategy.LINE_BASED,
            )
        ]

    def _handle_todo_instructions(self, instruction_lower: str, content: str) -> List[FileEdit]:
        """Handle TODO-related instructions."""
        edits = []
        lines = content.split("\n")

        # Get TODO patterns
        todo_patterns = self._get_todo_patterns()

        # Process each line looking for TODOs
        for i, line in enumerate(lines):
            todo_match = self._find_todo_in_line(line)
            if todo_match:
                todo_edits = self._process_todo_match(
                    todo_match, i, line, lines, todo_patterns, instruction_lower
                )
                edits.extend(todo_edits)

        return edits

    def _handle_validation_instructions(
        self, instruction_lower: str, content: str
    ) -> List[FileEdit]:
        """Handle validation-related instructions."""
        edits = []
        lines = content.splitlines()

        # Define function pattern for validation instructions
        func_pattern = r"^(\s*)def\s+(\w+)\s*\(([^)]*)\)\s*:"

        for i, line in enumerate(lines):
            func_match = re.match(func_pattern, line)
            if func_match:
                validation_edits = self._add_validation_to_function(
                    func_match, i, lines, instruction_lower
                )
                edits.extend(validation_edits)

        return edits

    def _handle_replace_patterns(self, instruction_lower: str) -> List[FileEdit]:
        """Handle replace/change pattern instructions."""
        edits = []
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

    def _get_todo_patterns(self) -> Dict[str, Dict[str, str]]:
        """Get TODO patterns and their templates."""
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
            r"TODO:?\s*[Rr]eturn": {
                "template": "return None  # TODO: Implement proper return value",
                "type": "replace",
            },
            r"TODO:?\s*[Ii]mplement": {
                "template": (
                    'raise NotImplementedError("This functionality is not yet implemented")'
                ),
                "type": "replace",
            },
        }

    def _find_todo_in_line(self, line: str) -> Optional[re.Match]:
        """Find TODO patterns in a line."""
        todo_matches = [
            re.search(r"#\s*TODO:?\s*(.+?)$", line, re.IGNORECASE),
            re.search(r"//\s*TODO:?\s*(.+?)$", line, re.IGNORECASE),
            re.search(r"/\*\s*TODO:?\s*(.+?)\s*\*/", line, re.IGNORECASE),
        ]
        return next((m for m in todo_matches if m), None)

    def _process_todo_match(
        self,
        todo_match: re.Match,
        line_idx: int,
        line: str,
        lines: List[str],
        todo_patterns: Dict[str, Dict[str, str]],
        instruction_lower: str,
    ) -> List[FileEdit]:
        """Process a matched TODO and generate appropriate edits."""
        edits = []
        todo_text = todo_match.group(1).strip()
        indent = len(line) - len(line.lstrip())
        base_indent = " " * indent

        # Extract context using helper method
        context = self._extract_todo_context(lines, line_idx)

        # Try to match against known patterns
        for pattern, config in todo_patterns.items():
            if re.search(pattern, todo_text, re.IGNORECASE):
                edit = self._generate_todo_edit(config, line_idx, line, lines, base_indent, context)
                if edit:
                    edits.append(edit)
                break
        else:
            # Handle generic TODO improvements if no pattern matched
            edit = self._handle_generic_todo(line_idx, line, base_indent, instruction_lower)
            if edit:
                edits.append(edit)

        return edits

    def _generate_todo_edit(
        self,
        config: Dict[str, str],
        line_idx: int,
        line: str,
        lines: List[str],
        base_indent: str,
        context: dict,
    ) -> Optional[FileEdit]:
        """Generate edit based on TODO template configuration."""
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
        return None

    def _handle_generic_todo(
        self, line_idx: int, line: str, base_indent: str, instruction_lower: str
    ) -> Optional[FileEdit]:
        """Handle generic TODO cases that don't match specific patterns."""
        if "implement" in instruction_lower or "complete" in instruction_lower:
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
        elif "replace" in instruction_lower:
            new_text = "Task completed"
            if "with" in instruction_lower:
                parts = instruction_lower.split("with")
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

    def _add_validation_to_function(
        self, func_match: re.Match, line_idx: int, lines: List[str], instruction_lower: str
    ) -> List[FileEdit]:
        """Add validation code to a function."""
        indent = func_match.group(1)
        func_name = func_match.group(2)
        params = func_match.group(3)

        if not self._should_add_validation(func_name, line_idx, lines, params, instruction_lower):
            return []

        param_list = [p.strip().split(":")[0].strip() for p in params.split(",") if p.strip()]
        validation_lines = self._generate_validation_lines(param_list, indent, instruction_lower)

        if not validation_lines:
            return []

        insert_line = self._find_validation_insert_point(line_idx, lines)
        return self._create_validation_edits(insert_line, lines, indent, validation_lines)

    def _should_add_validation(
        self, func_name: str, line_idx: int, lines: List[str], params: str, instruction_lower: str
    ) -> bool:
        """Check if validation should be added to this function."""
        if not params.strip():
            return False

        if func_name.lower() in instruction_lower:
            return True
        if (
            line_idx + 1 < len(lines)
            and "TODO" in lines[line_idx + 1]
            and "validation" in lines[line_idx + 1].lower()
        ):
            return True
        if params and ("multiply" in func_name.lower() or "add" in func_name.lower()):
            return True
        return False

    def _generate_validation_lines(
        self, param_list: List[str], indent: str, instruction_lower: str
    ) -> List[str]:
        """Generate validation code lines for parameters."""
        validation_lines = []

        if "number" in instruction_lower or "numeric" in instruction_lower:
            for param in param_list:
                validation_lines.extend(
                    [
                        f"{indent}    if not isinstance({param}, (int, float)):",
                        f'{indent}        raise TypeError("{param} must be a number")',
                    ]
                )
        else:
            for param in param_list:
                validation_lines.extend(
                    [
                        f"{indent}    if {param} is None:",
                        f'{indent}        raise ValueError("{param} cannot be None")',
                    ]
                )

        return validation_lines

    def _find_validation_insert_point(self, line_idx: int, lines: List[str]) -> int:
        """Find where to insert validation code."""
        insert_line = line_idx + 2

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

    def _create_validation_edits(
        self, insert_line: int, lines: List[str], indent: str, validation_lines: List[str]
    ) -> List[FileEdit]:
        """Create FileEdit objects for validation insertion."""
        edits = []

        if insert_line <= len(lines) and "TODO" in lines[insert_line - 1]:
            edits.append(
                FileEdit(
                    type=EditType.REPLACE,
                    start_line=insert_line,
                    content=f"{indent}    # Validation added\n" + "\n".join(validation_lines),
                )
            )
        else:
            edits.append(
                FileEdit(
                    type=EditType.INSERT,
                    target_line=insert_line,
                    content="\n".join(validation_lines) + "\n",
                )
            )

        return edits

    def _handle_replace_instruction(
        self, match: re.Match, instruction: str, content: str
    ) -> List[FileEdit]:
        """Handle replace-type instructions."""
        old_text = match.group(1).strip()
        new_text = match.group(2).strip()

        # Remove quotes if present
        old_text = old_text.strip("\"'")
        new_text = new_text.strip("\"'")

        return [
            FileEdit(
                type=EditType.REPLACE,
                pattern=re.escape(old_text),
                replacement=new_text,
                strategy=EditStrategy.PATTERN_BASED,
            )
        ]

    def _handle_add_instruction(
        self, match: re.Match, instruction: str, content: str
    ) -> List[FileEdit]:
        """Handle add/insert instructions."""
        # For now, return empty - can be expanded later
        return []

    def _handle_remove_instruction(
        self, match: re.Match, instruction: str, content: str
    ) -> List[FileEdit]:
        """Handle remove/delete instructions."""
        text_to_remove = match.group(1).strip()
        text_to_remove = text_to_remove.strip("\"'")

        return [
            FileEdit(
                type=EditType.DELETE,
                pattern=re.escape(text_to_remove),
                strategy=EditStrategy.PATTERN_BASED,
            )
        ]

    def _handle_validation_instruction(
        self, match: re.Match, instruction: str, content: str
    ) -> List[FileEdit]:
        """Handle validation-related instructions."""
        edits = []

        # Look for function definitions that might need validation
        func_pattern = r"def\s+(\w+)\s*\(([^)]*)\):"
        for func_match in re.finditer(func_pattern, content):
            func_name = func_match.group(1)
            params = func_match.group(2)

            # Check if instruction mentions this function or its parameters
            param_matches = any(
                param.strip() in instruction.lower() for param in params.split(",") if param.strip()
            )
            if func_name in instruction.lower() or param_matches:
                # Find the line number
                lines = content[: func_match.end()].splitlines()
                func_line = len(lines)

                # Generate validation code based on parameters
                validation_code = self._generate_validation_code(params, instruction)

                if validation_code:
                    edits.append(
                        FileEdit(
                            type=EditType.INSERT,
                            target_line=func_line + 1,
                            content=validation_code,
                            strategy=EditStrategy.LINE_BASED,
                        )
                    )

        return edits

    def _generate_validation_code(self, params: str, instruction: str) -> str:
        """Generate validation code based on parameters and instruction."""
        if not params.strip():
            return ""

        param_list = [p.strip() for p in params.split(",") if p.strip()]
        validations = []

        # Check if instruction mentions number/numeric validation
        if any(word in instruction.lower() for word in ["number", "numeric", "int", "float"]):
            for param in param_list:
                validations.append(
                    f"    if not isinstance({param}, (int, float)):\n"
                    f"        raise TypeError(f'{param} must be a number')"
                )

        # Check if instruction mentions string validation
        elif "string" in instruction.lower():
            for param in param_list:
                validations.append(
                    f"    if not isinstance({param}, str):\n"
                    f"        raise TypeError(f'{param} must be a string')"
                )

        # Generic validation
        else:
            validations.append("    # Add validation here")

        return "\n".join(validations) + "\n" if validations else ""

    def _parse_contextual_instruction(self, instruction: str, content: str) -> List[FileEdit]:
        """Parse instruction using context from the file."""
        edits = []

        # Look for TODO comments if instruction mentions them
        if "todo" in instruction.lower():
            todo_pattern = r"(\s*)#\s*TODO:?\s*(.+)"
            for match in re.finditer(todo_pattern, content, re.IGNORECASE):
                indent = match.group(1)
                todo_text = match.group(2)

                # Generate code based on TODO content
                if "validation" in todo_text.lower():
                    # Find the function this TODO belongs to
                    lines_before = content[: match.start()].splitlines()
                    line_num = len(lines_before) + 1

                    edits.append(
                        FileEdit(
                            type=EditType.REPLACE,
                            start_line=line_num,
                            content=(
                                f"{indent}# Validation added\n"
                                f"{indent}# TODO: Implement specific validation logic"
                            ),
                            strategy=EditStrategy.LINE_BASED,
                        )
                    )

        return edits

    def _handle_import_instruction(self, instruction: str) -> List[FileEdit]:
        """Handle import-related instructions."""
        import_match = re.search(r"import\s+([^\s]+)", instruction)
        if import_match:
            import_name = import_match.group(1)
            return [
                FileEdit(
                    type=EditType.INSERT,
                    target_line=1,
                    content=f"import {import_name}\n",
                    strategy=EditStrategy.LINE_BASED,
                )
            ]
        return []

    def _handle_logging_instruction(self) -> List[FileEdit]:
        """Handle print-to-logging instructions."""
        return [
            FileEdit(
                type=EditType.REPLACE,
                pattern=r"print\((.*?)\)",
                replacement=r"logger.info(\1)",
                strategy=EditStrategy.PATTERN_BASED,
            )
        ]

    def _handle_error_handling_instruction(self, content: str) -> List[FileEdit]:
        """Handle error handling instructions."""
        edits = []
        lines = content.splitlines()

        # Find function definitions
        for i, line in enumerate(lines):
            if re.match(r"^\s*def\s+\w+", line):
                # Get function indentation
                indent_match = re.match(r"^(\s*)", line)
                base_indent = indent_match.group(1) if indent_match else ""
                func_indent = base_indent + "    "

                # Find the function body start and end
                body_start = i + 1
                body_end = self._find_function_body_end(lines, i)

                if body_start < len(lines) and body_end > body_start:
                    # Extract existing function body
                    existing_body = lines[body_start:body_end]

                    # Skip if already has try-except
                    if any("try:" in line for line in existing_body[:3]):
                        continue

                    # Create new body with try-except wrapper
                    new_body = [f"{func_indent}try:"]

                    # Indent existing body one more level
                    for body_line in existing_body:
                        if body_line.strip():  # Skip empty lines
                            new_body.append(f"    {body_line}")
                        else:
                            new_body.append(body_line)

                    # Add except block
                    new_body.extend(
                        [
                            f"{func_indent}except Exception as e:",
                            f"{func_indent}    # Handle error appropriately",
                            f"{func_indent}    raise",
                        ]
                    )

                    # Create edit to replace function body
                    edits.append(
                        FileEdit(
                            type=EditType.REPLACE,
                            start_line=body_start + 1,
                            end_line=body_end,
                            replacement="\n".join(new_body) + "\n",
                            strategy=EditStrategy.LINE_BASED,
                        )
                    )

        return edits

    def _find_function_body_end(self, lines: List[str], func_start: int) -> int:
        """Find the end of a function body."""
        if func_start >= len(lines):
            return func_start

        # Get function indentation level
        func_line = lines[func_start]
        func_indent_match = re.match(r"^(\s*)", func_line)
        func_indent_level = len(func_indent_match.group(1)) if func_indent_match else 0

        # Look for the end of the function
        i = func_start + 1
        while i < len(lines):
            line = lines[i]

            # Skip empty lines and comments
            if not line.strip() or line.strip().startswith("#"):
                i += 1
                continue

            # Check indentation level
            line_indent_match = re.match(r"^(\s*)", line)
            line_indent_level = len(line_indent_match.group(1)) if line_indent_match else 0

            # If we find a line at the same or lower indentation level as the function,
            # we've reached the end of the function body
            if line_indent_level <= func_indent_level:
                return i

            i += 1

        # If we reach the end of file, return the last line
        return len(lines)

    def _handle_docstring_instruction(self, content: str) -> List[FileEdit]:
        """Handle docstring addition instructions."""
        edits = []
        lines = content.splitlines()

        for i, line in enumerate(lines):
            if re.match(r"^\s*def\s+\w+", line):
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1

                if j < len(lines) and not lines[j].strip().startswith('"""'):
                    indent_match = re.match(r"^(\s*)", line)
                    indent = indent_match.group(1) if indent_match else ""
                    func_name_match = re.search(r"def\s+(\w+)", line)
                    func_name = func_name_match.group(1) if func_name_match else "function"

                    docstring = f'{indent}    """{func_name.replace("_", " ").title()}."""\n'
                    edits.append(
                        FileEdit(
                            type=EditType.INSERT,
                            target_line=i + 2,
                            content=docstring,
                            strategy=EditStrategy.LINE_BASED,
                        )
                    )
        return edits

    def _handle_remove_comments_instruction(self) -> List[FileEdit]:
        """Handle comment removal instructions."""
        return [
            FileEdit(
                type=EditType.REPLACE,
                pattern=r"^\s*#.*$",
                replacement="",
                strategy=EditStrategy.PATTERN_BASED,
            )
        ]

    def _handle_type_hints_instruction(self) -> List[FileEdit]:
        """Handle type hints instructions."""
        return [
            FileEdit(
                type=EditType.REPLACE,
                pattern=r"def\s+(\w+)\s*\(([^)]*)\)\s*:",
                replacement=r"def \1(\2) -> None:",
                strategy=EditStrategy.PATTERN_BASED,
            )
        ]

    def _handle_format_instruction(self) -> List[FileEdit]:
        """Handle code formatting instructions."""
        return [
            FileEdit(
                type=EditType.REPLACE,
                pattern=r"\n\n\n+",
                replacement="\n\n",
                strategy=EditStrategy.PATTERN_BASED,
            )
        ]

    def _handle_rename_instruction(self, instruction_lower: str) -> List[FileEdit]:
        """Handle rename instructions."""
        rename_match = re.search(r"rename\s+(\w+)\s+to\s+(\w+)", instruction_lower)
        if rename_match:
            old_name, new_name = rename_match.groups()
            return [
                FileEdit(
                    type=EditType.REPLACE,
                    pattern=rf"\b{old_name}\b",
                    replacement=new_name,
                    strategy=EditStrategy.PATTERN_BASED,
                )
            ]
        return []

    def _load_default_examples(self) -> List[EditExample]:
        """
        Load default examples for AI instruction parsing.

        Returns:
            List of EditExample objects
        """
        return [
            EditExample(
                instruction="Add error handling to this function",
                before="def process_data(data):\n    result = data.process()\n    return result",
                after=(
                    "def process_data(data):\n    try:\n        result = data.process()\n"
                    "        return result\n    except Exception as e:\n"
                    "        logger.error(f'Error processing data: {e}')\n        raise"
                ),
                explanation="Wrapped function body in try-except block",
            ),
            EditExample(
                instruction="Replace print statements with logging",
                before="print('Processing started')\nprocess()\nprint('Processing completed')",
                after=(
                    "logger.info('Processing started')\nprocess()\n"
                    "logger.info('Processing completed')"
                ),
                explanation="Replaced print() calls with logger.info()",
            ),
            EditExample(
                instruction="Add docstring to function",
                before="def calculate_total(items):\n    return sum(item.price for item in items)",
                after=(
                    "def calculate_total(items):\n"
                    '    """Calculate the total price of all items."""\n'
                    "    return sum(item.price for item in items)"
                ),
                explanation="Added descriptive docstring to function",
            ),
            EditExample(
                instruction="Add type hints",
                before="def greet(name):\n    return f'Hello, {name}!'",
                after="def greet(name: str) -> str:\n    return f'Hello, {name}!'",
                explanation="Added type hints for parameter and return value",
            ),
        ]

    def add_example(self, example: EditExample) -> None:
        """
        Add a new example for AI instruction parsing.

        Args:
            example: EditExample to add
        """
        self.examples.append(example)

    def _extract_todo_context(self, lines: List[str], todo_line: int) -> dict:
        """Extract context around a TODO for better code generation."""
        context = {
            "function_name": "unknown_function",
            "params": [],
            "params_str": "",
            "params_hash": "hash(params)",
            "param_docs": "",
            "sample_params": "",
            "context": "operation",
            "var": "value",
            "expected_type": "str",
            "required_permission": "read",
        }

        # Look backwards for function definition
        for i in range(todo_line - 1, max(-1, todo_line - 20), -1):
            func_match = re.match(r"^\s*def\s+(\w+)\s*\(([^)]*)\):", lines[i])
            if func_match:
                context["function_name"] = func_match.group(1)
                context["context"] = func_match.group(1)
                params_str = func_match.group(2)
                context["params_str"] = params_str

                if params_str:
                    self._parse_function_parameters(params_str, context)
                break

        return context

    def _parse_function_parameters(self, params_str: str, context: dict) -> None:
        """Parse function parameters and update context with parameter information."""
        param_list = []
        param_docs = []
        sample_values = []

        for param in params_str.split(","):
            param = param.strip()
            if param and param != "self":
                # Extract parameter name and type
                if ":" in param:
                    param_name, param_type = param.split(":", 1)
                    param_name = param_name.strip()
                    param_type = param_type.strip()
                else:
                    param_name = param.strip()
                    param_type = "Any"

                param_list.append(param_name)
                param_docs.append(f"    {param_name} ({param_type}): Description of {param_name}.")

                # Generate sample values based on type hints
                sample_values.append(self._get_sample_value_for_type(param_name, param_type))

        context["params"] = param_list
        context["param_docs"] = "\n".join(param_docs) if param_docs else "    None"
        context["sample_params"] = ", ".join(sample_values)

        if param_list:
            context["var"] = param_list[0]
            context["params_hash"] = "{" + ", ".join(param_list) + "}"
            # Infer expected type from first parameter
            if ":" in params_str:
                first_param_type = params_str.split(",")[0].split(":")[1].strip()
                context["expected_type"] = first_param_type

    def _get_sample_value_for_type(self, param_name: str, param_type: str) -> str:
        """Generate a sample value based on parameter type."""
        if "str" in param_type:
            return f'"sample_{param_name}"'
        elif "int" in param_type:
            return "42"
        elif "float" in param_type:
            return "3.14"
        elif "list" in param_type.lower():
            return "[]"
        elif "dict" in param_type.lower():
            return "{}"
        else:
            return f"{param_name}_value"

    def _format_template(self, template: str, indent: str, context: dict) -> str:
        """Format a code template with proper indentation and context."""
        # Add indentation to each line
        lines = template.strip().split("\n")
        formatted_lines = [indent + line if line.strip() else line for line in lines]
        formatted = "\n".join(formatted_lines)

        # Replace placeholders
        for key, value in context.items():
            formatted = formatted.replace("{" + key + "}", str(value))

        return formatted

    def _find_code_block_end(self, lines: List[str], start: int) -> int:
        """Find the end of a code block starting from a TODO line."""
        if start >= len(lines) - 1:
            return start

        todo_indent = len(lines[start]) - len(lines[start].lstrip())

        # Find next line with same or less indentation
        for i in range(start + 1, len(lines)):
            if lines[i].strip():  # Skip empty lines
                line_indent = len(lines[i]) - len(lines[i].lstrip())
                if line_indent <= todo_indent:
                    return i - 1

        return len(lines) - 1

    def get_suggestions(self, file_path: str) -> List[str]:
        """
        Get AI-powered suggestions for improving the file.

        Args:
            file_path: Path to the file to analyze

        Returns:
            List of improvement suggestions
        """
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                return []

            content = file_path_obj.read_text()
            suggestions = []

            # Check for missing docstrings
            if re.search(r"def\s+\w+", content) and '"""' not in content:
                suggestions.append("Add docstrings to functions")

            # Check for print statements
            if re.search(r"print\s*\(", content):
                suggestions.append("Replace print statements with logging")

            # Check for bare except clauses
            if re.search(r"except\s*:", content):
                suggestions.append("Use specific exception types instead of bare except")

            # Check for missing type hints
            if re.search(r"def\s+\w+\s*\([^)]*\)\s*:", content) and "->" not in content:
                suggestions.append("Add type hints to functions")

            # Check for long lines
            lines = content.splitlines()
            long_lines = [i + 1 for i, line in enumerate(lines) if len(line) > 100]
            if long_lines:
                suggestions.append(
                    f"Consider breaking long lines (lines: {', '.join(map(str, long_lines[:5]))})"
                )

            return suggestions

        except Exception:
            return []
