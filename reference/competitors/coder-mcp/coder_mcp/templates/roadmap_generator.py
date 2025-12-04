#!/usr/bin/env python3
"""
Improvement Roadmap Generator
Generates personalized improvement roadmaps based on project context
"""

import logging
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class RoadmapGenerator:
    """Generates personalized improvement roadmaps"""

    # Roadmap configuration - data-driven approach
    ROADMAP_RULES: Dict[str, Dict[str, List[Dict[str, Any]]]] = {
        "quality": {
            "high": [
                {
                    "condition": lambda ctx: ctx.get("quality_metrics", {}).get("overall_score", 5)
                    < 7,
                    "items": [
                        "Improve code quality with automated linting",
                        "Add comprehensive test coverage",
                    ],
                }
            ],
            "medium": [
                {
                    "condition": lambda ctx: ctx.get("quality_metrics", {}).get("overall_score", 5)
                    < 8,
                    "items": [
                        "Refactor large functions into smaller, focused ones",
                        "Add comprehensive documentation",
                    ],
                }
            ],
        },
        "security": {
            "high": [
                {
                    "condition": lambda ctx: True,  # Always applicable
                    "items": [
                        "Implement input validation and sanitization",
                        "Add proper error handling and logging",
                    ],
                }
            ],
            "medium": [
                {
                    "condition": lambda ctx: True,
                    "items": [
                        "Review and update dependency security",
                        "Implement proper authentication patterns",
                    ],
                }
            ],
        },
        "performance": {
            "medium": [
                {
                    "condition": lambda ctx: True,
                    "items": [
                        "Optimize database queries and add indexes",
                        "Implement caching strategies",
                        "Add performance monitoring",
                    ],
                }
            ],
            "low": [
                {
                    "condition": lambda ctx: True,
                    "items": [
                        "Profile and optimize hot code paths",
                        "Consider async/await patterns where appropriate",
                    ],
                }
            ],
        },
        "maintainability": {
            "medium": [
                {
                    "condition": lambda ctx: True,
                    "items": [
                        "Implement proper dependency injection",
                        "Add comprehensive API documentation",
                    ],
                }
            ],
            "low": [
                {
                    "condition": lambda ctx: True,
                    "items": [
                        "Consider design pattern improvements",
                        "Add integration tests",
                    ],
                }
            ],
        },
    }

    # General recommendations that apply to all projects
    GENERAL_RECOMMENDATIONS = {
        "high": [],
        "medium": [
            "Set up continuous integration pipeline",
            "Implement automated testing",
        ],
        "low": [
            "Consider upgrading dependencies to latest versions",
            "Add advanced monitoring and alerting",
            "Implement feature flags for controlled rollouts",
        ],
    }

    def __init__(self):
        """Initialize roadmap generator"""

    async def generate_roadmap(
        self,
        context: Dict[str, Any],
        focus_areas: Optional[List[str]] = None,
        time_frame: str = "short_term",
    ) -> Dict[str, List[str]]:
        """Generate a personalized improvement roadmap

        Args:
            context: Project context from context manager
            focus_areas: Areas to focus on (quality, performance, security, maintainability)
            time_frame: Time frame for improvements (short_term, medium_term, long_term)

        Returns:
            Roadmap organized by priority (high, medium, low)
        """
        focus_areas = focus_areas or ["quality", "performance", "security", "maintainability"]
        roadmap: Dict[str, List[str]] = {"high": [], "medium": [], "low": []}

        try:
            # Apply focus area rules
            for focus_area in focus_areas:
                if focus_area in self.ROADMAP_RULES:
                    area_roadmap = self._generate_area_roadmap(context, focus_area)
                    self._merge_roadmaps(roadmap, area_roadmap)

            # Add general recommendations
            self._add_general_recommendations(roadmap, context, time_frame)

            # Apply time frame filtering
            roadmap = self._filter_by_time_frame(roadmap, time_frame)

            # Limit items per priority to avoid overwhelming users
            roadmap = self._limit_roadmap_items(roadmap)

        except Exception as e:  # noqa: BLE001  # Catch-all for roadmap generation errors
            logger.error("Error generating roadmap: %s", e)
            # Return minimal roadmap on error
            roadmap = {
                "high": ["Review and improve code quality"],
                "medium": ["Add comprehensive testing"],
                "low": ["Update documentation"],
            }

        return roadmap

    def _generate_area_roadmap(
        self, context: Dict[str, Any], focus_area: str
    ) -> Dict[str, List[str]]:
        """Generate roadmap for a specific focus area

        Args:
            context: Project context
            focus_area: Focus area to generate roadmap for

        Returns:
            Roadmap for the focus area
        """
        area_roadmap: Dict[str, List[str]] = {"high": [], "medium": [], "low": []}
        rules = self.ROADMAP_RULES.get(focus_area, {})

        for priority, rule_list in rules.items():
            for rule in rule_list:
                try:
                    if rule["condition"](context):
                        area_roadmap[priority].extend(rule["items"])
                except Exception as e:  # noqa: BLE001  # Catch-all for rule evaluation errors
                    logger.warning("Error evaluating rule condition: %s", e)

        return area_roadmap

    def _merge_roadmaps(self, target: Dict[str, List[str]], source: Dict[str, List[str]]) -> None:
        """Merge source roadmap into target roadmap

        Args:
            target: Target roadmap to merge into
            source: Source roadmap to merge from
        """
        for priority, items in source.items():
            if priority in target:
                # Avoid duplicates
                for item in items:
                    if item not in target[priority]:
                        target[priority].append(item)

    def _add_general_recommendations(
        self,
        roadmap: Dict[str, List[str]],
        context: Dict[str, Any],
        time_frame: str,  # noqa: ARG002
    ) -> None:
        """Add general recommendations to the roadmap

        Args:
            roadmap: Roadmap to add recommendations to
            context: Project context
            time_frame: Time frame for improvements
        """
        for priority, items in self.GENERAL_RECOMMENDATIONS.items():
            for item in items:
                if item not in roadmap[priority]:
                    roadmap[priority].append(item)

    def _filter_by_time_frame(
        self, roadmap: Dict[str, List[str]], time_frame: str  # noqa: ARG002
    ) -> Dict[str, List[str]]:
        """Filter roadmap items by time frame

        Args:
            roadmap: Roadmap to filter
            time_frame: Time frame for filtering

        Returns:
            Filtered roadmap
        """
        # For now, return all items regardless of time frame
        # This can be enhanced to filter based on estimated effort/complexity
        return roadmap

    def _limit_roadmap_items(
        self, roadmap: Dict[str, List[str]], max_per_priority: int = 5
    ) -> Dict[str, List[str]]:
        """Limit the number of items per priority to avoid overwhelming users

        Args:
            roadmap: Roadmap to limit
            max_per_priority: Maximum items per priority level

        Returns:
            Limited roadmap
        """
        limited_roadmap = {}
        for priority, items in roadmap.items():
            limited_roadmap[priority] = items[:max_per_priority]

        return limited_roadmap

    def add_custom_rule(
        self,
        focus_area: str,
        priority: str,
        condition_func: Callable[[Dict[str, Any]], bool],
        items: List[str],
    ) -> None:
        """Add a custom rule to the roadmap generator

        Args:
            focus_area: Focus area for the rule
            priority: Priority level (high, medium, low)
            condition_func: Function that takes context and returns bool
            items: List of recommendation items
        """
        if focus_area not in self.ROADMAP_RULES:
            self.ROADMAP_RULES[focus_area] = {"high": [], "medium": [], "low": []}

        if priority not in self.ROADMAP_RULES[focus_area]:
            self.ROADMAP_RULES[focus_area][priority] = []

        self.ROADMAP_RULES[focus_area][priority].append(
            {"condition": condition_func, "items": items}
        )

    def get_available_focus_areas(self) -> List[str]:
        """Get list of available focus areas

        Returns:
            List of focus area names
        """
        return list(self.ROADMAP_RULES.keys())

    def get_roadmap_info(self) -> Dict[str, Any]:
        """Get information about the roadmap generator

        Returns:
            Information about available rules and focus areas
        """
        rule_counts = {}
        for focus_area, rules in self.ROADMAP_RULES.items():
            rule_counts[focus_area] = sum(len(rule_list) for rule_list in rules.values())

        return {
            "available_focus_areas": self.get_available_focus_areas(),
            "total_rule_sets": sum(rule_counts.values()),
            "rules_per_area": rule_counts,
            "supported_priorities": ["high", "medium", "low"],
        }
