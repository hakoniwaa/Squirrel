"""
Base AST visitor for code analysis
"""

import ast
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List


class BaseASTVisitor(ast.NodeVisitor, ABC):
    """Base class for AST-based code analysis visitors"""

    def __init__(self, file_path: Path, workspace_root: Path, smell_types: List[str]):
        self.file_path = file_path
        self.workspace_root = workspace_root
        self.smell_types = smell_types
        self.smells: List[Dict[str, Any]] = []

    @abstractmethod
    def get_smells(self) -> List[Dict[str, Any]]:
        """Get detected code smells"""

    def add_smell(
        self, smell_type: str, line: int, severity: str, description: str, suggestion: str = ""
    ):
        """Add a detected code smell"""
        self.smells.append(
            {
                "type": smell_type,
                "file": str(self.file_path.relative_to(self.workspace_root)),
                "line": line,
                "severity": severity,
                "description": description,
                "suggestion": suggestion,
            }
        )

    def should_check_smell(self, smell_type: str) -> bool:
        """Check if a specific smell type should be detected"""
        return smell_type in self.smell_types
