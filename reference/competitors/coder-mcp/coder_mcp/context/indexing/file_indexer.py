"""
File indexing operations for the context manager
"""

import hashlib
import logging
from pathlib import Path
from typing import Any, Dict

from ...security.path_security import PathSecurityManager
from ...utils.file_utils import FileManager
from .index_strategies import BasicIndexStrategy, IndexStrategy

logger = logging.getLogger(__name__)


class FileIndexer:
    """Handle single file indexing operations"""

    def __init__(self, workspace_root: Path, config_manager: Any) -> None:
        self.workspace_root = workspace_root
        self.config_manager = config_manager

        # Initialize dependencies
        self.path_security = PathSecurityManager(workspace_root)

        # Handle different config manager types
        if hasattr(config_manager, "limits"):
            # ServerConfig case
            max_file_size = config_manager.limits.max_file_size
        elif hasattr(config_manager, "config") and hasattr(config_manager.config, "storage"):
            # ConfigurationManager case
            max_file_size = config_manager.config.storage.max_file_size
        else:
            # Fallback to default
            max_file_size = 10 * 1024 * 1024  # 10MB default

        self.file_manager = FileManager(max_file_size)

        # Select indexing strategy
        self.strategy = self._select_strategy()

    def _select_strategy(self) -> IndexStrategy:
        """Select appropriate indexing strategy based on configuration"""
        # For now, use basic strategy - can be enhanced later
        return BasicIndexStrategy()

    async def index_single_file(self, file_path: Path) -> bool:
        """Index a single file for vector search"""
        try:
            # Validate path security
            if not await self.should_index_file(file_path):
                return False

            resolved_path = await self._resolve_and_validate_path(file_path)
            if not resolved_path:
                return False

            content = await self.file_manager.safe_read_file(resolved_path)
            processed_content = await self.strategy.process_content(content, resolved_path)

            embedding = await self._create_embedding(processed_content, resolved_path)
            if not embedding:
                return False

            doc_id = self._generate_document_id(resolved_path)
            metadata = await self._prepare_metadata(file_path, resolved_path, content)

            return await self._store_vector(doc_id, embedding, metadata, file_path)

        except (OSError, ValueError) as e:
            logger.error("Error ...: %s", e)
            return False

    async def _resolve_and_validate_path(self, file_path: Path) -> Path | None:
        try:
            if file_path.is_absolute():
                resolved_path = file_path.resolve()
                try:
                    relative_path = resolved_path.relative_to(self.workspace_root.resolve())
                    resolved_path = self.workspace_root / relative_path
                except ValueError:
                    logger.debug("Skipping file outside workspace: %s", file_path)
                    return None
            else:
                resolved_path = self.path_security.resolve_path(str(file_path))
            return resolved_path
        except (OSError, ValueError) as e:
            logger.debug("Failed to resolve path %s: %s", file_path, e)
            return None

    async def _create_embedding(self, processed_content: str, resolved_path: Path) -> Any:
        embedding = await self.config_manager.embedding_provider.create_embedding(processed_content)
        if not embedding:
            logger.warning("Could not create embedding for %s", resolved_path)
            return None
        return embedding

    async def _store_vector(
        self, doc_id: str, embedding: Any, metadata: Dict[str, Any], file_path: Path
    ) -> bool:
        result = await self.config_manager.vector_store.store_vector(doc_id, embedding, metadata)
        success = bool(result)
        if success:
            logger.debug("Successfully indexed file: %s", file_path)
        else:
            logger.warning("Failed to store vector for: %s", file_path)
        return success

    async def should_index_file(self, file_path: Path) -> bool:
        """Determine if a file should be indexed"""
        try:
            # Security check
            if not self.path_security.is_safe_path(file_path):
                logger.debug("Skipping unsafe path: %s", file_path)
                return False

            # Skip binary files
            if self.file_manager.is_binary_file(file_path):
                logger.debug("Skipping binary file: %s", file_path)
                return False

            # Check file size limits
            file_info = self.file_manager.get_file_info(file_path)

            # Handle different config manager types for max_file_size
            if hasattr(self.config_manager, "limits"):
                # ServerConfig case
                max_size = self.config_manager.limits.max_file_size
            elif hasattr(self.config_manager, "config") and hasattr(
                self.config_manager.config, "storage"
            ):
                # ConfigurationManager case
                max_size = self.config_manager.config.storage.max_file_size
            else:
                # Fallback to default
                max_size = 10 * 1024 * 1024  # 10MB default

            if file_info["size"] > max_size:
                logger.debug("Skipping large file (%d bytes): %s", file_info["size"], file_path)
                return False

            # Check if file type is indexable
            file_type = self.file_manager.get_file_type(file_path)

            # Handle different config manager types for indexable_types
            if hasattr(self.config_manager, "config") and hasattr(
                self.config_manager.config, "storage"
            ):
                # ConfigurationManager case
                indexable_types = getattr(
                    self.config_manager.config.storage,
                    "indexable_types",
                    ["text", "python", "javascript", "typescript", "markdown", "json", "yaml"],
                )
            else:
                # ServerConfig case or fallback
                indexable_types = [
                    "text",
                    "python",
                    "javascript",
                    "typescript",
                    "markdown",
                    "json",
                    "yaml",
                ]

            if file_type not in indexable_types:
                logger.debug("Skipping non-indexable file type '%s': %s", file_type, file_path)
                return False

            return True

        except Exception as e:  # pylint: disable=broad-except
            # Catching all exceptions to ensure indexability check does not break batch logic
            logger.error("Error checking if file should be indexed %s: %s", file_path, e)
            return False

    async def _prepare_metadata(
        self, file_path: Path, resolved_path: Path, content: str
    ) -> Dict[str, Any]:
        """Prepare metadata for the indexed file"""
        file_info = self.file_manager.get_file_info(resolved_path)

        # Calculate relative path safely
        try:
            if file_path.is_absolute():
                relative_file_path = str(file_path.relative_to(self.workspace_root.resolve()))
            else:
                relative_file_path = str(file_path)
        except ValueError:
            # If we can't make it relative, use the filename
            relative_file_path = file_path.name

        metadata = {
            "content_preview": content[:1000],  # First 1000 chars for preview
            "file_path": relative_file_path,
            "file_type": self.file_manager.get_file_type(resolved_path),
            "file_size": file_info["size"],
            "modified": file_info["modified"],
            "project": self.workspace_root.name,
            "lines_of_code": len(content.splitlines()),
            "char_count": len(content),
            "index_timestamp": file_info.get("created", file_info["modified"]),
        }

        # Add language-specific metadata
        await self._add_language_metadata(metadata, content, resolved_path)

        return metadata

    async def _add_language_metadata(
        self, metadata: Dict[str, Any], content: str, file_path: Path
    ) -> None:
        """Add language-specific metadata"""
        file_ext = file_path.suffix.lower()

        if file_ext == ".py":
            # Python-specific metadata
            import_count = len(
                [
                    line
                    for line in content.splitlines()
                    if line.strip().startswith(("import ", "from "))
                ]
            )
            class_count = len(
                [line for line in content.splitlines() if line.strip().startswith("class ")]
            )
            func_count = len(
                [line for line in content.splitlines() if line.strip().startswith("def ")]
            )

            metadata.update(
                {
                    "python_imports": import_count,
                    "python_classes": class_count,
                    "python_functions": func_count,
                }
            )

        elif file_ext in [".js", ".ts", ".jsx", ".tsx"]:
            # JavaScript/TypeScript metadata
            import_count = len(
                [line for line in content.splitlines() if "import " in line or "require(" in line]
            )
            func_count = len(
                [line for line in content.splitlines() if "function " in line or "=>" in line]
            )

            metadata.update(
                {
                    "js_imports": import_count,
                    "js_functions": func_count,
                    "is_typescript": file_ext in [".ts", ".tsx"],
                }
            )

        elif file_ext == ".md":
            # Markdown metadata
            lines = content.splitlines()
            heading_count = len([line for line in lines if line.strip().startswith("#")])
            link_count = content.count("[") + content.count("](")

            metadata.update({"markdown_headings": heading_count, "markdown_links": link_count})

    def _generate_document_id(self, file_path: Path) -> str:
        """Generate a unique document ID for the file"""
        # Use the file path relative to workspace root for consistent IDs
        try:
            if file_path.is_absolute():
                relative_path = str(file_path.relative_to(self.workspace_root.resolve()))
            else:
                relative_path = str(file_path)
        except ValueError:
            # If we can't make it relative, use the absolute path
            relative_path = str(file_path)

        # Produce a deterministic hash for the file's relative path
        try:
            digest = hashlib.md5(relative_path.encode("utf-8"), usedforsecurity=False)
        except TypeError:
            digest = hashlib.md5(relative_path.encode("utf-8"))  # nosec B324
        return digest.hexdigest()

    async def update_file_index(self, file_path: Path) -> bool:
        """Update an existing file's index"""
        # For now, re-index the file completely
        # Could be optimized to check if content changed
        result = await self.index_single_file(file_path)
        return bool(result)

    async def remove_file_index(self, file_path: Path) -> bool:
        """Remove a file from the index"""
        try:
            doc_id = self._generate_document_id(file_path)
            success = await self.config_manager.vector_store.delete_vector(doc_id)

            if success:
                logger.debug("Removed index for file: %s", file_path)
            else:
                logger.warning("Failed to remove index for file: %s", file_path)
            return bool(success)
        except Exception as e:
            logger.error("Error removing file index for %s: %s", file_path, e)
            return False

    async def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the file indexing"""
        try:
            vector_stats = await self.config_manager.vector_store.get_stats()

            return {
                "indexed_files": vector_stats.get("total_vectors", 0),
                "index_size": vector_stats.get("index_size", 0),
                "last_updated": vector_stats.get("last_updated"),
                "strategy": type(self.strategy).__name__,
            }

        except Exception as e:  # pylint: disable=broad-except
            # Defensive: catch all exceptions to ensure stats retrieval does not break batch logic
            logger.error("Failed to get index stats: %s", e)
            return {"error": str(e)}
