#!/usr/bin/env python3
"""
Comprehensive tests for the modular AI enhancer architecture
Tests all enhancer modules and the orchestrator
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import enhancer classes from the new package structure
from coder_mcp.ai.enhancers import (
    BaseEnhancer,
    CodeEnhancer,
    ContextEnhancer,
    DependencyEnhancer,
    EnhancerOrchestrator,
    GenerationEnhancer,
    SearchEnhancer,
)


class MockConfigManager:
    """Mock configuration manager for testing"""

    def __init__(self, ai_enabled=True):
        self.ai_enabled = ai_enabled
        self.config = self

    def is_ai_enabled(self):
        return self.ai_enabled

    def get_ai_limits(self):
        return {"max_tokens": 4096, "max_requests_per_hour": 100}


@pytest.fixture
def mock_config_manager():
    """Create a mock configuration manager"""
    return MockConfigManager(ai_enabled=True)


@pytest.fixture
def mock_config_manager_disabled():
    """Create a mock configuration manager with AI disabled"""
    return MockConfigManager(ai_enabled=False)


@pytest.fixture
def mock_ai_service():
    """Create a mock AI service"""
    mock_service = AsyncMock()
    mock_response = MagicMock()
    mock_response.content = (
        "Test AI response content with suggestions: improve readability, add tests"
    )
    mock_service.reason_about_code.return_value = mock_response

    # Mock analyze_code method
    mock_analysis_result = MagicMock()
    mock_analysis_result.security_concerns = ["SQL injection risk"]
    mock_analysis_result.performance_insights = ["O(n²) algorithm detected"]
    mock_analysis_result.suggestions = ["Extract method for better readability"]
    mock_analysis_result.metrics = {"maintainability": 8.0, "complexity": 6.0}
    mock_analysis_result.summary = "Overall code quality is good"
    mock_analysis_result.issues = [{"description": "Long function detected", "severity": "medium"}]
    mock_service.analyze_code.return_value = mock_analysis_result

    return mock_service


@pytest.fixture
def mock_processor():
    """Create a mock response processor"""
    return MagicMock()


class TestBaseEnhancer:
    """Test the abstract base enhancer functionality"""

    def test_enabled_initialization(self, mock_config_manager):
        """Test base enhancer initialization with AI enabled"""
        with (
            patch("coder_mcp.ai.enhancers.base_enhancer.OpenAIService"),
            patch("coder_mcp.ai.enhancers.base_enhancer.ResponseProcessor"),
            patch("coder_mcp.ai.enhancers.base_enhancer.ConfigurationManager") as mock_config,
        ):

            mock_config.return_value = MagicMock()

            # Create a concrete implementation for testing
            class TestEnhancer(BaseEnhancer):
                async def get_enhancement_capabilities(self):
                    return ["test"]

            enhancer = TestEnhancer(mock_config_manager)

            assert enhancer.enabled is True
            assert enhancer.ai_service is not None
            assert enhancer.processor is not None

    def test_disabled_initialization(self, mock_config_manager_disabled):
        """Test base enhancer initialization with AI disabled"""

        class TestEnhancer(BaseEnhancer):
            async def get_enhancement_capabilities(self):
                return ["test"]

        enhancer = TestEnhancer(mock_config_manager_disabled)

        assert enhancer.enabled is False
        assert enhancer.ai_service is None
        assert enhancer.processor is None

    def test_status_reporting(self, mock_config_manager):
        """Test status reporting functionality"""
        with (
            patch("coder_mcp.ai.enhancers.base_enhancer.OpenAIService"),
            patch("coder_mcp.ai.enhancers.base_enhancer.ResponseProcessor"),
            patch("coder_mcp.ai.enhancers.base_enhancer.ConfigurationManager"),
        ):

            class TestEnhancer(BaseEnhancer):
                async def get_enhancement_capabilities(self):
                    return ["test"]

            enhancer = TestEnhancer(mock_config_manager)
            status = enhancer.get_status()

            assert status["enabled"] is True
            assert status["enhancer_type"] == "TestEnhancer"
            assert "config" in status

    def test_helper_methods(self, mock_config_manager_disabled):
        """Test helper methods for parsing AI responses"""

        class TestEnhancer(BaseEnhancer):
            async def get_enhancement_capabilities(self):
                return ["test"]

        enhancer = TestEnhancer(mock_config_manager_disabled)

        # Test list extraction
        response = "- suggestion one\n- suggestion two\n* suggestion three"
        suggestions = enhancer._extract_list_from_response(response, ["suggestion"])
        assert len(suggestions) >= 2

        # Test score extraction
        response = "Quality score: 8.5 out of 10"
        score = enhancer._extract_score_from_response(response)
        assert score == 8.5

        # Test fallback enhancement
        original_data = {"test": "data"}
        fallback = enhancer._fallback_enhancement(original_data, "Test message")
        assert "ai_fallback" in fallback


class TestCodeEnhancer:
    """Test the code enhancement module"""

    @pytest.fixture
    def code_enhancer(self, mock_config_manager):
        """Create a code enhancer instance for testing"""
        with (
            patch("coder_mcp.ai.enhancers.base_enhancer.OpenAIService"),
            patch("coder_mcp.ai.enhancers.base_enhancer.ResponseProcessor"),
            patch("coder_mcp.ai.enhancers.base_enhancer.ConfigurationManager") as mock_config,
        ):

            mock_config.return_value = MagicMock()

            return CodeEnhancer(mock_config_manager)

    @pytest.mark.asyncio
    async def test_capabilities(self, code_enhancer):
        """Test that code enhancer reports correct capabilities"""
        capabilities = await code_enhancer.get_enhancement_capabilities()

        expected_capabilities = [
            "code_analysis",
            "quality_assessment",
            "code_smell_detection",
            "refactoring_suggestions",
            "security_analysis",
            "performance_insights",
        ]

        for capability in expected_capabilities:
            assert capability in capabilities

    @pytest.mark.asyncio
    async def test_enhance_analysis(self, code_enhancer, mock_ai_service):
        """Test code analysis enhancement"""
        code_enhancer.ai_service = mock_ai_service

        basic_analysis = {"quality_score": 7}
        code = "def test(): pass"
        language = "python"

        result = await code_enhancer.enhance_analysis(basic_analysis, code, language)

        assert "ai_insights" in result
        assert "security_risks" in result["ai_insights"]
        assert "performance_insights" in result["ai_insights"]
        assert "metrics" in result
        assert result["metrics"]["ai_quality_score"] == 8.0

    @pytest.mark.asyncio
    async def test_enhance_code_smells(self, code_enhancer, mock_ai_service):
        """Test code smell enhancement"""
        code_enhancer.ai_service = mock_ai_service

        basic_smells = [{"type": "long_function", "line": 10}]
        code = "def very_long_function(): pass"
        language = "python"

        result = await code_enhancer.enhance_code_smells(basic_smells, code, language)

        assert "basic_smells" in result
        assert "ai_detected_issues" in result
        assert "ai_quality_assessment" in result
        assert result["ai_quality_assessment"]["overall_score"] == 8.0

    @pytest.mark.asyncio
    async def test_disabled_enhancer(self, mock_config_manager_disabled):
        """Test code enhancer behavior when AI is disabled"""
        enhancer = CodeEnhancer(mock_config_manager_disabled)

        basic_analysis = {"quality_score": 7}
        result = await enhancer.enhance_analysis(basic_analysis, "code", "python")

        assert "ai_fallback" in result


class TestSearchEnhancer:
    """Test the search enhancement module"""

    @pytest.fixture
    def search_enhancer(self, mock_config_manager):
        """Create a search enhancer instance for testing"""
        with (
            patch("coder_mcp.ai.enhancers.base_enhancer.OpenAIService"),
            patch("coder_mcp.ai.enhancers.base_enhancer.ResponseProcessor"),
            patch("coder_mcp.ai.enhancers.base_enhancer.ConfigurationManager") as mock_config,
        ):

            mock_config.return_value = MagicMock()

            return SearchEnhancer(mock_config_manager)

    @pytest.mark.asyncio
    async def test_capabilities(self, search_enhancer):
        """Test that search enhancer reports correct capabilities"""
        capabilities = await search_enhancer.get_enhancement_capabilities()

        expected_capabilities = [
            "query_understanding",
            "result_reranking",  # actual capability name
            "semantic_search",
            "search_suggestions",
            "intent_detection",  # actual capability name
            "context_expansion",  # additional actual capability
        ]

        for capability in expected_capabilities:
            assert capability in capabilities

    @pytest.mark.asyncio
    async def test_enhance_search(self, search_enhancer, mock_ai_service):
        """Test search enhancement"""
        search_enhancer.ai_service = mock_ai_service

        query = "authentication function"
        basic_results = [
            {"content": "def authenticate_user(): pass", "path": "auth.py"},
            {"content": "def login(): pass", "path": "login.py"},
        ]

        enhanced_results, ai_insights = await search_enhancer.enhance_search(query, basic_results)

        assert len(enhanced_results) == len(basic_results)
        assert ai_insights is not None

    @pytest.mark.asyncio
    async def test_suggest_related_searches(self, search_enhancer, mock_ai_service):
        """Test related search suggestions"""
        search_enhancer.ai_service = mock_ai_service

        query = "user authentication"
        suggestions = await search_enhancer.suggest_related_searches(query)

        # Should return some suggestions (empty list if AI disabled)
        assert isinstance(suggestions, list)


class TestContextEnhancer:
    """Test the context enhancement module"""

    @pytest.fixture
    def context_enhancer(self, mock_config_manager):
        """Create a context enhancer instance for testing"""
        with (
            patch("coder_mcp.ai.enhancers.base_enhancer.OpenAIService"),
            patch("coder_mcp.ai.enhancers.base_enhancer.ResponseProcessor"),
            patch("coder_mcp.ai.enhancers.base_enhancer.OpenAIService") as mock_openai,
            patch("coder_mcp.ai.enhancers.base_enhancer.ResponseProcessor") as mock_proc,
        ):

            mock_openai.return_value = MagicMock()
            mock_proc.return_value = MagicMock()

            return ContextEnhancer(mock_config_manager)

    @pytest.mark.asyncio
    async def test_capabilities(self, context_enhancer):
        """Test that context enhancer reports correct capabilities"""
        capabilities = await context_enhancer.get_enhancement_capabilities()

        expected_capabilities = [
            "project_understanding",
            "context_building",
            "file_relationships",
            "architecture_analysis",
            "pattern_recognition",
            "knowledge_extraction",
        ]

        for capability in expected_capabilities:
            assert capability in capabilities

    @pytest.mark.asyncio
    async def test_enhance_context_understanding(self, context_enhancer, mock_ai_service):
        """Test context understanding enhancement"""
        context_enhancer.ai_service = mock_ai_service

        context_summary = {"structure": {"files": 100}, "quality_metrics": {"score": 8}}
        workspace_path = "/test/workspace"

        result = await context_enhancer.enhance_context_understanding(
            context_summary, workspace_path
        )

        assert isinstance(result, dict)
        # Should have some insights when AI is enabled
        if context_enhancer.enabled:
            assert len(result) > 0


class TestDependencyEnhancer:
    """Test the dependency enhancement module"""

    @pytest.fixture
    def dependency_enhancer(self, mock_config_manager):
        """Create a dependency enhancer instance for testing"""
        with (
            patch("coder_mcp.ai.enhancers.base_enhancer.OpenAIService") as mock_openai,
            patch("coder_mcp.ai.enhancers.base_enhancer.ResponseProcessor") as mock_proc,
        ):

            mock_openai.return_value = MagicMock()
            mock_proc.return_value = MagicMock()

            return DependencyEnhancer(mock_config_manager)

    @pytest.mark.asyncio
    async def test_capabilities(self, dependency_enhancer):
        """Test that dependency enhancer reports correct capabilities"""
        capabilities = await dependency_enhancer.get_enhancement_capabilities()

        expected_capabilities = [
            "dependency_analysis",
            "vulnerability_detection",
            "update_recommendations",
            "compatibility_assessment",
            "license_analysis",
            "security_audit",
        ]

        for capability in expected_capabilities:
            assert capability in capabilities

    @pytest.mark.asyncio
    async def test_enhance_dependency_analysis(self, dependency_enhancer, mock_ai_service):
        """Test dependency analysis enhancement"""
        dependency_enhancer.ai_service = mock_ai_service

        basic_deps = {"requirements": ["requests==2.25.1", "flask==1.1.2"]}
        project_context = {"type": "web_app"}

        result = await dependency_enhancer.enhance_dependency_analysis(basic_deps, project_context)

        assert isinstance(result, dict)
        # Should enhance with AI analysis when enabled
        if dependency_enhancer.enabled:
            assert "ai_analysis" in result or "ai_fallback" not in result


class TestGenerationEnhancer:
    """Test the generation enhancement module"""

    @pytest.fixture
    def generation_enhancer(self, mock_config_manager):
        """Create a generation enhancer instance for testing"""
        with (
            patch("coder_mcp.ai.enhancers.base_enhancer.OpenAIService") as mock_openai,
            patch("coder_mcp.ai.enhancers.base_enhancer.ResponseProcessor") as mock_proc,
        ):

            mock_openai.return_value = MagicMock()
            mock_proc.return_value = MagicMock()

            return GenerationEnhancer(mock_config_manager)

    @pytest.mark.asyncio
    async def test_capabilities(self, generation_enhancer):
        """Test that generation enhancer reports correct capabilities"""
        capabilities = await generation_enhancer.get_enhancement_capabilities()

        expected_capabilities = [
            "scaffold_enhancement",
            "code_generation",
            "template_improvement",
            "documentation_generation",
            "test_generation",
            "best_practices_application",
        ]

        for capability in expected_capabilities:
            assert capability in capabilities

    @pytest.mark.asyncio
    async def test_enhance_scaffold_output(self, generation_enhancer, mock_ai_service):
        """Test scaffold enhancement"""
        generation_enhancer.ai_service = mock_ai_service

        scaffold_result = {"files_created": ["models/user.py", "views/user.py"]}
        scaffold_context = {
            "feature_type": "api_endpoint",
            "name": "UserAPI",
            "files_created": ["models/user.py", "views/user.py"],
        }

        result = await generation_enhancer.enhance_scaffold_output(
            scaffold_result, scaffold_context
        )

        assert "files_created" in result
        # Should have AI recommendations when enabled
        if generation_enhancer.enabled:
            assert "ai_recommendations" in result or "ai_fallback" in result


class TestEnhancerOrchestrator:
    """Test the enhancer orchestrator coordination"""

    @pytest.fixture
    def orchestrator(self, mock_config_manager):
        """Create an orchestrator instance for testing"""
        with (
            patch("coder_mcp.ai.enhancers.base_enhancer.OpenAIService") as mock_openai,
            patch("coder_mcp.ai.enhancers.base_enhancer.ResponseProcessor") as mock_proc,
        ):

            mock_openai.return_value = MagicMock()
            mock_proc.return_value = MagicMock()

            return EnhancerOrchestrator(mock_config_manager)

    def test_initialization(self, orchestrator):
        """Test orchestrator initialization"""
        assert orchestrator.enabled is True
        assert len(orchestrator._enhancers) == 5  # All enhancer types

        # Check that all enhancers are initialized
        expected_enhancers = ["code", "search", "context", "dependency", "generation"]
        for enhancer_type in expected_enhancers:
            assert enhancer_type in orchestrator._enhancers

    def test_get_enhancer(self, orchestrator):
        """Test getting specific enhancers"""
        code_enhancer = orchestrator.get_enhancer("code")
        assert isinstance(code_enhancer, CodeEnhancer)

        search_enhancer = orchestrator.get_enhancer("search")
        assert isinstance(search_enhancer, SearchEnhancer)

        unknown_enhancer = orchestrator.get_enhancer("unknown")
        assert unknown_enhancer is None

    @pytest.mark.asyncio
    async def test_status_reporting(self, orchestrator):
        """Test comprehensive status reporting"""
        status = await orchestrator.get_status()

        assert status["orchestrator_enabled"] is True
        assert status["total_enhancers"] == 5
        assert "enhancer_status" in status
        assert "capabilities" in status

        # Each enhancer should have status
        for enhancer_type in ["code", "search", "context", "dependency", "generation"]:
            assert enhancer_type in status["enhancer_status"]

    @pytest.mark.asyncio
    async def test_code_enhancement_delegation(self, orchestrator, mock_ai_service):
        """Test that code enhancement is properly delegated"""
        # Mock the code enhancer
        orchestrator._enhancers["code"].ai_service = mock_ai_service

        basic_analysis = {"quality_score": 7}
        result = await orchestrator.enhance_analysis(basic_analysis, "code", "python")

        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_search_enhancement_delegation(self, orchestrator, mock_ai_service):
        """Test that search enhancement is properly delegated"""
        # Mock the search enhancer
        orchestrator._enhancers["search"].ai_service = mock_ai_service

        query = "test query"
        basic_results = [{"content": "test content"}]

        enhanced_results, insights = await orchestrator.enhance_search(query, basic_results)

        assert isinstance(enhanced_results, list)

    @pytest.mark.asyncio
    async def test_backward_compatibility(self, orchestrator, mock_ai_service):
        """Test backward compatibility methods"""
        # Mock enhancers
        orchestrator._enhancers["context"].ai_service = mock_ai_service
        orchestrator._enhancers["dependency"].ai_service = mock_ai_service

        basic_roadmap = {"high": [], "medium": [], "low": []}
        codebase_summary = {"dependencies": {}, "workspace_path": "/test"}

        result = await orchestrator.enhance_improvement_roadmap(basic_roadmap, codebase_summary)

        assert isinstance(result, dict)
        assert "high" in result  # Should maintain basic structure

    def test_disabled_orchestrator(self, mock_config_manager_disabled):
        """Test orchestrator behavior when AI is disabled"""
        orchestrator = EnhancerOrchestrator(mock_config_manager_disabled)

        assert orchestrator.enabled is False
        assert len(orchestrator._enhancers) == 0  # No enhancers initialized


class TestErrorHandling:
    """Test error handling across all enhancers"""

    @pytest.mark.asyncio
    async def test_ai_service_error_handling(self, mock_config_manager):
        """Test handling of AI service errors"""
        with (
            patch("coder_mcp.ai.enhancers.base_enhancer.OpenAIService") as mock_openai,
            patch("coder_mcp.ai.enhancers.base_enhancer.ResponseProcessor") as mock_proc,
        ):

            # Mock AI service to raise an error
            mock_service = AsyncMock()
            mock_service.analyze_code.side_effect = Exception("AI Service Error")
            mock_openai.return_value = mock_service
            mock_proc.return_value = MagicMock()

            enhancer = CodeEnhancer(mock_config_manager)
            enhancer.ai_service = mock_service

            basic_analysis = {"quality_score": 7}
            result = await enhancer.enhance_analysis(basic_analysis, "code", "python")

            # Should gracefully handle error and return fallback
            assert "ai_fallback" in result

    @pytest.mark.asyncio
    async def test_orchestrator_error_isolation(self, mock_config_manager):
        """Test that orchestrator isolates errors from individual enhancers"""
        with (
            patch("coder_mcp.ai.enhancers.base_enhancer.OpenAIService") as mock_openai,
            patch("coder_mcp.ai.enhancers.base_enhancer.ResponseProcessor") as mock_proc,
        ):

            mock_openai.return_value = MagicMock()
            mock_proc.return_value = MagicMock()

            orchestrator = EnhancerOrchestrator(mock_config_manager)

            # Mock one enhancer to fail
            orchestrator._enhancers["code"].enhance_analysis = AsyncMock(
                side_effect=Exception("Test error")
            )

            basic_analysis = {"quality_score": 7}
            result = await orchestrator.enhance_analysis(basic_analysis, "code", "python")

            # Should return original data even if one enhancer fails
            assert "quality_score" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
