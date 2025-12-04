"""
Unit tests for HybridSearch class.

This module tests the hybrid search functionality that combines
semantic and text search strategies for comprehensive results.
"""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, create_autospec, patch

import pytest

from coder_mcp.context.search.hybrid_search import HybridSearch
from coder_mcp.core import ConfigurationManager


class TestHybridSearch:
    """Test cases for HybridSearch."""

    @pytest.fixture
    def mock_config_manager(self):
        """Create a mock configuration manager."""
        # Use create_autospec to properly mock the ConfigurationManager
        mock_config = create_autospec(ConfigurationManager, instance=True)
        mock_config.get_workspace_config = Mock(
            return_value={
                "search": {"semantic_weight": 0.6, "text_weight": 0.4, "max_results": 100}
            }
        )
        return mock_config

    @pytest.fixture
    def mock_semantic_search(self):
        """Create a mock semantic search instance."""
        mock_search = Mock()
        mock_search.search = AsyncMock()
        return mock_search

    @pytest.fixture
    def mock_text_search(self):
        """Create a mock text search instance."""
        mock_search = Mock()
        mock_search.search_files = AsyncMock()
        return mock_search

    @pytest.fixture
    def hybrid_search(self, mock_config_manager, mock_semantic_search, mock_text_search):
        """Create a HybridSearch instance with mocked dependencies."""
        workspace_root = Path("/test/workspace")

        with (
            patch("coder_mcp.context.search.hybrid_search.SemanticSearch") as MockSemantic,
            patch("coder_mcp.context.search.hybrid_search.TextSearch") as MockText,
        ):

            MockSemantic.return_value = mock_semantic_search
            MockText.return_value = mock_text_search

            search = HybridSearch(workspace_root, mock_config_manager)
            return search

    def test_initialization(self, hybrid_search):
        """Test that HybridSearch initializes correctly."""
        assert hybrid_search.workspace_root == Path("/test/workspace")
        assert hybrid_search.config_manager is not None
        assert hybrid_search.semantic_search is not None
        assert hybrid_search.text_search is not None
        assert hybrid_search.semantic_weight == 0.6
        assert hybrid_search.text_weight == 0.4

    @pytest.mark.asyncio
    async def test_search_combined_strategy(self, hybrid_search):
        """Test search with combined strategy."""
        # Mock search results
        semantic_results = [
            {"file": "file1.py", "score": 0.9, "content": "semantic result 1"},
            {"file": "file2.py", "score": 0.8, "content": "semantic result 2"},
        ]
        text_results = [
            {"file": "file3.py", "score": 0.85, "content": "text result 1"},
            {"file": "file1.py", "score": 0.75, "content": "text result 2"},
        ]

        hybrid_search.semantic_search.search.return_value = semantic_results
        hybrid_search.text_search.search_files.return_value = text_results

        # Mock the merge method
        with patch.object(
            hybrid_search, "_merge_and_rank_results", new_callable=AsyncMock
        ) as mock_merge:
            mock_merge.return_value = [
                {"file": "file1.py", "score": 0.87, "content": "merged result"},
                {"file": "file3.py", "score": 0.85, "content": "text result 1"},
            ]

            results = await hybrid_search.search("test query", top_k=5, search_strategy="combined")

            assert len(results) == 2
            assert results[0]["file"] == "file1.py"
            mock_merge.assert_called_once_with(semantic_results, text_results, 0.6)

    @pytest.mark.asyncio
    async def test_search_semantic_first_strategy(self, hybrid_search):
        """Test search with semantic_first strategy."""
        semantic_results = [
            {"file": "file1.py", "score": 0.9, "content": "result 1"},
            {"file": "file2.py", "score": 0.8, "content": "result 2"},
        ]

        hybrid_search.semantic_search.search.return_value = semantic_results

        with patch.object(
            hybrid_search, "_semantic_first_search", new_callable=AsyncMock
        ) as mock_method:
            mock_method.return_value = semantic_results

            results = await hybrid_search.search(
                "test query", top_k=5, search_strategy="semantic_first"
            )

            assert results == semantic_results
            mock_method.assert_called_once_with("test query", 5)

    @pytest.mark.asyncio
    async def test_search_text_first_strategy(self, hybrid_search):
        """Test search with text_first strategy."""
        text_results = [
            {"file": "file1.py", "score": 0.85, "content": "result 1"},
        ]

        hybrid_search.text_search.search_files.return_value = text_results

        with patch.object(
            hybrid_search, "_text_first_search", new_callable=AsyncMock
        ) as mock_method:
            mock_method.return_value = text_results

            results = await hybrid_search.search(
                "test query", top_k=5, search_strategy="text_first"
            )

            assert results == text_results
            mock_method.assert_called_once_with("test query", 5)

    @pytest.mark.asyncio
    async def test_search_parallel_strategy(self, hybrid_search):
        """Test search with parallel strategy."""
        combined_results = [
            {"file": "file1.py", "score": 0.9, "content": "result 1"},
            {"file": "file2.py", "score": 0.8, "content": "result 2"},
        ]

        with patch.object(hybrid_search, "_parallel_search", new_callable=AsyncMock) as mock_method:
            mock_method.return_value = combined_results

            results = await hybrid_search.search("test query", top_k=5, search_strategy="parallel")

            assert results == combined_results
            mock_method.assert_called_once_with("test query", 5, 0.6)

    @pytest.mark.asyncio
    async def test_search_unknown_strategy(self, hybrid_search):
        """Test search with unknown strategy returns empty list."""
        results = await hybrid_search.search("test query", top_k=5, search_strategy="unknown")
        assert results == []

    @pytest.mark.asyncio
    async def test_search_exception_handling(self, hybrid_search):
        """Test search handles exceptions gracefully."""
        hybrid_search.semantic_search.search.side_effect = Exception("Search failed")

        results = await hybrid_search.search("test query", top_k=5, search_strategy="combined")

        assert results == []

    @pytest.mark.asyncio
    async def test_merge_and_rank_results(self, hybrid_search):
        """Test merging and ranking of search results."""
        semantic_results = [
            {
                "score": 0.9,
                "metadata": {
                    "file_path": "file1.py",
                    "content_preview": "semantic 1",
                    "file_type": "python",
                },
            },
            {
                "score": 0.8,
                "metadata": {
                    "file_path": "file2.py",
                    "content_preview": "semantic 2",
                    "file_type": "python",
                },
            },
        ]
        text_results = [
            {
                "file": "file1.py",
                "line_number": 1,
                "line": "def test_function(): pass",
                "match": "test",
                "match_start": 4,
                "match_end": 8,
                "matched_text": "test",
                "file_type": "python",
            },
            {
                "file": "file3.py",
                "line_number": 5,
                "line": "class TestClass: pass",
                "match": "test",
                "match_start": 6,
                "match_end": 10,
                "matched_text": "Test",
                "file_type": "python",
            },
        ]

        results = await hybrid_search._merge_and_rank_results(
            semantic_results, text_results, semantic_ratio=0.6
        )

        # Verify results are merged and ranked
        assert len(results) > 0
        assert all("hybrid_metadata" in r for r in results)
        # Results should be sorted by combined score
        scores = [r["hybrid_metadata"]["combined_score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_semantic_first_search_with_fallback(self, hybrid_search):
        """Test semantic_first search falls back to text search when needed."""
        # Mock insufficient semantic results
        semantic_results = [
            {
                "score": 0.9,
                "metadata": {
                    "file_path": "file1.py",
                    "content_preview": "result 1",
                    "file_type": "python",
                },
            },
        ]
        text_results = [
            {
                "file": "file2.py",
                "line_number": 1,
                "line": "def test_function(): pass",
                "match": "test",
                "match_start": 4,
                "match_end": 8,
                "matched_text": "test",
                "file_type": "python",
            },
            {
                "file": "file3.py",
                "line_number": 5,
                "line": "class TestClass: pass",
                "match": "test",
                "match_start": 6,
                "match_end": 10,
                "matched_text": "Test",
                "file_type": "python",
            },
        ]

        hybrid_search.semantic_search.search.return_value = semantic_results
        hybrid_search.text_search.search_files.return_value = text_results

        results = await hybrid_search._semantic_first_search("test query", top_k=3)

        # Should include both semantic and text results
        assert len(results) == 3
        assert results[0]["metadata"]["file_path"] == "file1.py"  # Semantic result first

        # Verify both search methods were called
        hybrid_search.semantic_search.search.assert_called_once()
        hybrid_search.text_search.search_files.assert_called_once()

    @pytest.mark.asyncio
    async def test_text_first_search_with_enhancement(self, hybrid_search):
        """Test text_first search enhances with semantic results."""
        text_results = [
            {
                "file": "file1.py",
                "line_number": 1,
                "line": "def test_function(): pass",
                "match": "test",
                "match_start": 4,
                "match_end": 8,
                "matched_text": "test",
                "file_type": "python",
            },
            {
                "file": "file2.py",
                "line_number": 5,
                "line": "class TestClass: pass",
                "match": "test",
                "match_start": 6,
                "match_end": 10,
                "matched_text": "Test",
                "file_type": "python",
            },
        ]
        semantic_results = [
            {
                "score": 0.9,
                "metadata": {
                    "file_path": "file3.py",
                    "content_preview": "semantic 1",
                    "file_type": "python",
                },
            },
        ]

        hybrid_search.text_search.search_files.return_value = text_results
        hybrid_search.semantic_search.search.return_value = semantic_results

        results = await hybrid_search._text_first_search("test query", top_k=3)

        # Should prioritize text results but include semantic
        assert len(results) == 3
        assert any(r["metadata"]["file_path"] == "file3.py" for r in results)

        # Verify both search methods were called
        hybrid_search.text_search.search_files.assert_called_once()
        hybrid_search.semantic_search.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_parallel_search(self, hybrid_search):
        """Test parallel search executes both searches concurrently."""
        semantic_results = [
            {"file": "file1.py", "score": 0.9, "content": "semantic 1"},
        ]
        text_results = [
            {"file": "file2.py", "score": 0.85, "content": "text 1"},
        ]

        hybrid_search.semantic_search.search.return_value = semantic_results
        hybrid_search.text_search.search_files.return_value = text_results

        # Mock the merge method
        with patch.object(
            hybrid_search, "_merge_and_rank_results", new_callable=AsyncMock
        ) as mock_merge:
            mock_merge.return_value = semantic_results + text_results

            results = await hybrid_search._parallel_search(
                "test query", top_k=5, semantic_ratio=0.7
            )

            assert len(results) == 2
            # Verify both searches were called
            hybrid_search.semantic_search.search.assert_called_once()
            hybrid_search.text_search.search_files.assert_called_once()
            mock_merge.assert_called_once()


class TestHybridSearchIntegration:
    """Integration tests for HybridSearch with real components."""

    @pytest.fixture
    def integration_search(self, tmp_path):
        """Create a HybridSearch instance with minimal real components."""
        config_manager = create_autospec(ConfigurationManager, instance=True)
        config_manager.get_workspace_config = Mock(
            return_value={"search": {"semantic_weight": 0.6, "text_weight": 0.4}}
        )

        # Create test files
        (tmp_path / "test1.py").write_text("def search_function(): pass")
        (tmp_path / "test2.py").write_text("class SearchClass: pass")

        return HybridSearch(tmp_path, config_manager)

    @pytest.mark.asyncio
    async def test_full_search_flow(self, integration_search):
        """Test complete search flow with all strategies."""
        strategies = ["combined", "semantic_first", "text_first", "parallel"]

        for strategy in strategies:
            # Mock the underlying search methods to return predictable results
            integration_search.semantic_search.search = AsyncMock(
                return_value=[{"file": "semantic.py", "score": 0.9, "content": "semantic"}]
            )
            integration_search.text_search.search_files = AsyncMock(
                return_value=[{"file": "text.py", "score": 0.8, "content": "text"}]
            )

            results = await integration_search.search(
                "test query", top_k=5, search_strategy=strategy
            )

            assert isinstance(results, list)
            assert len(results) <= 5

    @pytest.mark.asyncio
    async def test_empty_query_handling(self, integration_search):
        """Test handling of empty queries."""
        integration_search.semantic_search.search = AsyncMock(return_value=[])
        integration_search.text_search.search_files = AsyncMock(return_value=[])

        results = await integration_search.search("", top_k=5)

        assert results == []

    @pytest.mark.asyncio
    async def test_large_result_set_handling(self, integration_search):
        """Test handling of large result sets."""
        # Create many mock results
        large_semantic_results = [
            {"file": f"file{i}.py", "score": 0.9 - i * 0.01, "content": f"content {i}"}
            for i in range(100)
        ]
        large_text_results = [
            {"file": f"text{i}.py", "score": 0.8 - i * 0.01, "content": f"text {i}"}
            for i in range(100)
        ]

        integration_search.semantic_search.search = AsyncMock(return_value=large_semantic_results)
        integration_search.text_search.search_files = AsyncMock(return_value=large_text_results)

        results = await integration_search.search("test", top_k=10, search_strategy="combined")

        assert len(results) == 10
        # Verify results are properly sorted
        scores = [r.get("combined_score", r.get("score", 0)) for r in results]
        assert scores == sorted(scores, reverse=True)


class TestHybridSearchEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def search_with_errors(self, tmp_path):
        """Create a HybridSearch instance that may encounter errors."""
        config_manager = create_autospec(ConfigurationManager, instance=True)
        config_manager.get_workspace_config = Mock(
            return_value={"search": {"semantic_weight": 0.6, "text_weight": 0.4}}
        )
        # Use tmp_path instead of nonexistent path
        return HybridSearch(tmp_path, config_manager)

    @pytest.mark.asyncio
    async def test_semantic_search_failure(self, search_with_errors):
        """Test handling when semantic search fails."""
        search_with_errors.semantic_search.search = AsyncMock(
            side_effect=Exception("Semantic search error")
        )
        search_with_errors.text_search.search_files = AsyncMock(
            return_value=[{"file": "fallback.py", "score": 0.7, "content": "fallback"}]
        )

        # Should fall back gracefully
        results = await search_with_errors.search("test query")
        assert isinstance(results, list)  # Should return empty list on error

    @pytest.mark.asyncio
    async def test_text_search_failure(self, search_with_errors):
        """Test handling when text search fails."""
        search_with_errors.semantic_search.search = AsyncMock(
            return_value=[{"file": "semantic.py", "score": 0.9, "content": "semantic"}]
        )
        search_with_errors.text_search.search_files = AsyncMock(
            side_effect=Exception("Text search error")
        )

        # Should fall back gracefully
        results = await search_with_errors.search("test query")
        assert isinstance(results, list)  # Should return empty list on error

    @pytest.mark.asyncio
    async def test_both_searches_fail(self, search_with_errors):
        """Test handling when both searches fail."""
        search_with_errors.semantic_search.search = AsyncMock(
            side_effect=Exception("Semantic error")
        )
        search_with_errors.text_search.search_files = AsyncMock(side_effect=Exception("Text error"))

        results = await search_with_errors.search("test")
        assert results == []  # Should return empty list when both fail

    @pytest.mark.asyncio
    async def test_invalid_semantic_ratio(self, search_with_errors):
        """Test handling of invalid semantic ratio values."""
        # Test with ratio > 1.0
        results = await search_with_errors.search("test", semantic_ratio=1.5)
        assert isinstance(results, list)

        # Test with ratio < 0.0
        results = await search_with_errors.search("test", semantic_ratio=-0.5)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_duplicate_file_handling(self, tmp_path):
        """Test handling of duplicate files in results."""
        config_manager = create_autospec(ConfigurationManager, instance=True)
        config_manager.get_workspace_config = Mock(
            return_value={"search": {"semantic_weight": 0.6, "text_weight": 0.4}}
        )
        search = HybridSearch(tmp_path, config_manager)

        # Mock results with duplicate files
        semantic_results = [
            {
                "score": 0.9,
                "metadata": {
                    "file_path": "duplicate.py",
                    "content_preview": "semantic content",
                    "file_type": "python",
                },
            }
        ]
        text_results = [
            {
                "file": "duplicate.py",
                "line_number": 1,
                "line": "def test_function(): pass",
                "match": "test",
                "match_start": 4,
                "match_end": 8,
                "matched_text": "test",
                "file_type": "python",
            }
        ]

        search.semantic_search.search = AsyncMock(return_value=semantic_results)
        search.text_search.search_files = AsyncMock(return_value=text_results)

        results = await search.search("test query")

        # Should not have duplicates based on file path
        file_names = [r["metadata"]["file_path"] for r in results]
        assert len(file_names) == len(set(file_names))  # No duplicates in output
