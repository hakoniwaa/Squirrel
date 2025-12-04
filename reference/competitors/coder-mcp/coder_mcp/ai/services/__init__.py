#!/usr/bin/env python3
"""
AI Services Package
Contains modular AI service implementations
"""

# Main service
from .base import OpenAIService

# Specialized services
from .completions import CompletionService
from .embeddings import EmbeddingService

__all__ = [
    # Main service (for backward compatibility)
    "OpenAIService",
    # Specialized services
    "CompletionService",
    "EmbeddingService",
]
