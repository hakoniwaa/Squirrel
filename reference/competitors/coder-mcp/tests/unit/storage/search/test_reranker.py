"""
Unit tests for coder_mcp.storage.search.reranker module.
Tests search result reranking functionality.
"""

from unittest.mock import Mock, patch

import pytest

from coder_mcp.storage.search.reranker import (
    CrossEncoderReranker,
    FeatureExtractor,
    SearchReranker,
)


class TestFeatureExtractor:
    """Test the FeatureExtractor class."""

    def test_extract_with_exact_match(self):
        """Test feature extraction with exact match."""
        extractor = FeatureExtractor()

        features = extractor.extract(
            query="python function", content="This is a Python function example", metadata={}
        )

        assert features["exact_match_score"] == 1.0
        assert features["recency_score"] == 0.5  # Default
        assert features["popularity_score"] == 0.5  # Default
        assert "length_score" in features

    def test_extract_without_exact_match(self):
        """Test feature extraction without exact match."""
        extractor = FeatureExtractor()

        features = extractor.extract(
            query="javascript", content="This is a Python function example", metadata={}
        )

        assert features["exact_match_score"] == 0.0

    def test_extract_case_insensitive_match(self):
        """Test case-insensitive matching."""
        extractor = FeatureExtractor()

        features = extractor.extract(query="PYTHON", content="python is great", metadata={})

        assert features["exact_match_score"] == 1.0

    def test_extract_with_metadata(self):
        """Test extraction with metadata scores."""
        extractor = FeatureExtractor()

        metadata = {"recency_score": 0.9, "popularity_score": 0.7}

        features = extractor.extract(query="test", content="test content", metadata=metadata)

        assert features["recency_score"] == 0.9
        assert features["popularity_score"] == 0.7

    def test_length_score_calculation(self):
        """Test length score calculation."""
        extractor = FeatureExtractor()

        # Short content - high score
        features = extractor.extract(query="test", content="short", metadata={})
        assert features["length_score"] > 0.99

        # Medium content
        features = extractor.extract(query="test", content="x" * 5000, metadata={})
        assert 0.4 < features["length_score"] < 0.6

        # Very long content - low score
        features = extractor.extract(query="test", content="x" * 10000, metadata={})
        assert features["length_score"] <= 0.0


class TestSearchReranker:
    """Test the SearchReranker class."""

    @patch("coder_mcp.storage.search.reranker.HAS_SENTENCE_TRANSFORMERS", False)
    def test_initialization_without_transformers(self):
        """Test initialization without sentence transformers."""
        reranker = SearchReranker()

        assert reranker.cross_encoder is None
        assert reranker.feature_extractor is not None

    @patch("coder_mcp.storage.search.reranker.HAS_SENTENCE_TRANSFORMERS", True)
    @patch("coder_mcp.storage.search.reranker.CrossEncoder")
    def test_initialization_with_transformers(self, mock_cross_encoder):
        """Test initialization with sentence transformers."""
        mock_encoder_instance = Mock()
        mock_cross_encoder.return_value = mock_encoder_instance

        reranker = SearchReranker()

        assert reranker.cross_encoder is mock_encoder_instance
        mock_cross_encoder.assert_called_once_with("microsoft/codebert-base")

    @patch("coder_mcp.storage.search.reranker.HAS_SENTENCE_TRANSFORMERS", True)
    @patch("coder_mcp.storage.search.reranker.CrossEncoder")
    def test_initialization_with_transformer_error(self, mock_cross_encoder):
        """Test initialization when CrossEncoder fails."""
        mock_cross_encoder.side_effect = Exception("Model not found")

        reranker = SearchReranker()

        assert reranker.cross_encoder is None

    @pytest.mark.asyncio
    async def test_rerank_without_cross_encoder(self):
        """Test reranking without cross encoder."""
        reranker = SearchReranker()
        reranker.cross_encoder = None

        candidates = [
            {"content": "python programming", "score": 0.7, "metadata": {}},
            {"content": "javascript code", "score": 0.8, "metadata": {}},
            {"content": "python tutorial", "score": 0.6, "metadata": {}},
        ]

        results = await reranker.rerank("python", candidates, top_k=2)

        assert len(results) == 2
        # Results should have final_score
        assert all("final_score" in r for r in results)
        assert all("ranking_details" in r for r in results)

    @pytest.mark.asyncio
    async def test_rerank_with_cross_encoder(self):
        """Test reranking with cross encoder."""
        reranker = SearchReranker()

        # Mock cross encoder
        mock_encoder = Mock()
        mock_encoder.predict.return_value = [0.9]  # High relevance
        reranker.cross_encoder = mock_encoder

        candidates = [{"content": "test content", "score": 0.5, "metadata": {}}]

        results = await reranker.rerank("test query", candidates)

        mock_encoder.predict.assert_called_once()
        assert len(results) == 1
        assert results[0]["final_score"] > 0.5  # Should be boosted

    def test_calculate_final_score(self):
        """Test final score calculation."""
        reranker = SearchReranker()

        # Test score calculation with various inputs
        score = reranker._calculate_final_score(
            vector_score=0.7,
            cross_encoder_score=0.8,
            features={
                "exact_match_score": 1.0,
                "recency_score": 0.5,
                "popularity_score": 0.6,
                "length_score": 0.9,
            },
        )

        assert 0.0 <= score <= 1.0
        # Should be influenced by all factors
        assert score > 0.7  # Better than just vector score

    @pytest.mark.asyncio
    async def test_rerank_empty_candidates(self):
        """Test reranking with empty candidates."""
        reranker = SearchReranker()

        results = await reranker.rerank("query", [])

        assert results == []

    @pytest.mark.asyncio
    async def test_rerank_top_k_limiting(self):
        """Test that top_k limits results."""
        reranker = SearchReranker()

        candidates = [
            {"content": f"content {i}", "score": i / 10, "metadata": {}} for i in range(20)
        ]

        results = await reranker.rerank("test", candidates, top_k=5)

        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_rerank_preserves_candidate_data(self):
        """Test that reranking preserves original candidate data."""
        reranker = SearchReranker()

        candidates = [
            {
                "id": 123,
                "content": "test content",
                "score": 0.5,
                "metadata": {"custom": "data"},
                "extra_field": "value",
            }
        ]

        results = await reranker.rerank("test", candidates)

        result = results[0]
        assert result["id"] == 123
        assert result["extra_field"] == "value"
        assert result["metadata"]["custom"] == "data"


