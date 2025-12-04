"""
Batch indexing operations for the context manager
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...security.path_security import PathSecurityManager
from .file_indexer import FileIndexer

logger = logging.getLogger(__name__)


class BatchIndexer:
    """Handle batch file indexing operations"""

    def __init__(self, workspace_root: Path, config_manager: Any) -> None:
        self.workspace_root = workspace_root
        self.config_manager = config_manager
        self.path_security = PathSecurityManager(workspace_root)
        self.file_indexer = FileIndexer(workspace_root, config_manager)

        # Batch processing settings - handle different config manager types
        if hasattr(config_manager, "config") and hasattr(config_manager.config, "storage"):
            # ConfigurationManager case
            self.batch_size = getattr(config_manager.config.storage, "batch_size", 10)
            self.max_concurrent = getattr(
                config_manager.config.storage, "max_concurrent_indexing", 3
            )
        else:
            # ServerConfig case or fallback
            self.batch_size = 10
            self.max_concurrent = 3

    async def batch_index_files(
        self, file_patterns: Optional[List[str]] = None, force_reindex: bool = False
    ) -> Dict[str, Any]:
        """Batch index multiple files"""
        if file_patterns is None:
            file_patterns = self._get_default_patterns()

        max_files = self._get_max_files_to_index()
        start_time = asyncio.get_event_loop().time()

        files_to_index, skipped_count = await self._collect_files_to_index(file_patterns, max_files)
        logger.info("Found %d files to index (skipped %d)", len(files_to_index), skipped_count)

        indexed_count, error_count = await self._process_batches(
            files_to_index, force_reindex, start_time
        )

        elapsed_time = asyncio.get_event_loop().time() - start_time

        return {
            "indexed_count": indexed_count,
            "error_count": error_count,
            "skipped_count": skipped_count,
            "total_found": len(files_to_index),
            "max_files": max_files,
            "completed": len(files_to_index) < max_files,
            "elapsed_time": elapsed_time,
            "indexing_rate": indexed_count / elapsed_time if elapsed_time > 0 else 0,
        }

    def _get_max_files_to_index(self) -> int:
        if hasattr(self.config_manager, "limits"):
            value = getattr(self.config_manager.limits, "max_files_to_index", 1000)
            return int(value) if isinstance(value, int) or isinstance(value, float) else 1000
        elif hasattr(self.config_manager, "config") and hasattr(
            self.config_manager.config, "storage"
        ):
            value = getattr(self.config_manager.config.storage, "max_files_to_index", 1000)
            return int(value) if isinstance(value, int) or isinstance(value, float) else 1000
        else:
            return 1000

    async def _collect_files_to_index(
        self, file_patterns: List[str], max_files: int
    ) -> tuple[List[Path], int]:
        files_to_index: List[Path] = []
        skipped_count = 0
        for pattern in file_patterns:
            for file_path in self.path_security.get_safe_file_iterator(pattern):
                if len(files_to_index) >= max_files:
                    logger.warning("Reached maximum file limit (%d)", max_files)
                    break
                if await self.file_indexer.should_index_file(file_path):
                    files_to_index.append(file_path)
                else:
                    skipped_count += 1
            if len(files_to_index) >= max_files:
                break
        return files_to_index, skipped_count

    async def _process_batches(
        self, files_to_index: List[Path], force_reindex: bool, start_time: float
    ) -> tuple[int, int]:
        indexed_count = 0
        error_count = 0
        semaphore = asyncio.Semaphore(self.max_concurrent)
        for i in range(0, len(files_to_index), self.batch_size):
            batch = files_to_index[i : i + self.batch_size]
            tasks = [
                self._index_file_with_semaphore(semaphore, file_path, force_reindex)
                for file_path in batch
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    error_count += 1
                    logger.error("Batch indexing error: %s", result)
                elif result:
                    indexed_count += 1
                else:
                    error_count += 1
            if indexed_count % 20 == 0 and indexed_count > 0:
                elapsed = asyncio.get_event_loop().time() - start_time
                rate = indexed_count / elapsed if elapsed > 0 else 0
                logger.info(
                    "Indexed %d/%d files (%.1f files/sec)",
                    indexed_count,
                    len(files_to_index),
                    rate,
                )
        return indexed_count, error_count

    async def _index_file_with_semaphore(
        self, semaphore: asyncio.Semaphore, file_path: Path, force_reindex: bool
    ) -> bool:
        """Index a single file with semaphore for concurrency control"""
        async with semaphore:
            try:
                # Check if already indexed (unless forcing reindex)
                if not force_reindex and await self._is_file_already_indexed(file_path):
                    logger.debug("File already indexed, skipping: %s", file_path)
                    return True

                return await self.file_indexer.index_single_file(file_path)

            except Exception as e:  # pylint: disable=broad-except
                # Catching all exceptions to ensure batch continues; log and return False
                logger.error("Error indexing %s: %s", file_path, e)
                return False

    async def _is_file_already_indexed(self, file_path: Path) -> bool:
        """Check if a file is already indexed and up-to-date"""
        try:
            doc_id = self.file_indexer._generate_document_id(file_path)

            # Try to retrieve the vector to see if it exists
            vector_data = await self.config_manager.vector_store.get_vector(doc_id)
            if not vector_data:
                return False

            # Check if the file has been modified since indexing
            file_info = self.file_indexer.file_manager.get_file_info(file_path)
            indexed_time = vector_data.get("metadata", {}).get("index_timestamp")

            if indexed_time and file_info["modified"] > indexed_time:
                logger.debug("File modified since indexing: %s", file_path)
                return False

            return True

        except Exception as e:  # pylint: disable=broad-except
            # Catching all exceptions to avoid breaking batch logic; log and return False
            logger.debug("Error checking if file is indexed %s: %s", file_path, e)
            return False

    def _get_default_patterns(self) -> List[str]:
        """Get default file patterns for indexing"""
        return [
            "*.py",
            "*.js",
            "*.ts",
            "*.jsx",
            "*.tsx",
            "*.md",
            "*.txt",
            "*.json",
            "*.yaml",
            "*.yml",
            "*.html",
            "*.css",
            "*.xml",
            "*.sql",
        ]

    async def reindex_modified_files(self) -> Dict[str, Any]:
        """Reindex only files that have been modified since last indexing"""
        logger.info("Starting reindex of modified files...")

        all_vectors = await self._get_all_vectors()
        if isinstance(all_vectors, dict) and "error" in all_vectors:
            return all_vectors

        modified_files, missing_files = await self._collect_modified_and_missing_files(all_vectors)
        await self._remove_missing_files_from_index(missing_files)
        reindex_count, error_count = await self._reindex_files(modified_files)

        return {
            "reindexed_count": reindex_count,
            "removed_count": len(missing_files),
            "error_count": error_count,
            "total_modified": len(modified_files),
            "total_missing": len(missing_files),
        }

    async def _get_all_vectors(self) -> Any:
        try:
            return await self.config_manager.vector_store.list_all_vectors()
        except Exception as e:  # pylint: disable=broad-except
            # Catching all exceptions to ensure error is reported in return value
            logger.error("Failed to get list of indexed files: %s", e)
            return []

    async def _collect_modified_and_missing_files(
        self, all_vectors: list[dict[str, Any]]
    ) -> tuple[list[Path], list[str]]:
        modified_files: list[Path] = []
        missing_files: list[str] = []
        for vector_info in all_vectors:
            metadata = vector_info.get("metadata", {})
            file_path = metadata.get("file_path")
            if not file_path:
                continue
            full_path = self.workspace_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
                continue
            try:
                file_info = self.file_indexer.file_manager.get_file_info(full_path)
                indexed_time = metadata.get("index_timestamp")
                if not indexed_time or file_info["modified"] > indexed_time:
                    modified_files.append(full_path)
            except Exception as e:  # pylint: disable=broad-except
                # Catching all exceptions to ensure all files are considered; log and add file
                logger.debug("Error checking modification time for %s: %s", file_path, e)
                modified_files.append(full_path)
        return modified_files, missing_files

    async def _remove_missing_files_from_index(self, missing_files: List[str]) -> None:
        for missing_file in missing_files:
            try:
                await self.file_indexer.remove_file_index(Path(missing_file))
                logger.debug("Removed missing file from index: %s", missing_file)
            except Exception as e:  # pylint: disable=broad-except
                # Catching all exceptions to ensure batch continues; log error
                logger.error("Failed to remove missing file from index %s: %s", missing_file, e)

    async def _reindex_files(self, modified_files: List[Path]) -> tuple[int, int]:
        reindex_count = 0
        error_count = 0
        if modified_files:
            logger.info("Reindexing %d modified files...", len(modified_files))
            semaphore = asyncio.Semaphore(self.max_concurrent)
            tasks = [
                self._index_file_with_semaphore(semaphore, file_path, force_reindex=True)
                for file_path in modified_files
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    error_count += 1
                    logger.error("Batch reindexing error: %s", result)
                elif result:
                    reindex_count += 1
                else:
                    error_count += 1
        return reindex_count, error_count

    async def index_directory(self, directory_path: str, recursive: bool = True) -> Dict[str, Any]:
        """Index all files in a specific directory"""
        dir_path = self.workspace_root / directory_path

        if not dir_path.exists() or not dir_path.is_dir():
            return {"error": f"Directory does not exist: {directory_path}"}

        # Collect files in directory
        files_to_index = []
        pattern = "**/*" if recursive else "*"

        for file_path in dir_path.glob(pattern):
            if file_path.is_file() and await self.file_indexer.should_index_file(file_path):
                files_to_index.append(file_path)

        if not files_to_index:
            return {
                "indexed_count": 0,
                "error_count": 0,
                "message": f"No indexable files found in {directory_path}",
            }

        # Process files
        indexed_count = 0
        error_count = 0

        semaphore = asyncio.Semaphore(self.max_concurrent)

        for i in range(0, len(files_to_index), self.batch_size):
            batch = files_to_index[i : i + self.batch_size]

            tasks = [
                self._index_file_with_semaphore(semaphore, file_path, force_reindex=False)
                for file_path in batch
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    error_count += 1
                elif result:
                    indexed_count += 1
                else:
                    error_count += 1

        return {
            "indexed_count": indexed_count,
            "error_count": error_count,
            "total_files": len(files_to_index),
            "directory": directory_path,
        }
