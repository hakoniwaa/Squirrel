#!/usr/bin/env python3
"""
Core types and enumerations for AI services
"""

from enum import Enum


class ModelType(str, Enum):
    """Available OpenAI model types"""

    EMBEDDING = "embedding"
    REASONING = "reasoning"
    CODE = "code"
    ANALYSIS = "analysis"
    VISION = "vision"
