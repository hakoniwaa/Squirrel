#!/usr/bin/env python3
"""
Base AI Enhancement Module - Abstract base class for all AI enhancers
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Literal, Optional, Tuple

from ...core import ConfigurationManager
from ..openai_service import OpenAIService
from ..processors import ResponseProcessor

logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """Exception raised when AI service encounters an error"""


class BaseEnhancer(ABC):
    """Abstract base class for all AI enhancers"""

    def __init__(self, config_manager: ConfigurationManager):
        self.config_manager = config_manager
        self.enabled = config_manager.config.is_ai_enabled()
        self.ai_service: Optional[OpenAIService] = None
        self.processor: Optional[ResponseProcessor] = None

        if self.enabled:
            try:
                self.ai_service = OpenAIService(config_manager)
                self.processor = ResponseProcessor()
                logger.info(f"{self.__class__.__name__} initialized with AI service enabled")
            except Exception as e:
                logger.warning(
                    f"Failed to initialize AI service for {self.__class__.__name__}: {e}"
                )
                self.enabled = False
                self.ai_service = None
                self.processor = None
        else:
            self.ai_service = None
            self.processor = None
            logger.info(f"{self.__class__.__name__} initialized with AI service disabled")

    def is_enabled(self) -> bool:
        """Check if AI enhancement is enabled"""
        return self.enabled

    def get_status(self) -> Dict[str, Any]:
        """Get AI enhancement status"""
        return {
            "enabled": self.enabled,
            "service_available": self.ai_service is not None,
            "processor_available": self.processor is not None,
            "enhancer_type": self.__class__.__name__,
            "config": self.config_manager.config.get_ai_limits() if self.enabled else None,
        }

    def _ensure_ai_available(self) -> bool:
        """Ensure AI service is available, return False if not"""
        if not self.enabled or not self.ai_service:
            logger.debug(f"AI service not available for {self.__class__.__name__}")
            return False
        return True

    def _safe_ai_call(self, operation_name: str) -> Any:
        """Decorator-like context for safe AI operations"""

        class SafeAIContext:
            def __init__(self, enhancer: "BaseEnhancer", operation: str):
                self.enhancer = enhancer
                self.operation = operation

            def __enter__(self) -> "SafeAIContext":
                if not self.enhancer._ensure_ai_available():
                    raise AIServiceError(f"AI service not available for {self.operation}")
                return self

            def __exit__(
                self,
                exc_type: type[BaseException] | None,
                exc_val: BaseException | None,
                exc_tb: Any,
            ) -> Literal[False]:
                if exc_type and isinstance(exc_val, Exception):
                    logger.warning(f"AI operation '{self.operation}' failed: {exc_val}")
                    return False  # Re-raise the exception
                return False

        return SafeAIContext(self, operation_name)

    # Common helper methods for parsing AI responses
    def _extract_list_from_response(self, ai_response: str, keywords: List[str]) -> List[str]:
        """Extract a list of items from AI response based on keywords"""
        lines = ai_response.split("\n")
        items = []

        for line in lines:
            line = line.strip()
            if any(keyword.lower() in line.lower() for keyword in keywords):
                # Remove common prefixes
                for prefix in ["- ", "* ", "• ", "1. ", "2. ", "3. ", "4. ", "5. "]:
                    if line.startswith(prefix):
                        line = line[len(prefix) :].strip()
                        break

                if line and len(line) < 200:  # Reasonable length
                    items.append(line)

        return items[:5]  # Limit to 5 items

    def _extract_score_from_response(self, ai_response: str, default: float = 5.0) -> float:
        """Extract a numeric score from AI response"""
        import re

        lines = ai_response.split("\n")
        for line in lines:
            if "score" in line.lower():
                numbers = re.findall(r"\d+(?:\.\d+)?", line)
                if numbers:
                    score = float(numbers[0])
                    return min(max(score, 0.0), 10.0)  # Clamp between 0-10

        return default

    def _extract_key_value_from_response(self, ai_response: str, key: str) -> str:
        """Extract value for a specific key from AI response"""
        lines = ai_response.split("\n")
        for line in lines:
            if key.lower() in line.lower() and ":" in line:
                value = line.split(":", 1)[1].strip()
                if value and "not available" not in value.lower():
                    return value

        # Return empty string instead of "not available" message
        return ""

    def _fallback_enhancement(
        self, original_data: Any, message: str = "AI enhancement unavailable"
    ) -> Dict[str, Any]:
        """Provide fallback when AI enhancement fails"""
        if isinstance(original_data, dict):
            fallback = original_data.copy()
            fallback["ai_fallback"] = {"message": message, "timestamp": "N/A"}
            return fallback
        return {"ai_fallback": {"message": message, "timestamp": "N/A"}}

    @abstractmethod
    async def get_enhancement_capabilities(self) -> List[str]:
        """Return list of enhancement capabilities this enhancer provides"""

    # Abstract methods that concrete enhancers should implement
    async def enhance_analysis(
        self, basic_analysis: Dict[str, Any], code: str, language: str, file_path: str = ""
    ) -> Dict[str, Any]:
        """Enhance basic analysis with AI insights"""
        return self._fallback_enhancement(basic_analysis, "Enhancement not implemented")

    async def enhance_code_smells(
        self, basic_smells: List[Dict[str, Any]], code: str, language: str, file_path: str = ""
    ) -> Dict[str, Any]:
        """Enhance code smell detection with AI insights"""
        return {"smells": basic_smells, "ai_fallback": "Enhancement not implemented"}

    async def enhance_security_analysis(
        self, basic_security: Dict[str, Any], code: str, language: str, file_path: str = ""
    ) -> Dict[str, Any]:
        """Enhance security analysis with AI insights"""
        return self._fallback_enhancement(basic_security, "Enhancement not implemented")

    async def enhance_search(
        self, query: str, basic_results: List[Dict[str, Any]], search_context: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Enhance search with AI insights"""
        return basic_results, None

    async def enhance_advanced_search(
        self,
        query: str,
        results: List[Dict[str, Any]],
        search_type: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Enhance advanced search with AI insights"""
        return {"enhanced_results": results, "ai_fallback": "Enhancement not implemented"}

    async def suggest_related_searches(self, query: str, context: str = "") -> List[str]:
        """Suggest related searches"""
        return []

    async def enhance_context_understanding(
        self, context_summary: Dict[str, Any], workspace_path: str
    ) -> Dict[str, Any]:
        """Enhance context understanding"""
        return {"ai_fallback": "Enhancement not implemented"}

    async def enhance_file_relationships(
        self, basic_relationships: Dict[str, Any], file_path: str, file_content: str, language: str
    ) -> Dict[str, Any]:
        """Enhance file relationship detection"""
        return self._fallback_enhancement(basic_relationships, "Enhancement not implemented")

    async def enhance_scaffold_output(
        self, scaffold_result: Dict[str, Any], scaffold_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance scaffolding output"""
        return self._fallback_enhancement(scaffold_result, "Enhancement not implemented")

    async def enhance_documentation_generation(
        self, basic_docs: str, code: str, language: str, doc_type: str = "comprehensive"
    ) -> str:
        """Enhance documentation generation"""
        return basic_docs

    async def enhance_dependency_analysis(
        self, basic_deps: Dict[str, Any], project_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance dependency analysis"""
        return self._fallback_enhancement(basic_deps, "Enhancement not implemented")

    async def analyze_security_vulnerabilities(
        self, dependencies: List[Dict[str, Any]], severity_threshold: str = "medium"
    ) -> Dict[str, Any]:
        """Analyze security vulnerabilities"""
        return {"vulnerabilities": [], "message": "Enhancement not implemented"}

    async def enhance_search_results(
        self, query: str, results: List[Dict[str, Any]], context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Enhance search results"""
        return results

    async def analyze_system_health(
        self, system_metrics: Dict[str, Any], historical_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze system health"""
        return {"ai_fallback": "Enhancement not implemented"}
