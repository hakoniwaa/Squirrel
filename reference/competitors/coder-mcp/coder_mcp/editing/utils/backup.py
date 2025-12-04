"""
Backup utilities for the enhanced file editing system.

This module provides functions for creating, managing, and restoring
file backups during editing operations.
"""

import hashlib
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.types import BackupError, BackupInfo


class BackupManager:
    """Manages file backups for editing operations."""

    def __init__(self, backup_dir: str = ".edit_backups", retention_days: int = 7):
        """
        Initialize the backup manager.

        Args:
            backup_dir: Directory to store backups
            retention_days: Number of days to retain backups
        """
        self.backup_dir = Path(backup_dir)
        self.retention_days = retention_days
        self._dir_created = False

    def _ensure_backup_dir(self) -> None:
        """Ensure the backup directory exists."""
        if not self._dir_created:
            try:
                self.backup_dir.mkdir(parents=True, exist_ok=True)
                self._dir_created = True
            except OSError as e:
                raise BackupError(f"Cannot create backup directory {self.backup_dir}: {e}")

    def create_backup(self, file_path: str, content: Optional[str] = None) -> BackupInfo:
        """
        Create a backup of a file.

        Args:
            file_path: Path to the file to backup
            content: Optional content to backup (if None, reads from file)

        Returns:
            BackupInfo object with backup details

        Raises:
            BackupError: If backup creation fails
        """
        try:
            self._ensure_backup_dir()
            original_path = Path(file_path)

            # Read content if not provided
            if content is None:
                if not original_path.exists():
                    raise BackupError(f"File not found: {file_path}")
                content = original_path.read_text()

            # Generate backup filename
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_name = f"{original_path.stem}_{timestamp}{original_path.suffix}"
            backup_path = self.backup_dir / backup_name

            # Ensure unique backup name
            counter = 1
            while backup_path.exists():
                backup_name = f"{original_path.stem}_{timestamp}_{counter}{original_path.suffix}"
                backup_path = self.backup_dir / backup_name
                counter += 1

            # Write backup
            backup_path.write_text(content)

            # Calculate checksum
            checksum = hashlib.sha256(content.encode()).hexdigest()

            return BackupInfo(
                original_path=str(original_path),
                backup_path=str(backup_path),
                timestamp=time.time(),
                size=len(content.encode()),
                checksum=checksum,
            )

        except Exception as e:
            raise BackupError(f"Failed to create backup: {str(e)}") from e

    def restore_backup(self, backup_info_or_path, target_path: Optional[str] = None) -> None:
        """
        Restore a file from backup.

        Args:
            backup_info_or_path: BackupInfo object or backup file path
            target_path: Optional target path for restored file

        Raises:
            BackupError: If restore fails
        """
        try:
            if isinstance(backup_info_or_path, BackupInfo):
                backup_info = backup_info_or_path
                backup_path = Path(backup_info.backup_path)
                original_path = Path(backup_info.original_path)
            else:
                # Assume it's a backup file path
                backup_path = Path(backup_info_or_path)
                if target_path:
                    original_path = Path(target_path)
                else:
                    # Try to infer original path from backup filename
                    parts = backup_path.stem.split("_")
                    if len(parts) >= 3:
                        original_name = "_".join(parts[:-2]) + backup_path.suffix
                        original_path = Path(original_name)
                    else:
                        raise BackupError("Cannot determine original file path")

            if not backup_path.exists():
                raise BackupError(f"Backup file not found: {backup_path}")

            # Read backup content
            content = backup_path.read_text()

            # Verify checksum if we have backup info
            if isinstance(backup_info_or_path, BackupInfo):
                checksum = hashlib.sha256(content.encode()).hexdigest()
                if checksum != backup_info_or_path.checksum:
                    raise BackupError("Backup file checksum mismatch")

            # Restore file
            original_path.parent.mkdir(parents=True, exist_ok=True)
            original_path.write_text(content)

        except Exception as e:
            raise BackupError(f"Failed to restore backup: {str(e)}") from e

    def list_backups(self, file_path: Optional[str] = None) -> List[BackupInfo]:
        """
        List available backups.

        Args:
            file_path: Optional file path to filter backups

        Returns:
            List of BackupInfo objects
        """
        backups: List[BackupInfo] = []

        # Return empty list if backup directory doesn't exist yet
        if not self.backup_dir.exists():
            return backups

        for backup_file in self.backup_dir.glob("*"):
            if backup_file.is_file():
                backup_info = self._create_backup_info_from_file(backup_file, file_path)
                if backup_info:
                    backups.append(backup_info)

        # Sort by timestamp (newest first)
        backups.sort(key=lambda x: x.timestamp, reverse=True)
        return backups

    def _create_backup_info_from_file(
        self, backup_file: Path, filter_file_path: Optional[str]
    ) -> Optional[BackupInfo]:
        """Create BackupInfo from backup file, applying filters."""
        try:
            # Try to parse the backup filename
            parts = backup_file.stem.split("_")
            if len(parts) < 3:
                return None

            # Extract timestamp
            timestamp_str = f"{parts[-2]}_{parts[-1]}"
            timestamp = time.mktime(time.strptime(timestamp_str, "%Y%m%d_%H%M%S"))

            # Calculate checksum
            content = backup_file.read_text()
            checksum = hashlib.sha256(content.encode()).hexdigest()

            # Reconstruct original filename (just the name part)
            original_name = "_".join(parts[:-2]) + backup_file.suffix

            # Check if this backup should be included based on filter
            if not self._should_include_backup(original_name, filter_file_path):
                return None

            # Determine the correct original path
            original_path = self._determine_original_path(original_name, filter_file_path)

            return BackupInfo(
                original_path=original_path,
                backup_path=str(backup_file),
                timestamp=timestamp,
                size=len(content.encode()),
                checksum=checksum,
            )

        except Exception:
            # Skip invalid backup files
            return None

    def _should_include_backup(self, original_name: str, filter_file_path: Optional[str]) -> bool:
        """Check if a backup should be included based on filter criteria."""
        if filter_file_path is None:
            return True

        file_path_obj = Path(filter_file_path)
        # Check both filename match and if the original_name could be a full path
        return (
            file_path_obj.name == original_name
            or str(file_path_obj) == original_name
            or file_path_obj.name == Path(original_name).name
        )

    def _determine_original_path(self, original_name: str, filter_file_path: Optional[str]) -> str:
        """Determine the correct original path for the backup."""
        if filter_file_path and (
            Path(filter_file_path).name == original_name
            or str(Path(filter_file_path)) == original_name
        ):
            return filter_file_path
        return original_name

    def cleanup_old_backups(
        self, file_path: Optional[str] = None, keep_count: Optional[int] = None
    ) -> int:
        """
        Clean up old backups based on retention policy or keep count.

        Args:
            file_path: Optional file path to filter backups for cleanup
            keep_count: Optional number of backups to keep (overrides retention_days)

        Returns:
            Number of backups cleaned up
        """
        # Return 0 if backup directory doesn't exist yet
        if not self.backup_dir.exists():
            return 0

        if keep_count is not None:
            return self._cleanup_by_count(file_path, keep_count)
        else:
            return self._cleanup_by_age(file_path)

    def _cleanup_by_count(self, file_path: Optional[str], keep_count: int) -> int:
        """Clean up backups by keeping only a specific count."""
        backups = self.list_backups(file_path)
        if len(backups) <= keep_count:
            return 0

        # Sort by timestamp (oldest first for deletion)
        backups.sort(key=lambda x: x.timestamp)
        backups_to_delete = backups[:-keep_count]

        cleaned_count = 0
        for backup in backups_to_delete:
            try:
                Path(backup.backup_path).unlink()
                cleaned_count += 1
            except Exception:
                continue
        return cleaned_count

    def _cleanup_by_age(self, file_path: Optional[str]) -> int:
        """Clean up backups by age."""
        cutoff_time = time.time() - (self.retention_days * 24 * 60 * 60)
        cleaned_count = 0

        for backup_file in self.backup_dir.glob("*"):
            if backup_file.is_file():
                try:
                    if self._should_delete_backup(backup_file, cutoff_time, file_path):
                        backup_file.unlink()
                        cleaned_count += 1
                except Exception:
                    continue
        return cleaned_count

    def _should_delete_backup(
        self, backup_file: Path, cutoff_time: float, file_path: Optional[str]
    ) -> bool:
        """Check if a backup file should be deleted."""
        parts = backup_file.stem.split("_")
        if len(parts) < 3:
            return False

        timestamp_str = f"{parts[-2]}_{parts[-1]}"
        timestamp = time.mktime(time.strptime(timestamp_str, "%Y%m%d_%H%M%S"))

        if timestamp >= cutoff_time:
            return False

        if file_path is None:
            return True

        original_name = "_".join(parts[:-2]) + backup_file.suffix
        return Path(original_name).name == Path(file_path).name

    def get_backup_stats(self) -> Dict[str, Any]:
        """
        Get statistics about backups.

        Returns:
            Dictionary with backup statistics
        """
        backups = self.list_backups()

        if not backups:
            return {
                "total_backups": 0,
                "total_size": 0,
                "oldest_backup": None,
                "newest_backup": None,
                "files_backed_up": 0,
            }

        total_size = sum(backup.size for backup in backups)
        oldest_backup = min(backups, key=lambda x: x.timestamp)
        newest_backup = max(backups, key=lambda x: x.timestamp)
        unique_files = len(set(backup.original_path for backup in backups))

        return {
            "total_backups": len(backups),
            "total_size": total_size,
            "oldest_backup": oldest_backup.timestamp,
            "newest_backup": newest_backup.timestamp,
            "files_backed_up": unique_files,
        }

    def verify_backup(self, backup_info_or_path, original_path: Optional[str] = None) -> bool:
        """
        Verify the integrity of a backup.

        Args:
            backup_info_or_path: BackupInfo object or backup file path
            original_path: Optional original file path for comparison

        Returns:
            True if backup is valid, False otherwise
        """
        try:
            if isinstance(backup_info_or_path, BackupInfo):
                backup_info = backup_info_or_path
                backup_path = Path(backup_info.backup_path)

                if not backup_path.exists():
                    return False

                # Verify checksum
                content = backup_path.read_text()
                checksum = hashlib.sha256(content.encode()).hexdigest()
                return checksum == backup_info.checksum
            else:
                # Backup file path provided
                backup_path = Path(backup_info_or_path)
                if not backup_path.exists():
                    return False

                if original_path:
                    original_file = Path(original_path)
                    if original_file.exists():
                        # Compare content
                        backup_content = backup_path.read_text()
                        original_content = original_file.read_text()
                        return backup_content == original_content

                # Just verify backup exists and is readable
                return True

        except Exception:
            return False


def create_backup(file_path: str, backup_dir: str = ".edit_backups") -> BackupInfo:
    """
    Convenience function to create a backup of a file.

    Args:
        file_path: Path to the file to backup
        backup_dir: Directory to store the backup

    Returns:
        BackupInfo object with backup details
    """
    manager = BackupManager(backup_dir)
    return manager.create_backup(file_path)


def restore_from_backup(backup_info: BackupInfo) -> None:
    """
    Convenience function to restore a file from backup.

    Args:
        backup_info: BackupInfo object with restore details
    """
    manager = BackupManager()
    manager.restore_backup(backup_info)


def cleanup_backups(backup_dir: str = ".edit_backups", retention_days: int = 7) -> int:
    """
    Convenience function to clean up old backups.

    Args:
        backup_dir: Directory containing backups
        retention_days: Number of days to retain backups

    Returns:
        Number of backups cleaned up
    """
    manager = BackupManager(backup_dir, retention_days)
    return manager.cleanup_old_backups()
