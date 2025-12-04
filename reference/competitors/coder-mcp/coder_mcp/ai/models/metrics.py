#!/usr/bin/env python3
"""
Usage metrics and cost tracking for AI services
"""

from datetime import datetime
from typing import Dict

from pydantic import BaseModel, Field


class UsageMetrics(BaseModel):
    """Track API usage metrics"""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0.0
    model: str
    timestamp: datetime = Field(default_factory=datetime.now)


class CostCalculator:
    """Calculate costs for API usage"""

    # Cost per 1K tokens (approximate)
    COST_PER_1K_TOKENS = {
        "text-embedding-3-large": {"input": 0.00013, "output": 0.0},
        "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "o1-preview": {"input": 0.015, "output": 0.06},
    }

    @classmethod
    def estimate_cost(cls, model: str, usage: Dict[str, int]) -> float:
        """Estimate API call cost"""
        if model not in cls.COST_PER_1K_TOKENS:
            return 0.0

        costs = cls.COST_PER_1K_TOKENS[model]
        input_cost = (usage.get("prompt_tokens", 0) / 1000) * costs["input"]
        output_cost = (usage.get("completion_tokens", 0) / 1000) * costs["output"]

        return round(input_cost + output_cost, 4)
