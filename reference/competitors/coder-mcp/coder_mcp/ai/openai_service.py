#!/usr/bin/env python3
"""
OpenAI Service - Legacy compatibility module
Now imports from modular services package for better maintainability

This module provides backward compatibility while the implementation
has been split into focused modules in the services/ and models/ packages.
"""

# Import from new modular structure
from .models import (  # Core types; Response models; Metrics
    AIResponse,
    CodeAnalysisResult,
    ModelType,
    UsageMetrics,
)
from .services import (  # Main service; Specialized services
    CompletionService,
    EmbeddingService,
    OpenAIService,
)

# Maintain backward compatibility - export everything that was previously available
__all__ = [
    # Core types
    "ModelType",
    # Response models
    "AIResponse",
    "CodeAnalysisResult",
    # Metrics
    "UsageMetrics",
    # Services
    "OpenAIService",
    "CompletionService",
    "EmbeddingService",
]
