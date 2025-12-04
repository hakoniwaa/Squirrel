#!/usr/bin/env python3
"""
Generation AI Enhancement Module - Handles AI enhancement for code generation and scaffolding
"""

import logging
from typing import Any, Dict, List, Optional

from .base_enhancer import AIServiceError, BaseEnhancer

logger = logging.getLogger(__name__)


class GenerationEnhancer(BaseEnhancer):
    """Handles AI enhancement for code generation, scaffolding, and templates"""

    async def get_enhancement_capabilities(self) -> List[str]:
        """Return list of enhancement capabilities this enhancer provides"""
        return [
            "scaffold_enhancement",
            "code_generation",
            "template_improvement",
            "documentation_generation",
            "test_generation",
            "best_practices_application",
        ]

    async def enhance_scaffold_output(
        self, scaffold_result: Dict[str, Any], scaffold_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance scaffolding output with AI recommendations"""
        if not self._ensure_ai_available():
            return self._fallback_enhancement(
                scaffold_result, "AI scaffolding enhancement unavailable"
            )

        try:
            with self._safe_ai_call("scaffold_enhancement"):
                if self.ai_service is None:
                    return self._fallback_enhancement(scaffold_result, "AI service not available")

                ai_response = await self.ai_service.reason_about_code(
                    f"""Analyze this scaffolded feature and provide recommendations:

                    Feature type: {scaffold_context.get('feature_type')}
                    Feature name: {scaffold_context.get('name')}
                    Files created: {scaffold_context.get('files_created', [])}
                    Project context: {scaffold_context.get('project_context', {})}

                    Provide recommendations on:
                    1. Next steps for implementation
                    2. Improvements to consider
                    3. Patterns that would fit well
                    4. Testing strategies
                    5. Integration considerations
                    """,
                    code="",
                )

                enhanced_result = scaffold_result.copy()
                enhanced_result["ai_recommendations"] = {
                    "next_steps": self._extract_next_steps(ai_response.content),
                    "improvements": self._extract_improvements(ai_response.content),
                    "patterns_to_follow": self._extract_patterns_to_follow(ai_response.content),
                    "testing_strategy": self._extract_testing_strategy(ai_response.content),
                }

                logger.debug("Enhanced scaffold output with AI recommendations")
                return enhanced_result

        except AIServiceError:
            return self._fallback_enhancement(
                scaffold_result, "AI scaffolding enhancement unavailable"
            )
        except Exception as e:
            logger.warning(f"AI enhancement failed for scaffold output: {e}")
            return self._fallback_enhancement(
                scaffold_result, f"Scaffolding enhancement error: {str(e)}"
            )

    async def enhance_documentation_generation(
        self, basic_docs: str, code: str, language: str, doc_type: str = "comprehensive"
    ) -> str:
        """Enhance documentation generation with AI insights"""
        if not self._ensure_ai_available():
            return basic_docs

        try:
            with self._safe_ai_call("documentation_generation"):
                if self.ai_service is None:
                    return basic_docs

                ai_response = await self.ai_service.reason_about_code(
                    f"""Enhance this documentation for a {language} code:

                    Current documentation:
                    {basic_docs}

                    Code:
                    ```{language}
                    {code}
                    ```

                    Please provide enhanced documentation that includes:
                    1. Better descriptions of complex logic
                    2. Usage examples
                    3. Common pitfalls and gotchas
                    4. Performance considerations
                    5. Integration patterns
                    6. Testing recommendations

                    Type: {doc_type}
                    """,
                    code,
                )

                enhanced_docs = (
                    f"{basic_docs}\n\n## 🤖 AI-Enhanced Documentation\n\n{ai_response.content}"
                )

                logger.debug("Enhanced documentation generation with AI")
                return enhanced_docs

        except AIServiceError:
            return basic_docs
        except Exception as e:
            logger.warning(f"AI enhancement failed for documentation: {e}")
            return basic_docs

    async def generate_comprehensive_tests(
        self, code: str, language: str, test_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive test suites with AI"""
        if not self._ensure_ai_available():
            return {"tests": [], "message": "AI test generation unavailable"}

        test_types = test_types or ["unit", "integration", "edge_cases"]

        try:
            with self._safe_ai_call("test_generation"):
                if self.ai_service is None:
                    return {"tests": [], "message": "AI service not available"}

                ai_response = await self.ai_service.reason_about_code(
                    f"""Generate comprehensive tests for this {language} code:

                    Code:
                    ```{language}
                    {code}
                    ```

                    Generate tests for:
                    {', '.join(test_types)}

                    Include:
                    1. Unit tests for all public methods
                    2. Integration tests for external dependencies
                    3. Edge cases and error conditions
                    4. Performance benchmarks where applicable
                    5. Security tests for input validation
                    6. Mock strategies for dependencies
                    7. Test data factories and fixtures
                    """,
                    code,
                )

                return {
                    "test_suites": self._extract_test_suites(ai_response.content),
                    "test_strategy": self._extract_test_strategy(ai_response.content),
                    "mock_recommendations": self._extract_mock_recommendations(ai_response.content),
                    "test_data_patterns": self._extract_test_data_patterns(ai_response.content),
                    "coverage_targets": self._extract_coverage_targets(ai_response.content),
                    "performance_benchmarks": self._extract_performance_benchmarks(
                        ai_response.content
                    ),
                }

        except AIServiceError:
            return {"tests": [], "message": "AI test generation unavailable"}
        except Exception as e:
            logger.warning(f"Failed to generate comprehensive tests: {e}")
            return {"tests": [], "message": f"Test generation error: {str(e)}"}

    async def enhance_code_generation(
        self, generation_context: Dict[str, Any], requirements: str, language: str = "python"
    ) -> Dict[str, Any]:
        """Enhance code generation with AI-powered best practices"""
        if not self._ensure_ai_available():
            return {"generated_code": "", "message": "AI code generation unavailable"}

        try:
            with self._safe_ai_call("code_generation"):
                if self.ai_service is None:
                    return {"generated_code": "", "message": "AI service not available"}

                ai_response = await self.ai_service.reason_about_code(
                    f"""Generate high-quality {language} code based on these requirements:

                    Requirements: {requirements}
                    Context: {generation_context}

                    Generate code that follows:
                    1. SOLID principles
                    2. Clean code practices
                    3. Proper error handling
                    4. Comprehensive documentation
                    5. Type hints and validation
                    6. Security best practices
                    7. Performance considerations
                    8. Testable design patterns

                    Include:
                    - Main implementation
                    - Error handling
                    - Input validation
                    - Logging
                    - Type hints
                    - Docstrings
                    - Usage examples
                    """,
                    code="",
                )

                return {
                    "generated_code": self._extract_generated_code(ai_response.content),
                    "design_patterns": self._extract_design_patterns(ai_response.content),
                    "implementation_notes": self._extract_implementation_notes(ai_response.content),
                    "testing_approach": self._extract_testing_approach(ai_response.content),
                    "security_considerations": self._extract_security_considerations(
                        ai_response.content
                    ),
                    "performance_notes": self._extract_performance_notes(ai_response.content),
                    "future_enhancements": self._extract_future_enhancements(ai_response.content),
                }

        except AIServiceError:
            return {"generated_code": "", "message": "AI code generation unavailable"}
        except Exception as e:
            logger.warning(f"Failed to enhance code generation: {e}")
            return {"generated_code": "", "message": f"Code generation error: {str(e)}"}

    async def suggest_template_improvements(
        self, existing_templates: Dict[str, str], project_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Suggest improvements to existing templates"""
        if not self._ensure_ai_available():
            return {"improvements": [], "message": "AI template analysis unavailable"}

        try:
            with self._safe_ai_call("template_improvement"):
                if self.ai_service is None:
                    return {"improvements": [], "message": "AI service not available"}

                ai_response = await self.ai_service.reason_about_code(
                    f"""Analyze these templates and suggest improvements:

                    Existing templates: {existing_templates}
                    Project context: {project_context}

                    Suggest improvements for:
                    1. Template reusability and modularity
                    2. Better parameter handling
                    3. Enhanced error checking
                    4. More comprehensive examples
                    5. Integration with project patterns
                    6. Performance optimizations
                    7. Security enhancements
                    """,
                    code="",
                )

                return {
                    "template_improvements": self._extract_template_improvements(
                        ai_response.content
                    ),
                    "modularity_suggestions": self._extract_modularity_suggestions(
                        ai_response.content
                    ),
                    "parameter_enhancements": self._extract_parameter_enhancements(
                        ai_response.content
                    ),
                    "integration_patterns": self._extract_integration_patterns(ai_response.content),
                    "reusability_score": self._extract_score_from_response(
                        ai_response.content, 7.0
                    ),
                }

        except AIServiceError:
            return {"improvements": [], "message": "AI template analysis unavailable"}
        except Exception as e:
            logger.warning(f"Failed to suggest template improvements: {e}")
            return {"improvements": [], "message": f"Template analysis error: {str(e)}"}

    async def apply_best_practices(
        self, code: str, language: str, practice_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Apply language-specific best practices to code"""
        if not self._ensure_ai_available():
            return {"enhanced_code": code, "message": "AI best practices application unavailable"}

        practice_areas = practice_areas or [
            "structure",
            "performance",
            "security",
            "maintainability",
        ]

        try:
            with self._safe_ai_call("best_practices_application"):
                if self.ai_service is None:
                    return {"enhanced_code": code, "message": "AI service not available"}

                ai_response = await self.ai_service.reason_about_code(
                    f"""Apply {language} best practices to this code:

                    Code:
                    ```{language}
                    {code}
                    ```

                    Focus areas: {', '.join(practice_areas)}

                    Apply best practices for:
                    1. Code structure and organization
                    2. Naming conventions
                    3. Error handling patterns
                    4. Performance optimizations
                    5. Security hardening
                    6. Type safety
                    7. Documentation standards
                    8. Testing considerations
                    """,
                    code,
                )

                return {
                    "enhanced_code": self._extract_enhanced_code(ai_response.content),
                    "applied_practices": self._extract_applied_practices(ai_response.content),
                    "improvement_summary": self._extract_improvement_summary(ai_response.content),
                    "quality_score_improvement": self._extract_quality_improvement(
                        ai_response.content
                    ),
                    "recommendations": self._extract_recommendations(ai_response.content),
                }

        except AIServiceError:
            return {"enhanced_code": code, "message": "AI best practices application unavailable"}
        except Exception as e:
            logger.warning(f"Failed to apply best practices: {e}")
            return {"enhanced_code": code, "message": f"Best practices error: {str(e)}"}

    # Helper methods for parsing AI responses
    def _extract_next_steps(self, ai_response: str) -> List[str]:
        """Extract next steps from AI response"""
        return self._extract_list_from_response(ai_response, ["next", "step", "implement", "todo"])

    def _extract_improvements(self, ai_response: str) -> List[str]:
        """Extract improvements from AI response"""
        return self._extract_list_from_response(
            ai_response, ["improve", "enhance", "better", "optimize"]
        )

    def _extract_patterns_to_follow(self, ai_response: str) -> List[str]:
        """Extract patterns to follow from AI response"""
        return self._extract_list_from_response(ai_response, ["pattern", "follow", "use", "apply"])

    def _extract_testing_strategy(self, ai_response: str) -> List[str]:
        """Extract testing strategy from AI response"""
        return self._extract_list_from_response(
            ai_response, ["test", "testing", "verify", "validate"]
        )

    def _extract_test_suites(self, ai_response: str) -> List[Dict[str, Any]]:
        """Extract test suites from AI response"""
        suites = []
        lines = ai_response.split("\n")
        current_suite: Dict[str, Any] = {}

        for line in lines:
            line = line.strip()
            if "test" in line.lower() and ("suite" in line.lower() or "class" in line.lower()):
                if current_suite:
                    suites.append(current_suite)
                current_suite = {"name": line, "tests": []}
            elif current_suite and line.startswith(("def test", "test_", "it(")):
                if not isinstance(current_suite.get("tests"), list):
                    current_suite["tests"] = []
                current_suite["tests"].append(line)

        if current_suite:
            suites.append(current_suite)

        return suites[:5]  # Limit to 5 test suites

    def _extract_test_strategy(self, ai_response: str) -> str:
        """Extract test strategy from AI response"""
        return (
            self._extract_key_value_from_response(ai_response, "strategy")
            or "Comprehensive testing approach"
        )

    def _extract_mock_recommendations(self, ai_response: str) -> List[str]:
        """Extract mock recommendations from AI response"""
        return self._extract_list_from_response(ai_response, ["mock", "stub", "fake", "double"])

    def _extract_test_data_patterns(self, ai_response: str) -> List[str]:
        """Extract test data patterns from AI response"""
        return self._extract_list_from_response(
            ai_response, ["data", "fixture", "factory", "builder"]
        )

    def _extract_coverage_targets(self, ai_response: str) -> Dict[str, Any]:
        """Extract coverage targets from AI response"""
        coverage_percentage = self._extract_score_from_response(ai_response, 80.0)
        return {
            "target_percentage": coverage_percentage,
            "critical_paths": self._extract_list_from_response(
                ai_response, ["critical", "important", "core"]
            ),
        }

    def _extract_performance_benchmarks(self, ai_response: str) -> List[str]:
        """Extract performance benchmarks from AI response"""
        return self._extract_list_from_response(
            ai_response, ["benchmark", "performance", "timing", "speed"]
        )

    def _extract_generated_code(self, ai_response: str) -> str:
        """Extract generated code from AI response"""
        lines = ai_response.split("\n")
        in_code_block = False
        code_lines = []

        for line in lines:
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                code_lines.append(line)

        return "\n".join(code_lines) if code_lines else "# No code generated"

    def _extract_design_patterns(self, ai_response: str) -> List[str]:
        """Extract design patterns from AI response"""
        return self._extract_list_from_response(
            ai_response, ["pattern", "design", "singleton", "factory", "observer"]
        )

    def _extract_implementation_notes(self, ai_response: str) -> List[str]:
        """Extract implementation notes from AI response"""
        return self._extract_list_from_response(
            ai_response, ["implement", "note", "consider", "important"]
        )

    def _extract_testing_approach(self, ai_response: str) -> str:
        """Extract testing approach from AI response"""
        return (
            self._extract_key_value_from_response(ai_response, "testing")
            or "Test-driven development recommended"
        )

    def _extract_security_considerations(self, ai_response: str) -> List[str]:
        """Extract security considerations from AI response"""
        return self._extract_list_from_response(
            ai_response, ["security", "secure", "validate", "sanitize", "authenticate"]
        )

    def _extract_performance_notes(self, ai_response: str) -> List[str]:
        """Extract performance notes from AI response"""
        return self._extract_list_from_response(
            ai_response, ["performance", "optimize", "cache", "async"]
        )

    def _extract_future_enhancements(self, ai_response: str) -> List[str]:
        """Extract future enhancements from AI response"""
        return self._extract_list_from_response(
            ai_response, ["future", "enhance", "extend", "expand"]
        )

    def _extract_template_improvements(self, ai_response: str) -> List[str]:
        """Extract template improvements from AI response"""
        return self._extract_list_from_response(
            ai_response, ["template", "improve", "enhance", "better"]
        )

    def _extract_modularity_suggestions(self, ai_response: str) -> List[str]:
        """Extract modularity suggestions from AI response"""
        return self._extract_list_from_response(
            ai_response, ["modular", "reusable", "component", "module"]
        )

    def _extract_parameter_enhancements(self, ai_response: str) -> List[str]:
        """Extract parameter enhancements from AI response"""
        return self._extract_list_from_response(
            ai_response, ["parameter", "argument", "config", "option"]
        )

    def _extract_integration_patterns(self, ai_response: str) -> List[str]:
        """Extract integration patterns from AI response"""
        return self._extract_list_from_response(
            ai_response, ["integration", "connect", "interface", "api"]
        )

    def _extract_enhanced_code(self, ai_response: str) -> str:
        """Extract enhanced code from AI response"""
        return self._extract_generated_code(ai_response)

    def _extract_applied_practices(self, ai_response: str) -> List[str]:
        """Extract applied practices from AI response"""
        return self._extract_list_from_response(
            ai_response, ["applied", "practice", "improvement", "standard"]
        )

    def _extract_improvement_summary(self, ai_response: str) -> str:
        """Extract improvement summary from AI response"""
        return (
            self._extract_key_value_from_response(ai_response, "summary")
            or "Code improvements applied"
        )

    def _extract_quality_improvement(self, ai_response: str) -> float:
        """Extract quality improvement score from AI response"""
        return self._extract_score_from_response(ai_response, 1.0)

    def _extract_recommendations(self, ai_response: str) -> List[str]:
        """Extract recommendations from AI response"""
        return self._extract_list_from_response(
            ai_response, ["recommend", "suggest", "consider", "should"]
        )
