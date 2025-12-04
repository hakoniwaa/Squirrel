"""
Memory type definitions for project context
"""

import hashlib
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Type


class MemoryCategory(Enum):
    """Categories of memory types"""

    CODE = "code"
    PROJECT = "project"
    USER = "user"
    SYSTEM = "system"
    TEMPORARY = "temporary"


class MemoryType(ABC):
    """Abstract base class for memory types"""

    def __init__(
        self,
        content: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.content = content
        self.tags = tags or []
        self.metadata = metadata or {}
        self.timestamp = datetime.now().isoformat()
        self.id = self._generate_id()

    def _generate_id(self) -> str:
        """Generate a unique ID for this memory"""
        try:
            digest = hashlib.md5(
                f"{self.content}:{self.timestamp}".encode("utf-8"),
                usedforsecurity=False,
            )
        except TypeError:
            digest = hashlib.md5(f"{self.content}:{self.timestamp}".encode("utf-8"))  # nosec B324
        content_hash = digest.hexdigest()
        return f"{self.get_category().value}_{content_hash[:8]}"

    @abstractmethod
    def get_category(self) -> MemoryCategory:
        """Get the category of this memory type"""

    @abstractmethod
    def get_type_name(self) -> str:
        """Get the specific type name"""

    def to_dict(self) -> Dict[str, Any]:
        """Convert memory to dictionary representation"""
        return {
            "id": self.id,
            "type": self.get_type_name(),
            "category": self.get_category().value,
            "content": self.content,
            "tags": self.tags,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryType":
        """Create memory instance from dictionary"""
        # This would be implemented by subclasses
        raise NotImplementedError

    def add_tag(self, tag: str) -> None:
        """Add a tag to this memory"""
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from this memory"""
        if tag in self.tags:
            self.tags.remove(tag)

    def update_metadata(self, key: str, value: Any) -> None:
        """Update metadata for this memory"""
        self.metadata[key] = value

    def matches_query(self, query: str) -> bool:
        """Check if this memory matches a search query"""
        query_lower = query.lower()

        # Search in content
        if query_lower in self.content.lower():
            return True

        # Search in tags
        if any(query_lower in tag.lower() for tag in self.tags):
            return True

        # Search in metadata values
        for value in self.metadata.values():
            if isinstance(value, str) and query_lower in value.lower():
                return True

        return False


class CodeMemory(MemoryType):
    """Memory related to code patterns, functions, or implementation details"""

    def __init__(
        self,
        content: str,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        function_name: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(content, tags, metadata)

        # Code-specific metadata
        if file_path:
            self.metadata["file_path"] = file_path
        if line_number:
            self.metadata["line_number"] = line_number
        if function_name:
            self.metadata["function_name"] = function_name

    def get_category(self) -> MemoryCategory:
        return MemoryCategory.CODE

    def get_type_name(self) -> str:
        return "code_memory"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CodeMemory":
        """Create CodeMemory from dictionary"""
        metadata = data.get("metadata", {})
        return cls(
            content=data["content"],
            file_path=metadata.get("file_path"),
            line_number=metadata.get("line_number"),
            function_name=metadata.get("function_name"),
            tags=data.get("tags", []),
            metadata=metadata,
        )

    def get_file_context(self) -> Dict[str, Any]:
        """Get file context information"""
        return {
            "file_path": self.metadata.get("file_path"),
            "line_number": self.metadata.get("line_number"),
            "function_name": self.metadata.get("function_name"),
        }


class ProjectMemory(MemoryType):
    """Memory related to project structure, decisions, or high-level concepts"""

    def __init__(
        self,
        content: str,
        project_area: Optional[str] = None,
        importance: int = 1,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(content, tags, metadata)

        # Project-specific metadata
        if project_area:
            self.metadata["project_area"] = project_area
        self.metadata["importance"] = importance  # 1-5 scale

    def get_category(self) -> MemoryCategory:
        return MemoryCategory.PROJECT

    def get_type_name(self) -> str:
        return "project_memory"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectMemory":
        """Create ProjectMemory from dictionary"""
        metadata = data.get("metadata", {})
        return cls(
            content=data["content"],
            project_area=metadata.get("project_area"),
            importance=metadata.get("importance", 1),
            tags=data.get("tags", []),
            metadata=metadata,
        )

    def set_importance(self, importance: int) -> None:
        """Set the importance level (1-5)"""
        self.metadata["importance"] = max(1, min(5, importance))

    def get_importance(self) -> int:
        """Get the importance level"""
        return int(self.metadata.get("importance", 1))


class UserMemory(MemoryType):
    """Memory from user interactions, preferences, or manual notes"""

    def __init__(
        self,
        content: str,
        user_intent: Optional[str] = None,
        context: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(content, tags, metadata)

        # User-specific metadata
        if user_intent:
            self.metadata["user_intent"] = user_intent
        if context:
            self.metadata["context"] = context

    def get_category(self) -> MemoryCategory:
        return MemoryCategory.USER

    def get_type_name(self) -> str:
        return "user_memory"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserMemory":
        """Create UserMemory from dictionary"""
        metadata = data.get("metadata", {})
        return cls(
            content=data["content"],
            user_intent=metadata.get("user_intent"),
            context=metadata.get("context"),
            tags=data.get("tags", []),
            metadata=metadata,
        )

    def get_user_context(self) -> Dict[str, Any]:
        """Get user context information"""
        return {
            "user_intent": self.metadata.get("user_intent"),
            "context": self.metadata.get("context"),
        }


class SystemMemory(MemoryType):
    """Memory from system operations, performance metrics, or automated insights"""

    def __init__(
        self,
        content: str,
        system_component: Optional[str] = None,
        metric_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(content, tags, metadata)

        # System-specific metadata
        if system_component:
            self.metadata["system_component"] = system_component
        if metric_type:
            self.metadata["metric_type"] = metric_type

    def get_category(self) -> MemoryCategory:
        return MemoryCategory.SYSTEM

    def get_type_name(self) -> str:
        return "system_memory"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SystemMemory":
        """Create SystemMemory from dictionary"""
        metadata = data.get("metadata", {})
        return cls(
            content=data["content"],
            system_component=metadata.get("system_component"),
            metric_type=metadata.get("metric_type"),
            tags=data.get("tags", []),
            metadata=metadata,
        )


class TemporaryMemory(MemoryType):
    """Short-term memory for current session or temporary insights"""

    def __init__(
        self,
        content: str,
        ttl_hours: int = 24,
        session_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(content, tags, metadata)

        # Temporary-specific metadata
        self.metadata["ttl_hours"] = ttl_hours
        if session_id:
            self.metadata["session_id"] = session_id

        # Calculate expiration time
        expiry_time = datetime.now() + timedelta(hours=ttl_hours)
        self.metadata["expires_at"] = expiry_time.isoformat()

    def get_category(self) -> MemoryCategory:
        return MemoryCategory.TEMPORARY

    def get_type_name(self) -> str:
        return "temporary_memory"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemporaryMemory":
        """Create TemporaryMemory from dictionary"""
        metadata = data.get("metadata", {})
        return cls(
            content=data["content"],
            ttl_hours=metadata.get("ttl_hours", 24),
            session_id=metadata.get("session_id"),
            tags=data.get("tags", []),
            metadata=metadata,
        )

    def is_expired(self) -> bool:
        """Check if this temporary memory has expired"""
        expiry_str = self.metadata.get("expires_at")
        if not expiry_str:
            return False

        try:
            expiry_time = datetime.fromisoformat(expiry_str)
            return datetime.now() > expiry_time
        except (ValueError, TypeError):
            return True  # If we can't parse the date, consider it expired

    def extend_ttl(self, additional_hours: int) -> None:
        """Extend the time-to-live by additional hours"""
        current_ttl = self.metadata.get("ttl_hours", 24)
        new_ttl = current_ttl + additional_hours
        self.metadata["ttl_hours"] = new_ttl

        # Update expiration time
        expiry_time = datetime.now() + timedelta(hours=new_ttl)
        self.metadata["expires_at"] = expiry_time.isoformat()


# Factory function to create memory instances
def create_memory(memory_type: str, content: str, **kwargs) -> MemoryType:
    """Factory function to create memory instances of the appropriate type"""

    memory_classes: Dict[str, Type[MemoryType]] = {
        "code": CodeMemory,
        "code_memory": CodeMemory,
        "project": ProjectMemory,
        "project_memory": ProjectMemory,
        "user": UserMemory,
        "user_memory": UserMemory,
        "system": SystemMemory,
        "system_memory": SystemMemory,
        "temporary": TemporaryMemory,
        "temporary_memory": TemporaryMemory,
    }

    memory_class = memory_classes.get(memory_type.lower())
    if not memory_class:
        raise ValueError(f"Unknown memory type: {memory_type}")

    return memory_class(content, **kwargs)


# Helper function to deserialize memories
def memory_from_dict(data: Dict[str, Any]) -> MemoryType:
    """Create appropriate memory instance from dictionary data"""
    memory_type = data.get("type", "")

    memory_classes: Dict[str, Type[MemoryType]] = {
        "code_memory": CodeMemory,
        "project_memory": ProjectMemory,
        "user_memory": UserMemory,
        "system_memory": SystemMemory,
        "temporary_memory": TemporaryMemory,
    }

    memory_class = memory_classes.get(memory_type)
    if not memory_class:
        raise ValueError(f"Unknown memory type in data: {memory_type}")

    return memory_class.from_dict(data)
