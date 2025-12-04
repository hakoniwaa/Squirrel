"""
File relationship detection and dependency tracking
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List

from ...security.path_security import PathSecurityManager
from ...utils.file_utils import FileManager

logger = logging.getLogger(__name__)


class FileRelationshipManager:
    """Detect and manage relationships between files"""

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.path_security = PathSecurityManager(workspace_root)
        self.file_manager = FileManager()

    async def get_related_files(
        self, file_path: str, top_k: int = 5, relationship_type: str = "similar_purpose"
    ) -> List[Dict[str, Any]]:
        """Find files related to the given file"""
        try:
            resolved_path = self.path_security.resolve_path(file_path)
            content = await self.file_manager.safe_read_file(resolved_path)

            if relationship_type == "imports":
                results = await self._find_import_related_files(content, file_path, top_k)
            elif relationship_type == "tests":
                results = await self._find_test_related_files(file_path, top_k)
            elif relationship_type == "documentation":
                results = await self._find_documentation_related_files(file_path, top_k)
            else:
                results = []

            return results

        except Exception as e:
            logger.error(f"Failed to find related files for {file_path}: {e}")
            return []

    async def _find_import_related_files(
        self, content: str, file_path: str, top_k: int
    ) -> List[Dict[str, Any]]:
        """Find files related through import statements"""
        results = []

        import_patterns = [
            r'from\s+[\'""]([^"\']+)[\'""]',
            r'import\s+[\'""]([^"\']+)[\'""]',
            r'require\s*\(\s*[\'""]([^"\']+)[\'""]',
        ]

        imported_modules = set()
        for pattern in import_patterns:
            matches = re.findall(pattern, content)
            imported_modules.update(matches)

        for module in imported_modules:
            for ext in [".py", ".js", ".ts", ".jsx", ".tsx"]:
                potential_path = self.workspace_root / f"{module.replace('.', '/')}{ext}"
                if potential_path.exists():
                    results.append(
                        {
                            "path": str(potential_path.relative_to(self.workspace_root)),
                            "score": 0.9,
                            "reason": f"Imported as '{module}'",
                        }
                    )

        return results[:top_k]

    async def _find_test_related_files(self, file_path: str, top_k: int) -> List[Dict[str, Any]]:
        """Find test files related to the given file"""
        results = []
        path_obj = Path(file_path)

        test_patterns = [
            f"test_{path_obj.stem}.py",
            f"{path_obj.stem}_test.py",
            f"{path_obj.stem}.test.js",
            f"{path_obj.stem}.spec.js",
        ]

        test_dirs = ["tests", "test", "__tests__", "spec"]

        for test_dir in test_dirs:
            test_path = self.workspace_root / test_dir
            if test_path.exists():
                for pattern in test_patterns:
                    test_file = test_path / pattern
                    if test_file.exists():
                        results.append(
                            {
                                "path": str(test_file.relative_to(self.workspace_root)),
                                "score": 0.95,
                                "reason": "Corresponding test file",
                            }
                        )

        return results[:top_k]

    async def _find_documentation_related_files(
        self, file_path: str, top_k: int
    ) -> List[Dict[str, Any]]:
        """Find documentation files related to the given file"""
        results = []
        path_obj = Path(file_path)

        readme_patterns = ["README.md", "readme.md", "README.txt"]
        for readme in readme_patterns:
            readme_path = path_obj.parent / readme
            if (self.workspace_root / readme_path).exists():
                results.append(
                    {"path": str(readme_path), "score": 0.8, "reason": "Directory documentation"}
                )

        return results[:top_k]
