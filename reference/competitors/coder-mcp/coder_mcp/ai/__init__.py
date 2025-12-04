#!/usr/bin/env python3
"""
AI Package - Intelligent code analysis and enhancement
Split into focused modules for better maintainability

Major improvements in this version:
- Modular enhancer architecture with single responsibilities
- Enhanced error handling and graceful fallbacks
- Improved caching and performance
- Better separation of concerns
- Factory pattern for enhancer coordination
"""

# Import new modular enhancer structure
from .enhancers import (
    AIServiceError,
    BaseEnhancer,
    CodeEnhancer,
    ContextEnhancer,
    DependencyEnhancer,
    EnhancerOrchestrator,
    GenerationEnhancer,
    SearchEnhancer,
)

# Import from existing modular structure
from .models import AIResponse, CodeAnalysisResult, ModelType, UsageMetrics
from .processors import (
    ChangeExtractor,
    CodeBlock,
    CodeChange,
    CodeExtractor,
    DiffProcessor,
    MarkdownProcessor,
    ProcessedResponse,
    ResponseProcessor,
    SyntaxValidator,
    TestCase,
)
from .prompts import PromptTemplates
from .services import OpenAIService

# Backward compatibility: AIEnhancer is now the orchestrator
AIEnhancer = EnhancerOrchestrator

__all__ = [
    # Core types and models
    "ModelType",
    "AIResponse",
    "CodeAnalysisResult",
    "UsageMetrics",
    # Main services
    "OpenAIService",
    "AIEnhancer",  # Legacy - now points to EnhancerOrchestrator
    # New modular enhancer architecture
    "BaseEnhancer",
    "AIServiceError",
    "CodeEnhancer",
    "SearchEnhancer",
    "ContextEnhancer",
    "DependencyEnhancer",
    "GenerationEnhancer",
    "EnhancerOrchestrator",
    # Processors and utilities
    "ResponseProcessor",
    "CodeBlock",
    "CodeChange",
    "TestCase",
    "ProcessedResponse",
    "CodeExtractor",
    "SyntaxValidator",
    "ChangeExtractor",
    "DiffProcessor",
    "MarkdownProcessor",
    # Prompts and templates
    "PromptTemplates",
]
