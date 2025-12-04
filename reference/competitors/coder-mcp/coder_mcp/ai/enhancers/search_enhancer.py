#!/usr/bin/env python3
"""
Search AI Enhancement Module - Handles AI enhancement for search and query understanding
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from .base_enhancer import AIServiceError, BaseEnhancer

logger = logging.getLogger(__name__)


class SearchEnhancer(BaseEnhancer):
    """Handles AI enhancement for search and query understanding"""

    async def get_enhancement_capabilities(self) -> List[str]:
        """Return list of enhancement capabilities this enhancer provides"""
        return [
            "query_understanding",
            "result_reranking",
            "semantic_search",
            "search_suggestions",
            "intent_detection",
            "context_expansion",
        ]

    async def enhance_search(
        self, query: str, basic_results: List[Dict[str, Any]], search_context: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Use AI to understand search intent and rerank results"""
        if not self._ensure_ai_available():
            return basic_results, None

        try:
            with self._safe_ai_call("search_enhancement"):
                if self.ai_service is None:
                    return basic_results, None

                enhanced_query_response = await self.ai_service.reason_about_code(
                    f"""Analyze this search query for intent and context:

                    Query: "{query}"
                    Search Context: {search_context or "No additional context"}

                    Provide:
                    1. Query intent analysis
                    2. Key concepts and keywords
                    3. Suggested query refinements
                    4. Ranking criteria for results
                    """,
                    "",  # No code context for search
                )

                # Extract search insights
                search_insights = {
                    "intent": self._extract_search_intent(enhanced_query_response.content),
                    "keywords": self._extract_keywords(enhanced_query_response.content),
                    "refinements": self._extract_refinements(enhanced_query_response.content),
                    "ranking_criteria": self._extract_ranking_criteria(
                        enhanced_query_response.content
                    ),
                }

                # Rerank results based on AI insights
                reranked_results = await self._rerank_results(basic_results, query, search_insights)

                logger.debug(f"Enhanced search for query: {query}")
                return reranked_results, search_insights

        except AIServiceError:
            return basic_results, None
        except Exception as e:
            logger.warning(f"Search enhancement failed: {e}")
            return basic_results, {"ai_fallback": f"Search enhancement error: {str(e)}"}

    async def enhance_advanced_search(
        self,
        query: str,
        results: List[Dict[str, Any]],
        search_type: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Enhance advanced search with AI semantic understanding"""
        if not self._ensure_ai_available():
            return {"enhanced_results": results}

        try:
            with self._safe_ai_call("advanced_search_enhancement"):
                if self.ai_service is None:
                    return {"enhanced_results": results}

                ai_response = await self.ai_service.reason_about_code(
                    f"""Perform advanced search analysis:

                    Query: "{query}"
                    Search Type: {search_type}
                    Context: {context or {}}

                    Analyze:
                    1. Search strategy effectiveness
                    2. Result relevance patterns
                    3. Missing information gaps
                    4. Optimization recommendations
                    """,
                    "",
                )

                enhanced_results = {
                    "enhanced_results": results,
                    "search_analysis": {
                        "strategy_assessment": self._extract_strategy_assessment(
                            ai_response.content
                        ),
                        "relevance_patterns": self._extract_relevance_patterns(ai_response.content),
                        "information_gaps": self._extract_information_gaps(ai_response.content),
                        "optimization_recommendations": self._extract_optimization_recommendations(
                            ai_response.content
                        ),
                    },
                    "query_expansion": self._extract_query_expansion(ai_response.content),
                }

                logger.debug(f"Enhanced advanced search for query: {query}")
                return enhanced_results

        except AIServiceError:
            return {"enhanced_results": results}
        except Exception as e:
            logger.warning(f"Advanced search enhancement failed: {e}")
            return {"enhanced_results": results, "ai_fallback": f"Advanced search error: {str(e)}"}

    async def suggest_related_searches(self, query: str, context: str = "") -> List[str]:
        """Suggest related searches based on query intent"""
        if not self._ensure_ai_available():
            return []

        try:
            with self._safe_ai_call("related_search_suggestions"):
                if self.ai_service is None:
                    return []

                ai_response = await self.ai_service.reason_about_code(
                    f"""Suggest related searches for:

                    Original Query: "{query}"
                    Context: {context}

                    Provide 5 related search queries that would:
                    1. Explore related concepts
                    2. Provide deeper insights
                    3. Offer alternative perspectives
                    4. Help with common follow-up questions
                    """,
                    "",
                )

                suggestions = self._extract_list_from_response(
                    ai_response.content, ["suggest", "related", "search", "query"]
                )

                logger.debug(f"Generated {len(suggestions)} related search suggestions")
                return suggestions

        except AIServiceError:
            return []
        except Exception as e:
            logger.warning(f"Related search suggestions failed: {e}")
            return []

    async def enhance_search_results(
        self, query: str, results: List[Dict[str, Any]], context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Enhance search results with AI insights"""
        if not self._ensure_ai_available():
            return results

        try:
            with self._safe_ai_call("search_results_enhancement"):
                if self.ai_service is None:
                    return results

                ai_response = await self.ai_service.reason_about_code(
                    f"""Enhance search results with metadata and insights:

                    Query: "{query}"
                    Context: {context or {}}
                    Number of results: {len(results)}

                    For each result, provide:
                    1. Relevance score (1-10)
                    2. Key insights or summary
                    3. Relationship to query
                    4. Suggested actions
                    """,
                    "",
                )

                enhanced_results = []
                for i, result in enumerate(results):
                    enhanced_result = result.copy()
                    enhanced_result["ai_enhancement"] = {
                        "relevance_score": self._extract_relevance_score(ai_response.content, i),
                        "insights": self._extract_result_insights(ai_response.content, i),
                        "relationship": self._extract_result_relationship(ai_response.content, i),
                        "suggested_actions": self._extract_suggested_actions(
                            ai_response.content, i
                        ),
                    }
                    enhanced_results.append(enhanced_result)

                logger.debug(f"Enhanced {len(enhanced_results)} search results")
                return enhanced_results

        except AIServiceError:
            return results
        except Exception as e:
            logger.warning(f"Search results enhancement failed: {e}")
            return results

    async def analyze_search_patterns(
        self, search_history: List[Dict[str, Any]], user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze search patterns to provide insights"""
        if not self._ensure_ai_available():
            return {"patterns": [], "insights": []}

        try:
            with self._safe_ai_call("search_pattern_analysis"):
                if self.ai_service is None:
                    return {"patterns": [], "insights": []}

                ai_response = await self.ai_service.reason_about_code(
                    f"""Analyze search patterns and user behavior:

                    Search History: {search_history[-10:]}  # Last 10 searches
                    User Context: {user_context}

                    Identify:
                    1. Common search themes
                    2. Information gaps
                    3. Search strategy patterns
                    4. Optimization opportunities
                    """,
                    "",
                )

                analysis = {
                    "common_themes": self._extract_common_themes(ai_response.content),
                    "information_gaps": self._extract_information_gaps(ai_response.content),
                    "strategy_patterns": self._extract_strategy_patterns(ai_response.content),
                    "optimization_opportunities": self._extract_optimization_opportunities(
                        ai_response.content
                    ),
                }

                logger.debug("Completed search pattern analysis")
                return analysis

        except AIServiceError:
            return {"patterns": [], "insights": []}
        except Exception as e:
            logger.warning(f"Search pattern analysis failed: {e}")
            return {
                "patterns": [],
                "insights": [],
                "ai_fallback": f"Pattern analysis error: {str(e)}",
            }

    # Helper methods for parsing AI responses and reranking
    async def _rerank_results(
        self, results: List[Dict[str, Any]], query: str, insights: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Rerank results based on AI insights"""
        keywords = insights.get("keywords", [])
        intent = insights.get("intent", "").lower()

        def relevance_score(result: Dict[str, Any]) -> float:
            score = 0.0
            content = str(result.get("content", "")).lower()

            # Score based on keywords
            for keyword in keywords:
                if keyword.lower() in content:
                    score += 1.0

            # Score based on intent matching
            if intent and any(word in content for word in intent.split()):
                score += 0.5

            return score

        # Sort by relevance score (descending)
        return sorted(results, key=relevance_score, reverse=True)

    def _extract_search_intent(self, ai_response: str) -> str:
        """Extract search intent from AI response"""
        return self._extract_key_value_from_response(ai_response, "intent") or "Information search"

    def _extract_keywords(self, ai_response: str) -> List[str]:
        """Extract keywords from AI response"""
        return self._extract_list_from_response(ai_response, ["keyword", "key", "important"])

    def _extract_refinements(self, ai_response: str) -> List[str]:
        """Extract query refinements from AI response"""
        return self._extract_list_from_response(
            ai_response, ["refine", "improve", "narrow", "specific"]
        )

    def _extract_ranking_criteria(self, ai_response: str) -> List[str]:
        """Extract ranking criteria from AI response"""
        return self._extract_list_from_response(
            ai_response, ["rank", "criteria", "priority", "important"]
        )

    def _extract_strategy_assessment(self, ai_response: str) -> str:
        """Extract strategy assessment from AI response"""
        return (
            self._extract_key_value_from_response(ai_response, "strategy")
            or "Standard search strategy"
        )

    def _extract_relevance_patterns(self, ai_response: str) -> List[str]:
        """Extract relevance patterns from AI response"""
        return self._extract_list_from_response(
            ai_response, ["relevant", "pattern", "match", "similar"]
        )

    def _extract_information_gaps(self, ai_response: str) -> List[str]:
        """Extract information gaps from AI response"""
        return self._extract_list_from_response(
            ai_response, ["gap", "missing", "incomplete", "need"]
        )

    def _extract_optimization_recommendations(self, ai_response: str) -> List[str]:
        """Extract optimization recommendations from AI response"""
        return self._extract_list_from_response(
            ai_response, ["optimize", "improve", "enhance", "better"]
        )

    def _extract_query_expansion(self, ai_response: str) -> List[str]:
        """Extract query expansion suggestions from AI response"""
        return self._extract_list_from_response(
            ai_response, ["expand", "broaden", "include", "also"]
        )

    def _extract_relevance_score(self, ai_response: str, result_index: int) -> float:
        """Extract relevance score for a specific result"""
        # Simple implementation - could be enhanced with more sophisticated parsing
        base_score = self._extract_score_from_response(ai_response, 5.0)
        # Add some variation based on result index
        return max(1.0, min(10.0, base_score - (result_index * 0.1)))

    def _extract_result_insights(self, ai_response: str, result_index: int) -> str:
        """Extract insights for a specific result"""
        insights = self._extract_list_from_response(
            ai_response, ["insight", "key", "important", "note"]
        )
        if result_index < len(insights):
            return insights[result_index]
        return "General insight available"

    def _extract_result_relationship(self, ai_response: str, result_index: int) -> str:
        """Extract relationship description for a specific result"""
        relationships = self._extract_list_from_response(
            ai_response, ["related", "connected", "similar", "matches"]
        )
        if result_index < len(relationships):
            return relationships[result_index]
        return "Related to query"

    def _extract_suggested_actions(self, ai_response: str, result_index: int) -> List[str]:
        """Extract suggested actions for a specific result"""
        actions = self._extract_list_from_response(ai_response, ["action", "do", "try", "consider"])
        # Return a subset of actions for this result
        start_idx = result_index * 2
        return actions[start_idx : start_idx + 2] if actions else ["Review content"]

    def _extract_common_themes(self, ai_response: str) -> List[str]:
        """Extract common themes from AI response"""
        return self._extract_list_from_response(
            ai_response, ["theme", "common", "frequent", "pattern"]
        )

    def _extract_strategy_patterns(self, ai_response: str) -> List[str]:
        """Extract strategy patterns from AI response"""
        return self._extract_list_from_response(
            ai_response, ["strategy", "approach", "method", "technique"]
        )

    def _extract_optimization_opportunities(self, ai_response: str) -> List[str]:
        """Extract optimization opportunities from AI response"""
        return self._extract_list_from_response(
            ai_response, ["opportunity", "improve", "optimize", "enhance"]
        )
