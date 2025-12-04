"""
Workspace Detector - Handles workspace root detection with robust fallbacks
"""

import logging
from pathlib import Path
from typing import Optional

from .server_config import PROJECT_INDICATORS, SYSTEM_DIRECTORIES

logger = logging.getLogger(__name__)


class WorkspaceDetector:
    """Handles workspace root detection with robust fallbacks"""

    def detect_workspace_root(self) -> Path:
        """Detect workspace root directory with robust fallbacks"""
        # Try environment variable first
        if workspace := self._get_workspace_from_env():
            return workspace

        # Try current working directory
        cwd = Path.cwd().resolve()
        if workspace := self._get_workspace_from_cwd(cwd):
            return workspace

        # Try script directory
        if workspace := self._get_workspace_from_script():
            return workspace

        # Final fallback
        return self._get_fallback_workspace()

    def _get_workspace_from_env(self) -> Optional[Path]:
        """Get workspace from environment variable"""
        import os

        if env_workspace := os.getenv("MCP_WORKSPACE_ROOT"):
            workspace = Path(env_workspace).resolve()
            if workspace.exists() and workspace.is_dir():
                logger.info(f"Using workspace from environment: {workspace}")
                return workspace
        return None

    def _get_workspace_from_cwd(self, cwd: Path) -> Optional[Path]:
        """Get workspace from current working directory"""
        if self._is_safe_directory(cwd):
            workspace = self._find_project_root(cwd)
            if workspace is not None:
                logger.info(f"Detected workspace root: {workspace}")
                return workspace
        return None

    def _get_workspace_from_script(self) -> Optional[Path]:
        """Get workspace from script directory"""
        script_dir = Path(__file__).parent.parent.resolve()
        logger.info(f"CWD unsafe, trying script directory: {script_dir}")

        workspace = self._find_project_root(script_dir)
        if workspace is not None:
            logger.info(f"Using script-relative workspace: {workspace}")
            return workspace

        if self._is_safe_directory(script_dir):
            logger.info(f"Using script directory as workspace: {script_dir}")
            return script_dir
        return None

    def _get_fallback_workspace(self) -> Path:
        """Get fallback workspace (home directory)"""
        home_dir = Path.home()
        logger.warning(f"Using home directory as last resort: {home_dir}")
        return home_dir

    def _is_safe_directory(self, directory: Path) -> bool:
        """Check if directory is safe to use as workspace"""
        return directory not in SYSTEM_DIRECTORIES and not any(
            directory.is_relative_to(sys_dir) for sys_dir in SYSTEM_DIRECTORIES
        )

    def _find_project_root(self, start_path: Path) -> Optional[Path]:
        """Find project root by looking for common project indicators"""
        current = start_path
        while current.parent != current:  # Not at filesystem root
            if any((current / indicator).exists() for indicator in PROJECT_INDICATORS):
                return current
            current = current.parent
        return None