class TestCrossEncoderReranker:
    """Test the CrossEncoderReranker alias."""

    def test_alias_exists(self):
        """Test that CrossEncoderReranker is an alias for SearchReranker."""
        assert CrossEncoderReranker is SearchReranker

    def test_can_instantiate_via_alias(self):
        """Test instantiation through alias."""
        reranker = CrossEncoderReranker()
        assert isinstance(reranker, SearchReranker)


class TestIntegrationScenarios:
    """Test integration scenarios for the reranker."""

    @pytest.mark.asyncio
    async def test_rerank_code_search_results(self):
        """Test reranking code search results."""
        reranker = SearchReranker()

        # Mock realistic code search results
        candidates = [
            {
                "content": (
                    "def calculate_average(numbers):\n" "    return sum(numbers) / len(numbers)"
                ),
                "score": 0.6,
                "metadata": {
                    "file_path": "utils.py",
                    "recency_score": 0.8,
                    "popularity_score": 0.9,
                },
            },
            {
                "content": (
                    "# Function to compute mean\n"
                    "def mean(values):\n    return sum(values) / len(values)"
                ),
                "score": 0.65,
                "metadata": {
                    "file_path": "stats.py",
                    "recency_score": 0.7,
                    "popularity_score": 0.6,
                },
            },
            {
                "content": "average = lambda lst: sum(lst) / len(lst)",
                "score": 0.55,
                "metadata": {
                    "file_path": "helpers.py",
                    "recency_score": 0.5,
                    "popularity_score": 0.5,
                },
            },
        ]

        results = await reranker.rerank("calculate average function", candidates)

        # All results should be reranked
        assert len(results) == 3
        assert all("final_score" in r for r in results)

        # First result should have exact match bonus
        # Query: "calculate average function"
        # Content: "def calculate_average(numbers):\n    return sum(numbers) / len(numbers)"
        # Should match "calculate" and "average" but not "function" -> 2/3 = 0.67
        expected_score = 2 / 3
        actual_score = results[0]["ranking_details"]["features"]["exact_match_score"]
        assert abs(actual_score - expected_score) < 0.01

    @pytest.mark.asyncio
    async def test_rerank_with_various_content_types(self):
        """Test reranking with different content types."""
        reranker = SearchReranker()

        candidates = [
            {"content": "", "score": 0.9, "metadata": {}},  # Empty content
            {"content": None, "score": 0.8, "metadata": {}},  # None content
            {"content": "Valid content", "score": 0.7, "metadata": {}},
        ]

        # Should handle edge cases gracefully
        results = await reranker.rerank("test", candidates)

        assert len(results) <= 3
        # Should not crash on empty/None content
