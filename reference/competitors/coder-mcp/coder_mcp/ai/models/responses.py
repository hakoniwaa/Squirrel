#!/usr/bin/env python3
"""
Response models for AI services
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .metrics import UsageMetrics


class AIResponse(BaseModel):
    """Standardized AI response format"""

    content: str
    model: str
    usage: Optional[UsageMetrics] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    cached: bool = False


class CodeAnalysisResult(BaseModel):
    """Structured code analysis result"""

    summary: str
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    suggestions: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    security_concerns: List[Dict[str, Any]] = Field(default_factory=list)
    performance_insights: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
