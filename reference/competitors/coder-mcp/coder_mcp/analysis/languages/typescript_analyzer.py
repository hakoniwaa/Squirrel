"""
TypeScript-specific code analyzer
"""

from pathlib import Path
from typing import List

from .javascript_analyzer import JavaScriptAnalyzer


class TypeScriptAnalyzer(JavaScriptAnalyzer):
    """TypeScript-specific code analyzer (extends JavaScript analyzer)"""

    def get_file_extensions(self) -> List[str]:
        """Return supported TypeScript file extensions"""
        return [".ts", ".tsx"]

    def _get_smell_types_for_analysis(self, analysis_type: str) -> List[str]:
        """Get appropriate smell types based on analysis type (TypeScript-specific)"""
        base_smells = super()._get_smell_types_for_analysis(analysis_type)

        # Add TypeScript-specific smells
        ts_smells = ["any_usage", "type_assertions", "non_null_assertions"]

        if analysis_type in ["deep", "security"]:
            base_smells.extend(ts_smells)

        return base_smells


def is_typescript_file(file_path: Path) -> bool:
    """Check if a file is a TypeScript file"""
    return file_path.suffix.lower() in [".ts", ".tsx"]
