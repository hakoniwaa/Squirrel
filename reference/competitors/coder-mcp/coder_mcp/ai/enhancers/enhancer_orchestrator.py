#!/usr/bin/env python3
"""
AI Enhancer Orchestrator - Coordinates and manages all AI enhancement modules
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Type

from ...core import ConfigurationManager
from .base_enhancer import BaseEnhancer
from .code_enhancer import CodeEnhancer
from .context_enhancer import ContextEnhancer
from .dependency_enhancer import DependencyEnhancer
from .generation_enhancer import GenerationEnhancer
from .search_enhancer import SearchEnhancer

logger = logging.getLogger(__name__)


class NoOpEnhancer(BaseEnhancer):
    async def get_enhancement_capabilities(self) -> List[str]:
        return []

    async def enhance_analysis(
        self, basic_analysis: Dict[str, Any], code: str, language: str, file_path: str = ""
    ) -> Dict[str, Any]:
        return basic_analysis

    async def enhance_code_smells(
        self, basic_smells: List[Dict[str, Any]], code: str, language: str, file_path: str = ""
    ) -> Dict[str, Any]:
        return {"smells": basic_smells}

    async def enhance_security_analysis(
        self, basic_security: Dict[str, Any], code: str, language: str, file_path: str = ""
    ) -> Dict[str, Any]:
        return basic_security

    async def enhance_search(
        self, query: str, basic_results: List[Dict[str, Any]], search_context: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        return basic_results, None

    async def enhance_advanced_search(
        self,
        query: str,
        results: List[Dict[str, Any]],
        search_type: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return {"enhanced_results": results}

    async def suggest_related_searches(self, query: str, context: str = "") -> List[str]:
        return []

    async def enhance_context_understanding(
        self, context_summary: Dict[str, Any], workspace_path: str
    ) -> Dict[str, Any]:
        return {}

    async def enhance_file_relationships(
        self, basic_relationships: Dict[str, Any], file_path: str, file_content: str, language: str
    ) -> Dict[str, Any]:
        return basic_relationships

    async def enhance_scaffold_output(
        self, scaffold_result: Dict[str, Any], scaffold_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        return scaffold_result

    async def enhance_documentation_generation(
        self, basic_docs: str, code: str, language: str, doc_type: str = "comprehensive"
    ) -> str:
        return basic_docs

    async def enhance_dependency_analysis(
        self, basic_deps: Dict[str, Any], project_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        return basic_deps

    async def analyze_security_vulnerabilities(
        self, dependencies: List[Dict[str, Any]], severity_threshold: str = "medium"
    ) -> Dict[str, Any]:
        return {"vulnerabilities": []}

    async def enhance_search_results(
        self, query: str, results: List[Dict[str, Any]], context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        return results

    async def analyze_system_health(
        self, system_metrics: Dict[str, Any], historical_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        return {}


class EnhancerOrchestrator:
    """
    Orchestrates and coordinates all AI enhancement modules

    This class provides a unified interface to all AI enhancers while maintaining
    the single responsibility principle. It acts as a factory and coordinator
    for different types of AI enhancements.
    """

    def __init__(self, config_manager: ConfigurationManager):
        self.config_manager = config_manager
        self.enabled = config_manager.config.is_ai_enabled()

        # Initialize all enhancer modules
        self._enhancers: Dict[str, BaseEnhancer] = {}

        if self.enabled:
            try:
                self._initialize_enhancers()
                logger.info("AI Enhancer Orchestrator initialized with all modules")
            except (RuntimeError, ValueError, TypeError, KeyError, AttributeError, OSError) as e:
                logger.warning("Failed to initialize AI enhancers: %s", e)
                self.enabled = False
        else:
            logger.info("AI Enhancement disabled")

    def _initialize_enhancers(self) -> None:
        """Initialize all enhancer modules"""
        enhancer_classes: Dict[str, Type[BaseEnhancer]] = {
            "code": CodeEnhancer,
            "search": SearchEnhancer,
            "context": ContextEnhancer,
            "dependency": DependencyEnhancer,
            "generation": GenerationEnhancer,
        }
        for name, enhancer_class in enhancer_classes.items():
            if enhancer_class is BaseEnhancer:
                logger.warning("Skipping abstract enhancer class: %s", enhancer_class.__name__)
                continue
            try:
                enhancer_instance = enhancer_class(self.config_manager)
                self._enhancers[name] = enhancer_instance
                logger.debug("Initialized %s enhancer", name)
            except (RuntimeError, ValueError, TypeError, KeyError, AttributeError, OSError) as e:
                logger.warning("Failed to initialize %s enhancer: %s", name, e)
                self._enhancers[name] = NoOpEnhancer(self.config_manager)

    def is_enabled(self) -> bool:
        """Check if AI enhancement is enabled"""
        return self.enabled

    async def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all enhancers"""
        status: Dict[str, Any] = {
            "orchestrator_enabled": self.enabled,
            "total_enhancers": len(self._enhancers),
            "enhancer_status": {},
            "capabilities": {},
        }
        for name, enhancer in self._enhancers.items():
            try:
                enhancer_status = enhancer.get_status()
                enhancer_status_dict = status["enhancer_status"]
                if not isinstance(enhancer_status_dict, dict):
                    enhancer_status_dict = {}
                    status["enhancer_status"] = enhancer_status_dict
                enhancer_status_dict[name] = enhancer_status
                if enhancer_status.get("enabled"):
                    capabilities = await enhancer.get_enhancement_capabilities()
                    capabilities_dict = status["capabilities"]
                    if not isinstance(capabilities_dict, dict):
                        capabilities_dict = {}
                        status["capabilities"] = capabilities_dict
                    capabilities_dict[name] = capabilities
            except (RuntimeError, ValueError, TypeError, KeyError, AttributeError, OSError) as e:
                enhancer_status_dict = status["enhancer_status"]
                if not isinstance(enhancer_status_dict, dict):
                    enhancer_status_dict = {}
                    status["enhancer_status"] = enhancer_status_dict
                enhancer_status_dict[name] = {"error": str(e)}
        return status

    def get_enhancer(self, enhancer_type: str) -> Optional[BaseEnhancer]:
        """Get a specific enhancer by type"""
        return self._enhancers.get(enhancer_type)

    async def get_available_capabilities(self) -> Dict[str, List[str]]:
        """Get all available enhancement capabilities across all enhancers"""
        capabilities: Dict[str, List[str]] = {}
        for name, enhancer in self._enhancers.items():
            if enhancer.is_enabled():
                try:
                    caps = await enhancer.get_enhancement_capabilities()
                    capabilities[name] = caps
                except (
                    RuntimeError,
                    ValueError,
                    TypeError,
                    KeyError,
                    AttributeError,
                    OSError,
                ) as e:
                    logger.warning("Failed to get capabilities for %s: %s", name, e)
                    capabilities[name] = []
        return capabilities

    # ============================================================================
    # Code Enhancement Methods
    # ============================================================================

    async def enhance_analysis(
        self, basic_analysis: Dict[str, Any], code: str, language: str, file_path: str = ""
    ) -> Dict[str, Any]:
        """Enhance basic AST analysis with AI insights"""
        if not self.enabled:
            return basic_analysis

        code_enhancer = self.get_enhancer("code")
        if code_enhancer and code_enhancer.is_enabled():
            try:
                return await code_enhancer.enhance_analysis(
                    basic_analysis, code, language, file_path
                )
            except (RuntimeError, ValueError, TypeError, KeyError, AttributeError, OSError) as e:
                logger.warning("Code analysis enhancement failed: %s", e)
            except Exception as e:
                logger.warning("Unexpected error during code analysis enhancement: %s", e)

        return basic_analysis

    async def enhance_code_smells(
        self, basic_smells: List[Dict[str, Any]], code: str, language: str, file_path: str = ""
    ) -> Dict[str, Any]:
        """Enhance code smell detection with AI insights"""
        if not self.enabled:
            return {"smells": basic_smells}

        code_enhancer = self.get_enhancer("code")
        if code_enhancer and code_enhancer.is_enabled():
            try:
                return await code_enhancer.enhance_code_smells(
                    basic_smells, code, language, file_path
                )
            except (RuntimeError, ValueError, TypeError, KeyError, AttributeError, OSError) as e:
                logger.warning("Code smell enhancement failed: %s", e)

        return {"smells": basic_smells}

    async def enhance_security_analysis(
        self, basic_security: Dict[str, Any], code: str, language: str, file_path: str = ""
    ) -> Dict[str, Any]:
        """Enhance security analysis with AI-powered vulnerability detection"""
        if not self.enabled:
            return basic_security

        code_enhancer = self.get_enhancer("code")
        if code_enhancer and code_enhancer.is_enabled():
            try:
                return await code_enhancer.enhance_security_analysis(
                    basic_security, code, language, file_path
                )
            except (RuntimeError, ValueError, TypeError, KeyError, AttributeError, OSError) as e:
                logger.warning("Security analysis enhancement failed: %s", e)

        return basic_security

    # ============================================================================
    # Search Enhancement Methods
    # ============================================================================

    async def enhance_search(
        self, query: str, basic_results: List[Dict[str, Any]], search_context: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Use AI to understand search intent and rerank results"""
        if not self.enabled or not basic_results:
            return basic_results, None

        search_enhancer = self.get_enhancer("search")
        if search_enhancer and search_enhancer.is_enabled():
            try:
                return await search_enhancer.enhance_search(query, basic_results, search_context)
            except (RuntimeError, ValueError, TypeError, KeyError, AttributeError, OSError) as e:
                logger.warning("Search enhancement failed: %s", e)

        return basic_results, None

    async def enhance_advanced_search(
        self,
        query: str,
        results: List[Dict[str, Any]],
        search_type: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Enhance advanced search with AI semantic understanding"""
        if not self.enabled or not results:
            return {"enhanced_results": results}

        search_enhancer = self.get_enhancer("search")
        if search_enhancer and search_enhancer.is_enabled():
            try:
                return await search_enhancer.enhance_advanced_search(
                    query, results, search_type, context
                )
            except (RuntimeError, ValueError, TypeError, KeyError, AttributeError, OSError) as e:
                logger.warning("Advanced search enhancement failed: %s", e)

        return {"enhanced_results": results}

    async def suggest_related_searches(self, query: str, context: str = "") -> List[str]:
        """Suggest related searches based on query intent"""
        if not self.enabled:
            return []

        search_enhancer = self.get_enhancer("search")
        if search_enhancer and search_enhancer.is_enabled():
            try:
                return await search_enhancer.suggest_related_searches(query, context)
            except (RuntimeError, ValueError, TypeError, KeyError, AttributeError, OSError) as e:
                logger.warning("Related search suggestions failed: %s", e)

        return []

    # ============================================================================
    # Context Enhancement Methods
    # ============================================================================

    async def enhance_context_understanding(
        self, context_summary: Dict[str, Any], workspace_path: str
    ) -> Dict[str, Any]:
        """Enhance project context with AI analysis"""
        if not self.enabled:
            return {}

        context_enhancer = self.get_enhancer("context")
        if context_enhancer and context_enhancer.is_enabled():
            try:
                return await context_enhancer.enhance_context_understanding(
                    context_summary, workspace_path
                )
            except (RuntimeError, ValueError, TypeError, KeyError, AttributeError, OSError) as e:
                logger.warning("Context understanding enhancement failed: %s", e)

        return {}

    async def enhance_file_relationships(
        self, basic_relationships: Dict[str, Any], file_path: str, file_content: str, language: str
    ) -> Dict[str, Any]:
        """Enhance file relationship detection with AI semantic understanding"""
        if not self.enabled:
            return basic_relationships

        context_enhancer = self.get_enhancer("context")
        if context_enhancer and context_enhancer.is_enabled():
            try:
                return await context_enhancer.enhance_file_relationships(
                    basic_relationships, file_path, file_content, language
                )
            except (RuntimeError, ValueError, TypeError, KeyError, AttributeError, OSError) as e:
                logger.warning("File relationship enhancement failed: %s", e)

        return basic_relationships

    # ============================================================================
    # Generation Enhancement Methods
    # ============================================================================

    async def enhance_scaffold_output(
        self, scaffold_result: Dict[str, Any], scaffold_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance scaffolding output with AI recommendations"""
        if not self.enabled:
            return scaffold_result

        generation_enhancer = self.get_enhancer("generation")
        if generation_enhancer and generation_enhancer.is_enabled():
            try:
                return await generation_enhancer.enhance_scaffold_output(
                    scaffold_result, scaffold_context
                )
            except (RuntimeError, ValueError, TypeError, KeyError, AttributeError, OSError) as e:
                logger.warning("Scaffold enhancement failed: %s", e)

        return scaffold_result

    async def enhance_documentation_generation(
        self, basic_docs: str, code: str, language: str, doc_type: str = "comprehensive"
    ) -> str:
        """Enhance documentation generation with AI insights"""
        if not self.enabled:
            return basic_docs

        generation_enhancer = self.get_enhancer("generation")
        if generation_enhancer and generation_enhancer.is_enabled():
            try:
                return await generation_enhancer.enhance_documentation_generation(
                    basic_docs, code, language, doc_type
                )
            except (RuntimeError, ValueError, TypeError, KeyError, AttributeError, OSError) as e:
                logger.warning("Documentation enhancement failed: %s", e)

        return basic_docs

    # ============================================================================
    # Dependency Enhancement Methods
    # ============================================================================

    async def enhance_dependency_analysis(
        self, basic_deps: Dict[str, Any], project_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance dependency analysis with AI insights"""
        if not self.enabled:
            return basic_deps

        dependency_enhancer = self.get_enhancer("dependency")
        if dependency_enhancer and dependency_enhancer.is_enabled():
            try:
                return await dependency_enhancer.enhance_dependency_analysis(
                    basic_deps, project_context
                )
            except (RuntimeError, ValueError, TypeError, KeyError, AttributeError, OSError) as e:
                logger.warning("Dependency analysis enhancement failed: %s", e)

        return basic_deps

    async def analyze_security_vulnerabilities(
        self, dependencies: List[Dict[str, Any]], severity_threshold: str = "medium"
    ) -> Dict[str, Any]:
        """Analyze dependencies for security vulnerabilities"""
        if not self.enabled:
            return {"vulnerabilities": [], "message": "AI security analysis unavailable"}

        dependency_enhancer = self.get_enhancer("dependency")
        if dependency_enhancer and dependency_enhancer.is_enabled():
            try:
                return await dependency_enhancer.analyze_security_vulnerabilities(
                    dependencies, severity_threshold
                )
            except (RuntimeError, ValueError, TypeError, KeyError, AttributeError, OSError) as e:
                logger.warning("Security vulnerability analysis failed: %s", e)
                return {"vulnerabilities": [], "message": f"Analysis error: {e}"}

        return {"vulnerabilities": [], "message": "No dependency enhancer available"}

    async def enhance_search_results(
        self, query: str, results: List[Dict[str, Any]], context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Enhance search results with AI insights"""
        if not self.enabled or not results:
            return results

        search_enhancer = self.get_enhancer("search")
        if search_enhancer and search_enhancer.is_enabled():
            try:
                return await search_enhancer.enhance_search_results(query, results, context)
            except (RuntimeError, ValueError, TypeError, KeyError, AttributeError, OSError) as e:
                logger.warning("Search results enhancement failed: %s", e)

        return results

    async def analyze_system_health(
        self, system_metrics: Dict[str, Any], historical_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze system health with AI insights"""
        if not self.enabled:
            return {"ai_fallback": "AI health analysis unavailable"}

        # Try to get insights from different enhancers
        insights = {}

        # Context enhancer for general system insights
        context_enhancer = self.get_enhancer("context")
        if context_enhancer and context_enhancer.is_enabled():
            try:
                context_insights = await context_enhancer.analyze_system_health(
                    system_metrics, historical_data
                )
                insights.update(context_insights)
            except (RuntimeError, ValueError, TypeError, KeyError, AttributeError, OSError) as e:
                logger.warning("Context health analysis failed: %s", e)

        # Search enhancer for search performance insights
        search_enhancer = self.get_enhancer("search")
        if search_enhancer and search_enhancer.is_enabled():
            try:
                search_insights = await search_enhancer.analyze_system_health(
                    system_metrics, historical_data
                )
                if search_insights:
                    insights["search_performance"] = search_insights
            except (RuntimeError, ValueError, TypeError, KeyError, AttributeError, OSError) as e:
                logger.warning("Search health analysis failed: %s", e)

        return insights if insights else {"ai_fallback": "No health analysis available"}

    # ============================================================================
    # Orchestration and Coordination Methods
    # ============================================================================

    async def comprehensive_enhancement(
        self, enhancement_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform comprehensive enhancement across multiple domains"""
        if not self.enabled:
            return {"message": "AI enhancement unavailable"}

        request_type = enhancement_request.get("type", "unknown")
        results = {"type": request_type, "enhancements": {}}

        try:
            # Determine which enhancers to use based on request type
            enhancers_to_use = self._determine_enhancers_for_request(enhancement_request)

            for enhancer_name in enhancers_to_use:
                enhancer = self.get_enhancer(enhancer_name)
                if enhancer and enhancer.is_enabled():
                    try:
                        enhancement_result = await self._apply_enhancer(
                            enhancer, enhancer_name, enhancement_request
                        )
                        results["enhancements"][enhancer_name] = enhancement_result
                    except (
                        RuntimeError,
                        ValueError,
                        TypeError,
                        KeyError,
                        AttributeError,
                        OSError,
                    ) as e:
                        results["enhancements"][enhancer_name] = {"error": str(e)}

            results["success"] = len(results["enhancements"]) > 0

        except (RuntimeError, ValueError, TypeError, KeyError, AttributeError, OSError) as e:
            results["error"] = str(e)
            results["success"] = False

        return results

    def _determine_enhancers_for_request(self, request: Dict[str, Any]) -> List[str]:
        """Determine which enhancers should be used for a given request"""
        request_type = request.get("type", "").lower()

        # Define enhancer mappings for different request types
        enhancer_mappings = {
            "code_analysis": ["code"],
            "security_audit": ["code", "dependency"],
            "search_optimization": ["search"],
            "project_analysis": ["context", "dependency"],
            "comprehensive": ["code", "search", "context", "dependency"],
        }

        return enhancer_mappings.get(request_type, ["code"])

    async def _apply_enhancer(
        self, enhancer: BaseEnhancer, enhancer_name: str, _request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply a specific enhancer to the request"""
        # This is a simplified implementation - in practice, you'd have more sophisticated
        # routing based on the enhancer type and request parameters

        if enhancer_name == "code":
            # Apply code enhancements
            return {
                "status": "Code enhancement applied",
                "capabilities": await enhancer.get_enhancement_capabilities(),
            }
        elif enhancer_name == "search":
            # Apply search enhancements
            return {
                "status": "Search enhancement applied",
                "capabilities": await enhancer.get_enhancement_capabilities(),
            }
        elif enhancer_name == "context":
            # Apply context enhancements
            return {
                "status": "Context enhancement applied",
                "capabilities": await enhancer.get_enhancement_capabilities(),
            }
        elif enhancer_name == "dependency":
            # Apply dependency enhancements
            return {
                "status": "Dependency enhancement applied",
                "capabilities": await enhancer.get_enhancement_capabilities(),
            }
        elif enhancer_name == "generation":
            # Apply generation enhancements
            return {
                "status": "Generation enhancement applied",
                "capabilities": await enhancer.get_enhancement_capabilities(),
            }
        else:
            return {"status": "Unknown enhancer type"}

    async def get_enhancement_recommendations(
        self, project_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get enhancement recommendations from all enhancers"""
        recommendations: Dict[str, List[str]] = {}
        for name, enhancer in self._enhancers.items():
            if enhancer.is_enabled():
                try:
                    recs = await self._get_enhancer_recommendations(enhancer, name, project_context)
                    recommendations[name] = recs
                except (
                    RuntimeError,
                    ValueError,
                    TypeError,
                    KeyError,
                    AttributeError,
                    OSError,
                ) as e:
                    logger.warning("Failed to get recommendations for %s: %s", name, e)
                    recommendations[name] = []
        return recommendations

    async def _get_enhancer_recommendations(
        self, enhancer: BaseEnhancer, _enhancer_name: str, _context: Dict[str, Any]
    ) -> List[str]:
        """Get recommendations from a specific enhancer"""
        # This would call enhancer-specific recommendation methods
        # For now, return the capabilities as placeholder
        try:
            capabilities = await enhancer.get_enhancement_capabilities()
            return [f"Utilize {cap} capabilities" for cap in capabilities[:3]]
        except (RuntimeError, ValueError, TypeError, KeyError, AttributeError, OSError):
            return []

    # ============================================================================
    # Backward Compatibility Methods (for original AIEnhancer interface)
    # ============================================================================

    async def enhance_improvement_roadmap(
        self, basic_roadmap: Dict[str, Any], codebase_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance improvement roadmap with AI strategic insights (backward compatibility)"""
        if not self.enabled:
            return basic_roadmap

        enhanced_roadmap = basic_roadmap.copy()

        # Get insights from different enhancers
        context_enhancer = self.get_enhancer("context")
        dependency_enhancer = self.get_enhancer("dependency")

        if context_enhancer and context_enhancer.is_enabled():
            try:
                # Get architectural insights for roadmap
                context_insights = await context_enhancer.enhance_context_understanding(
                    codebase_summary, codebase_summary.get("workspace_path", "")
                )
                enhanced_roadmap["architectural_recommendations"] = context_insights.get(
                    "development_recommendations", []
                )
            except (RuntimeError, ValueError, TypeError, KeyError, AttributeError, OSError) as e:
                logger.warning("Failed to get architectural insights for roadmap: %s", e)

        if dependency_enhancer and dependency_enhancer.is_enabled():
            try:
                # Get dependency insights for roadmap
                dependency_insights = await dependency_enhancer.enhance_dependency_analysis(
                    codebase_summary.get("dependencies", {}), codebase_summary
                )
                enhanced_roadmap["dependency_recommendations"] = dependency_insights.get(
                    "ai_analysis", {}
                ).get("recommended_additions", [])
            except (RuntimeError, ValueError, TypeError, KeyError, AttributeError, OSError) as e:
                logger.warning("Failed to get dependency insights for roadmap: %s", e)

        return enhanced_roadmap
