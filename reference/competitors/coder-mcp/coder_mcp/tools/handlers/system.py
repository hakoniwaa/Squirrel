#!/usr/bin/env python3
"""
System health and monitoring tool handler
Handles health checks, performance metrics, and advanced search operations
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from mcp.types import Tool

from ...security.exceptions import handle_exceptions
from ...security.validators import validate_dict_input, validate_string_input
from ..base_handler import BaseHandler

logger = logging.getLogger(__name__)


class SystemHandler(BaseHandler):
    """System health and monitoring operations"""

    def _get_historical_metrics(self) -> Optional[Dict[str, Any]]:
        """Get historical metrics for trend analysis"""
        try:
            if (
                self.context_manager
                and hasattr(self.context_manager, "metrics")
                and hasattr(self.context_manager.metrics, "get_historical_data")
            ):
                result = self.context_manager.metrics.get_historical_data()
                return result if isinstance(result, dict) else None
            return None
        except (AttributeError, TypeError, ValueError) as e:
            logger.debug("Failed to get historical metrics: %s", e)
            return None

    def _validate_health_check_args(self, args: Dict[str, Any]) -> Tuple[bool, bool]:
        """Validate and extract health check arguments."""
        validate_dict_input(args, "health_check arguments")
        verbose = args.get("verbose", False)
        test_operations = args.get("test_operations", True)
        return verbose, test_operations

    async def _check_provider_health(self) -> Dict[str, Any]:
        """Check provider health status and basic connectivity."""
        provider_status = {"overall_healthy": False, "providers": {}, "error": None}

        try:
            # Get health status from config manager
            health_status = self.config_manager.health_check()
            provider_status["overall_healthy"] = health_status.get("overall_healthy", False)

            # Provider status with detailed descriptions
            provider_health = health_status.get("providers", {})
            provider_status["providers"] = {
                "📊 Embedding Provider": {
                    "status": provider_health.get("embedding", {}).get("healthy", False),
                    "description": "Vector embedding generation service",
                },
                "🗄️ Vector Store": {
                    "status": provider_health.get("vector_store", {}).get("healthy", False),
                    "description": "Vector similarity search database",
                },
                "💾 Cache Provider": {
                    "status": provider_health.get("cache", {}).get("healthy", False),
                    "description": "Redis caching layer",
                },
                "🔗 Context Manager": {
                    "status": self.context_manager is not None,
                    "description": "Project context management system",
                },
            }

        except (AttributeError, TypeError, ValueError, ConnectionError) as e:
            provider_status["error"] = str(e)
            logger.error("Provider health check failed: %s", e)

        return provider_status

    async def _perform_test_operations(self) -> Dict[str, Any]:
        """Perform read/write test operations."""
        test_results: Dict[str, Any] = {
            "cache_test": False,
            "context_test": False,
            "cache_latency_ms": None,
            "context_latency_ms": None,
            "error": None,
        }

        if not self.context_manager:
            test_results["error"] = "Context manager not available"
            return test_results

        try:
            # Test cache operations
            if (
                hasattr(self.config_manager, "cache_provider")
                and self.config_manager.cache_provider
            ):
                test_key = f"health_check_{int(time.time())}"
                start_time = time.time()

                await self.config_manager.cache_provider.set(test_key, "test_value")
                retrieved = await self.config_manager.cache_provider.get(test_key)
                cache_ok = retrieved == "test_value"
                await self.config_manager.cache_provider.delete(test_key)

                test_results["cache_test"] = cache_ok
                test_results["cache_latency_ms"] = (time.time() - start_time) * 1000

            # Test context loading
            start_time = time.time()
            context = await self.context_manager.load_context()
            context_ok = isinstance(context, dict)
            test_results["context_test"] = context_ok
            test_results["context_latency_ms"] = (time.time() - start_time) * 1000

        except (AttributeError, TypeError, ValueError, ConnectionError, IOError) as e:
            test_results["error"] = str(e)
            logger.error("Test operations failed: %s", e)

        return test_results

    async def _get_ai_health_insights(
        self, provider_status: Dict[str, Any], test_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get AI health analysis and insights."""
        ai_insights: Dict[str, Any] = {}

        if not self.is_ai_enabled():
            return ai_insights

        try:
            # Prepare health data for AI analysis
            comprehensive_health_data = {
                "providers": provider_status.get("providers", {}),
                "overall_healthy": provider_status.get("overall_healthy", False),
                "operational_tests": test_results,
                "timestamp": time.time(),
            }

            # Get historical metrics for trend analysis
            historical_data = self._get_historical_metrics()

            ai_insights = await self.ai_enhancer.analyze_system_health(
                comprehensive_health_data, historical_data
            )

        except (AttributeError, TypeError, ValueError, ConnectionError, IOError) as e:
            # AI fails gracefully
            logger.debug("AI enhancement failed for health check: %s", e)
            ai_insights["error"] = str(e)

        return ai_insights

    async def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system and configuration metrics."""
        metrics: Dict[str, Any] = {"config_summary": {}, "error": None}

        try:
            if self.config_manager:
                config_summary = self.config_manager.get_summary()
                metrics["config_summary"] = config_summary

        except (AttributeError, TypeError, ValueError) as e:
            metrics["error"] = str(e)
            logger.debug("Failed to collect system metrics: %s", e)

        return metrics

    def _format_health_response(
        self,
        provider_status: Dict[str, Any],
        test_results: Optional[Dict[str, Any]],
        ai_insights: Dict[str, Any],
        metrics: Optional[Dict[str, Any]],
        verbose: bool,
    ) -> str:
        """Format health check results into a readable response."""
        result_parts = ["🏥 **System Health Check**\n"]

        # Add each section
        result_parts.extend(self._format_provider_status(provider_status, verbose))
        result_parts.extend(self._format_overall_status(provider_status))
        result_parts.extend(self._format_test_results(test_results, verbose))
        result_parts.extend(self._format_ai_insights(ai_insights))
        result_parts.extend(self._format_config_summary(metrics, verbose))

        return "\n".join(result_parts)

    def _format_provider_status(self, provider_status: Dict[str, Any], verbose: bool) -> List[str]:
        """Format provider status section"""
        result_parts = []
        providers = provider_status.get("providers", {})

        # Display provider status
        for name, info in providers.items():
            healthy = info["status"]
            status_icon = "✅" if healthy else "❌"
            result_parts.append(f"{name}: {status_icon}")

            if verbose:
                result_parts.append(f"   {info['description']}")

        return result_parts

    def _format_overall_status(self, provider_status: Dict[str, Any]) -> List[str]:
        """Format overall system status section"""
        all_healthy = provider_status.get("overall_healthy", False)
        overall_status = "✅ HEALTHY" if all_healthy else "⚠️  DEGRADED"

        return [f"\n**Overall Status:** {overall_status}", self.format_ai_enhancement_status()]

    def _format_test_results(
        self, test_results: Optional[Dict[str, Any]], verbose: bool
    ) -> List[str]:
        """Format test operations results section"""
        if not test_results:
            return []

        result_parts = ["\n**Testing Operations:**"]

        # Cache test results
        if test_results.get("cache_test") is not None:
            cache_status = "✅" if test_results["cache_test"] else "❌"
            result_parts.append(f"Cache Operations: {cache_status}")
            if verbose and test_results.get("cache_latency_ms"):
                result_parts.append(f"   Latency: {test_results['cache_latency_ms']:.2f}ms")
        else:
            result_parts.append("Cache Operations: ❌ (No cache provider)")

        # Context test results
        if test_results.get("context_test") is not None:
            context_status = "✅" if test_results["context_test"] else "❌"
            result_parts.append(f"Context Loading: {context_status}")
            if verbose and test_results.get("context_latency_ms"):
                result_parts.append(f"   Latency: {test_results['context_latency_ms']:.2f}ms")

        return result_parts

    def _format_ai_insights(self, ai_insights: Dict[str, Any]) -> List[str]:
        """Format AI insights section"""
        if not ai_insights or ai_insights.get("error"):
            return []

        result_parts = ["\n## 🤖 AI Health Analysis"]

        # Add each AI insight category
        self._add_ai_trends(result_parts, ai_insights)
        self._add_ai_warnings(result_parts, ai_insights)
        self._add_ai_optimizations(result_parts, ai_insights)
        self._add_ai_predictions(result_parts, ai_insights)
        self._add_ai_priority_actions(result_parts, ai_insights)

        return result_parts

    def _add_ai_trends(self, result_parts: List[str], ai_insights: Dict[str, Any]) -> None:
        """Add AI trends to result"""
        if ai_insights.get("trends"):
            result_parts.append("**Performance Trends:**")
            for trend in ai_insights["trends"][:3]:
                result_parts.append(f"  • {trend}")

    def _add_ai_warnings(self, result_parts: List[str], ai_insights: Dict[str, Any]) -> None:
        """Add AI warnings to result"""
        if ai_insights.get("warnings"):
            result_parts.append("**Potential Issues:**")
            for warning in ai_insights["warnings"][:3]:
                result_parts.append(f"  ⚠️  {warning}")

    def _add_ai_optimizations(self, result_parts: List[str], ai_insights: Dict[str, Any]) -> None:
        """Add AI optimizations to result"""
        if ai_insights.get("optimizations"):
            result_parts.append("**Optimization Suggestions:**")
            for optimization in ai_insights["optimizations"][:3]:
                result_parts.append(f"  💡 {optimization}")

    def _add_ai_predictions(self, result_parts: List[str], ai_insights: Dict[str, Any]) -> None:
        """Add AI predictions to result"""
        if ai_insights.get("predictions"):
            result_parts.append("**Predictive Insights:**")
            for prediction in ai_insights["predictions"][:2]:
                result_parts.append(f"  🔮 {prediction}")

    def _add_ai_priority_actions(
        self, result_parts: List[str], ai_insights: Dict[str, Any]
    ) -> None:
        """Add AI priority actions to result"""
        if ai_insights.get("priority_actions"):
            result_parts.append("**Priority Actions:**")
            for action in ai_insights["priority_actions"][:3]:
                result_parts.append(f"  🎯 {action}")

    def _format_config_summary(self, metrics: Optional[Dict[str, Any]], verbose: bool) -> List[str]:
        """Format configuration summary section"""
        if not verbose or not metrics or not metrics.get("config_summary"):
            return []

        result_parts = ["\n**Configuration Summary:**"]
        for section, details in metrics["config_summary"].items():
            result_parts.append(f"**{section.title()}:** {details}")

        return result_parts

    @staticmethod
    def get_tools() -> List[Tool]:
        """Get system tools"""
        return [
            Tool(
                name="health_check",
                description="Check health status of Redis and other services",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "verbose": {
                            "type": "boolean",
                            "default": False,
                            "description": "Include detailed metrics",
                        },
                        "test_operations": {
                            "type": "boolean",
                            "default": True,
                            "description": "Test read/write operations",
                        },
                    },
                },
            ),
            Tool(
                name="get_metrics",
                description="Get performance metrics and usage analytics",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "metric_type": {
                            "type": "string",
                            "enum": ["performance", "usage", "errors", "all"],
                            "default": "all",
                        },
                        "time_range": {
                            "type": "string",
                            "enum": ["hour", "day", "week", "all"],
                            "default": "day",
                        },
                    },
                },
            ),
            Tool(
                name="advanced_search",
                description="Perform advanced search using vector and text search",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "search_type": {
                            "type": "string",
                            "enum": ["semantic", "fulltext", "pattern", "hybrid"],
                            "default": "hybrid",
                            "description": "Type of search to perform",
                        },
                        "filters": {
                            "type": "object",
                            "properties": {
                                "file_type": {"type": "string"},
                                "max_size": {"type": "integer"},
                                "modified_after": {"type": "string"},
                                "quality_score_min": {"type": "integer"},
                            },
                        },
                    },
                    "required": ["query"],
                },
            ),
        ]

    @handle_exceptions
    async def health_check(self, args: Dict[str, Any]) -> str:
        """
        Check health status of all services.

        Now a clean orchestrator that delegates to focused helper methods.
        """
        try:
            # 1. Validate inputs
            verbose, test_operations = self._validate_health_check_args(args)

            # 2. Run health checks in parallel
            tasks = [
                self._check_provider_health(),
            ]

            if test_operations:
                tasks.append(self._perform_test_operations())

            if verbose:
                tasks.append(self._collect_system_metrics())

            # Execute provider health check and test operations
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 3. Unpack results
            provider_status = (
                results[0] if not isinstance(results[0], Exception) else {"error": str(results[0])}
            )
            test_results = (
                results[1] if len(results) > 1 and not isinstance(results[1], Exception) else None
            )
            metrics = (
                results[2] if len(results) > 2 and not isinstance(results[2], Exception) else None
            )

            # 4. Get AI insights (if enabled and verbose)
            ai_insights: Dict[str, Any] = {}
            if verbose and isinstance(provider_status, dict):
                test_results_dict = test_results if isinstance(test_results, dict) else {}
                ai_insights = await self._get_ai_health_insights(provider_status, test_results_dict)

            # 5. Format and return response
            if isinstance(provider_status, dict):
                response = self._format_health_response(
                    provider_status,
                    test_results if isinstance(test_results, dict) else None,
                    ai_insights,
                    metrics if isinstance(metrics, dict) else None,
                    verbose,
                )
                # 6. Log the operation
                all_healthy = provider_status.get("overall_healthy", False)
            else:
                response = self.format_error("health_check", "Provider health check failed")
                all_healthy = False
            await self.log_tool_usage("health_check", args, all_healthy)

            return response

        except (AttributeError, TypeError, ValueError, ConnectionError, IOError) as e:
            await self.log_tool_usage("health_check", args, False)
            return self.format_error("health_check", str(e))

    @handle_exceptions
    async def get_metrics(self, args: Dict[str, Any]) -> str:
        """Get performance metrics and usage analytics"""
        validate_dict_input(args, "get_metrics arguments")

        metric_type = args.get("metric_type", "all")
        time_range = args.get("time_range", "day")

        try:
            metrics = self._get_metrics_data()
            result_parts = [f"📊 **System Metrics ({time_range})**\n"]

            self._add_performance_metrics(result_parts, metrics, metric_type)
            self._add_usage_analytics(result_parts, metrics, metric_type)
            self._add_error_statistics(result_parts, metrics, metric_type)
            self._add_system_information(result_parts)

            await self.log_tool_usage("get_metrics", args, True)
            return "\n".join(result_parts)

        except (AttributeError, TypeError, ValueError, ConnectionError, IOError) as e:
            await self.log_tool_usage("get_metrics", args, False)
            return self.format_error("get_metrics", str(e))

    def _get_metrics_data(self) -> Dict[str, Any]:
        """Get metrics data from context manager or fallback"""
        if self.context_manager and hasattr(self.context_manager, "metrics"):
            return self.context_manager.metrics.get_snapshot()
        else:
            return {
                "cache_hits": 0,
                "cache_misses": 0,
                "vector_searches": 0,
                "tool_usage": {},
                "uptime": time.time(),
                "last_updated": time.time(),
            }

    def _add_performance_metrics(
        self, result_parts: List[str], metrics: Dict[str, Any], metric_type: str
    ):
        """Add performance metrics section"""
        if metric_type not in ["performance", "all"]:
            return

        result_parts.append("**Performance Metrics:**")
        cache_hits = metrics.get("cache_hits", 0)
        cache_misses = metrics.get("cache_misses", 0)
        total_cache_ops = cache_hits + cache_misses

        result_parts.append(f"  • Cache Hits: {cache_hits:,}")
        result_parts.append(f"  • Cache Misses: {cache_misses:,}")

        if total_cache_ops > 0:
            hit_rate = (cache_hits / total_cache_ops) * 100
            result_parts.append(f"  • Cache Hit Rate: {hit_rate:.1f}%")

        result_parts.append(f"  • Vector Searches: {metrics.get('vector_searches', 0):,}")

        if metrics.get("latencies"):
            latencies = metrics["latencies"]
            avg_latency = sum(latencies) / len(latencies)
            max_latency = max(latencies)
            result_parts.append(f"  • Avg Latency: {avg_latency:.2f}ms")
            result_parts.append(f"  • Max Latency: {max_latency:.2f}ms")

    def _add_usage_analytics(
        self, result_parts: List[str], metrics: Dict[str, Any], metric_type: str
    ):
        """Add usage analytics section"""
        if metric_type not in ["usage", "all"]:
            return

        result_parts.append("\n**Usage Analytics:**")
        tool_usage = metrics.get("tool_usage", {})

        if tool_usage:
            sorted_tools = sorted(tool_usage.items(), key=lambda x: x[1], reverse=True)
            result_parts.append("  Top Tools:")
            for tool, count in sorted_tools[:5]:
                result_parts.append(f"    • {tool}: {count:,} calls")

            if len(sorted_tools) > 5:
                total_other = sum(count for _, count in sorted_tools[5:])
                result_parts.append(f"    • Others: {total_other:,} calls")
        else:
            result_parts.append("  No tool usage data available")

        # Uptime information
        if metrics.get("uptime"):
            uptime_seconds = time.time() - metrics["uptime"]
            uptime_hours = uptime_seconds / 3600
            if uptime_hours < 24:
                result_parts.append(f"  • Uptime: {uptime_hours:.1f} hours")
            else:
                uptime_days = uptime_hours / 24
                result_parts.append(f"  • Uptime: {uptime_days:.1f} days")

    def _add_error_statistics(
        self, result_parts: List[str], metrics: Dict[str, Any], metric_type: str
    ):
        """Add error statistics section"""
        if metric_type not in ["errors", "all"]:
            return

        result_parts.append("\n**Error Statistics:**")
        error_count = metrics.get("error_count", 0)
        last_error = metrics.get("last_error", None)

        result_parts.append(f"  • Total Errors: {error_count:,}")
        if last_error:
            result_parts.append(f"  • Last Error: {last_error}")
        else:
            result_parts.append("  • Last Error: None")

    def _add_system_information(self, result_parts: List[str]):
        """Add system information section"""
        result_parts.append("\n**System Information:**")
        result_parts.append(f"  • Workspace: {self.workspace_root}")
        result_parts.append(f"  • Context Available: {'Yes' if self.context_manager else 'No'}")

    @handle_exceptions
    async def advanced_search(self, args: Dict[str, Any]) -> str:
        """Perform advanced search using vector and text search with AI enhancement"""
        validate_dict_input(args, "advanced_search arguments")

        query = validate_string_input(args.get("query", ""), "query")
        search_type = args.get("search_type", "hybrid")
        filters = args.get("filters", {})

        try:
            if not self.context_manager:
                return self.format_error("advanced_search", "Context manager not available")

            # Step 1: Perform basic search
            results = await self._perform_basic_search(query, search_type)

            if not results:
                return self.format_info("advanced_search", f"No results found for: {query}")

            # Step 2: Apply filters
            results = self._apply_search_filters(results, filters)

            # Step 3: AI enhancement
            enhanced_results, ai_insights = await self._enhance_search_with_ai(
                query, results, search_type
            )

            # Step 4: Format and return results
            formatted_result = self._format_search_results(
                query, search_type, enhanced_results, ai_insights
            )

            await self.log_tool_usage("advanced_search", args, len(enhanced_results) > 0)
            return formatted_result

        except (AttributeError, TypeError, ValueError, ConnectionError, IOError) as e:
            await self.log_tool_usage("advanced_search", args, False)
            return self.format_error("advanced_search", str(e))

    async def _perform_basic_search(self, query: str, search_type: str) -> List[Dict[str, Any]]:
        """Perform the basic search operation based on search type"""
        if search_type == "semantic":
            return await self.context_manager.semantic_search(query=query, top_k=10)
        elif search_type == "fulltext":
            return await self._perform_fulltext_search(query)
        elif search_type == "pattern":
            return await self.context_manager.search_files(
                pattern=query, path=".", file_pattern="*"
            )
        else:  # hybrid
            return await self._perform_hybrid_search(query)

    async def _perform_fulltext_search(self, query: str) -> List[Dict[str, Any]]:
        """Perform fulltext search with fallback"""
        if hasattr(self.context_manager, "text_search"):
            search_method = getattr(self.context_manager, "text_search")
            result = await search_method(query=query, limit=10)
            return result if isinstance(result, list) else []
        else:
            result = await self.context_manager.search_files(
                pattern=query, path=".", file_pattern="*"
            )
            return result if isinstance(result, list) else []

    async def _perform_hybrid_search(self, query: str) -> List[Dict[str, Any]]:
        """Perform hybrid search combining semantic and text search"""
        semantic_results = await self.context_manager.semantic_search(query=query, top_k=5)

        text_results = []
        if hasattr(self.context_manager, "search_files"):
            text_results = await self.context_manager.search_files(
                pattern=query, path=".", file_pattern="*"
            )

        return semantic_results + text_results[:5]

    def _apply_search_filters(
        self, results: List[Dict[str, Any]], filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply filters to search results"""
        if not filters:
            return results

        filtered_results = []
        for result in results:
            if self._passes_filters(result, filters):
                filtered_results.append(result)

        return filtered_results

    def _passes_filters(self, result: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if a result passes all filters"""
        # Filter by file type
        if filters.get("file_type"):
            file_path = result.get("file_path", result.get("file", ""))
            if not file_path.endswith(filters["file_type"]):
                return False

        # Filter by quality score
        if filters.get("quality_score_min"):
            score = result.get("score", 0)
            if score < filters["quality_score_min"]:
                return False

        return True

    async def _enhance_search_with_ai(
        self, query: str, results: List[Dict[str, Any]], search_type: str
    ) -> tuple:
        """Enhance search results with AI insights"""
        enhanced_results = results
        ai_insights = {}

        if self.is_ai_enabled() and results:
            try:
                context = (
                    await self.context_manager.load_context() if self.context_manager else None
                )

                enhanced_search_data = await self.ai_enhancer.enhance_advanced_search(
                    query, results, search_type, context
                )

                enhanced_results = enhanced_search_data.get("enhanced_results", results)
                ai_insights = enhanced_search_data.get("ai_insights", {})

            except (AttributeError, TypeError, ValueError, ConnectionError, IOError) as e:
                logger.debug("AI enhancement failed for advanced search: %s", e)

        return enhanced_results, ai_insights

    def _format_search_results(
        self,
        query: str,
        search_type: str,
        enhanced_results: List[Dict[str, Any]],
        ai_insights: Dict[str, Any],
    ) -> str:
        """Format the complete search results output"""
        result_parts = [
            f"🔍 **Advanced Search Results ({search_type})**",
            f"**Query:** {query}",
            f"**Results Found:** {len(enhanced_results)}",
            self.format_ai_enhancement_status(),
            "",
        ]

        # Add AI search insights
        result_parts.extend(self._format_ai_search_insights(ai_insights))

        # Display enhanced results
        result_parts.extend(self._format_search_results_display(enhanced_results))

        # Add AI-suggested related queries
        result_parts.extend(self._format_related_queries(ai_insights))

        # Add search tips
        result_parts.extend(self._format_search_tips())

        return "\n".join(result_parts)

    def _format_ai_search_insights(self, ai_insights: Dict[str, Any]) -> List[str]:
        """Format AI search insights section"""
        if not ai_insights.get("search_intent"):
            return []

        result_parts = ["## 🤖 AI Search Analysis"]
        result_parts.append(f"**Search Intent**: {ai_insights['search_intent']}")

        if ai_insights.get("semantic_groups"):
            groups = ai_insights["semantic_groups"]
            if groups and len(groups) > 1:
                result_parts.append(f"**Result Groups**: Found {len(groups)} semantic clusters")

        if ai_insights.get("refinement_suggestions"):
            suggestions = ai_insights["refinement_suggestions"][:2]
            if suggestions:
                result_parts.append("**Refinement Suggestions**:")
                for suggestion in suggestions:
                    result_parts.append(f"  • {suggestion}")

        result_parts.append("")
        return result_parts

    def _format_search_results_display(self, enhanced_results: List[Dict[str, Any]]) -> List[str]:
        """Format the display of search results"""
        result_parts = []

        for i, result in enumerate(enhanced_results[:10], 1):
            file_path = result.get("file_path", result.get("file", "Unknown"))
            score = result.get("score", 0)
            ai_relevance = result.get("ai_relevance_score", 0)
            content_preview = result.get("content", result.get("line", ""))[:150]
            metadata = result.get("metadata", {})
            line_number = result.get("line_number", "")

            # Format result display with AI scoring
            location = f":{line_number}" if line_number else ""
            score_display = f" (Score: {score:.3f})" if score > 0 else ""
            ai_score_display = f" AI: {ai_relevance:.2f}" if ai_relevance > 0 else ""

            result_parts.append(
                f"**{i}. {file_path}{location}**{score_display}{ai_score_display}\n"
                f"   {content_preview}{'...' if len(content_preview) == 150 else ''}\n"
            )

            if metadata:
                metadata_str = ", ".join([f"{k}: {v}" for k, v in metadata.items()])
                result_parts.append(f"   Metadata: {metadata_str}\n")

        if len(enhanced_results) > 10:
            result_parts.append(f"... and {len(enhanced_results) - 10} more results")

        return result_parts

    def _format_related_queries(self, ai_insights: Dict[str, Any]) -> List[str]:
        """Format AI-suggested related queries section"""
        if not ai_insights.get("related_queries"):
            return []

        related_queries = ai_insights["related_queries"]
        if not related_queries:
            return []

        result_parts = ["\n💡 **AI suggests also searching for**:"]
        for query_suggestion in related_queries:
            result_parts.append(f"  • {query_suggestion}")

        return result_parts

    def _format_search_tips(self) -> List[str]:
        """Format search tips section"""
        return [
            "\n**Search Types Available:**",
            "• `semantic` - AI-powered concept search",
            "• `fulltext` - Exact text matching",
            "• `pattern` - Regex/wildcard patterns",
            "• `hybrid` - Combined semantic + text (recommended)",
        ]
