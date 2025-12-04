#!/usr/bin/env python3
"""
Base data models and types for AI response processing
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


@dataclass
class CodeBlock:
    """Represents an extracted code block"""

    language: str
    code: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    description: Optional[str] = None


class ProcessedResponse(BaseModel):
    """Standardized processed response"""

    content: str
    code_blocks: List[CodeBlock] = Field(default_factory=list)
    structured_data: Optional[Dict[str, Any]] = None
    action_items: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


class CodeChange(BaseModel):
    """Represents a suggested code change"""

    file_path: str
    change_type: str  # add, modify, delete
    original_code: Optional[str] = None
    new_code: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    description: str
    priority: str = "medium"  # low, medium, high, critical


class TestCase(BaseModel):
    """Represents a generated test case"""

    name: str
    description: str
    code: str
    test_type: str  # unit, integration, e2e
    assertions: List[str] = Field(default_factory=list)
    setup_code: Optional[str] = None
    teardown_code: Optional[str] = None
