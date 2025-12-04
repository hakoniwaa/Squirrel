"""
Unit tests for coder_mcp.storage.search module.
Tests re-exports and module imports.
"""

import sys
from unittest.mock import patch

import pytest

# Import the module
import coder_mcp.storage.search as search


class TestSearchModule:
    """Test the search module exports."""

    def test_module_imports(self):
        """Test that the module can be imported."""
        assert search is not None
        assert hasattr(search, "__all__")

    def test_all_exports(self):
        """Test that __all__ contains expected exports."""
        expected_exports = [
            "SearchMetrics",
            "CrossEncoderReranker",
        ]

        assert hasattr(search, "__all__")
        assert set(search.__all__) == set(expected_exports)

    def test_search_metrics_available(self):
        """Test that SearchMetrics is available."""
        assert hasattr(search, "SearchMetrics")
        # It should be a class or callable
        assert callable(search.SearchMetrics) or isinstance(search.SearchMetrics, type)

    def test_cross_encoder_reranker_available(self):
        """Test that CrossEncoderReranker is available."""
        assert hasattr(search, "CrossEncoderReranker")
        assert callable(search.CrossEncoderReranker) or isinstance(
            search.CrossEncoderReranker, type
        )

    def test_all_exports_are_accessible(self):
        """Test that all items in __all__ are actually accessible."""
        for item in search.__all__:
            assert hasattr(search, item), f"{item} is in __all__ but not accessible"

    def test_no_unexpected_exports(self):
        """Test that no unexpected items are exported."""
        # Get all public attributes (not starting with _)
        public_attrs = [attr for attr in dir(search) if not attr.startswith("_")]

        # These are expected to be in the module but not necessarily in __all__
        expected_internal = ["metrics", "reranker"]  # Sub-modules might be visible

        # All public attributes should either be in __all__ or be expected internal items
        for attr in public_attrs:
            if attr not in search.__all__ and attr not in expected_internal:
                # Could be a module attribute, check if it's a module
                attr_obj = getattr(search, attr)
                assert hasattr(attr_obj, "__module__"), f"Unexpected public attribute: {attr}"

    @patch("coder_mcp.storage.search.metrics.SearchMetrics")
    @patch("coder_mcp.storage.search.reranker.CrossEncoderReranker")
    def test_imports_from_correct_locations(self, mock_reranker, mock_metrics):
        """Test that imports come from expected locations."""
        # Store original module state
        original_search_module = sys.modules.get("coder_mcp.storage.search")

        try:
            # Force reload to use mocked versions
            if "coder_mcp.storage.search" in sys.modules:
                del sys.modules["coder_mcp.storage.search"]

            import coder_mcp.storage.search as search_reloaded

            # The module should have imported from the mocked locations
            assert search_reloaded.SearchMetrics is mock_metrics
            assert search_reloaded.CrossEncoderReranker is mock_reranker
        finally:
            # Restore original module state
            if original_search_module is not None:
                sys.modules["coder_mcp.storage.search"] = original_search_module
            elif "coder_mcp.storage.search" in sys.modules:
                del sys.modules["coder_mcp.storage.search"]


class TestSearchIntegration:
    """Test integration aspects of the search module."""

    def test_module_structure(self):
        """Test that the module follows expected structure."""
        import inspect

        # Get the module source
        source_file = inspect.getsourcefile(search)
        assert source_file is not None
        assert source_file.endswith("__init__.py")

        # Check module docstring
        assert search.__doc__ is not None
        assert len(search.__doc__.strip()) > 0

    def test_submodule_imports(self):
        """Test that submodules can be imported."""
        try:
            from coder_mcp.storage.search import metrics, reranker

            # Submodules should exist
            assert metrics is not None
            assert reranker is not None
        except ImportError as e:
            pytest.fail(f"Failed to import submodules: {e}")

    def test_module_reexport_pattern(self):
        """Test that this follows the re-export pattern correctly."""
        import inspect

        source = inspect.getsource(search)

        # Should contain import statements
        assert "from .metrics import" in source
        assert "from .reranker import" in source
        assert "__all__" in source

        # Should be concise (re-export modules are typically small)
        line_count = len(source.strip().split("\n"))
        assert line_count < 30, "Re-export module should be concise"

    def test_circular_import_safety(self):
        """Test that there are no circular import issues."""
        # This should not raise ImportError
        try:
            # Try importing in different order
            from coder_mcp.storage.search import SearchMetrics as SM2
            from coder_mcp.storage.search.metrics import SearchMetrics

            # Should be the same classes (both should be real imports, not mocks)
            assert SearchMetrics is SM2
        except ImportError as e:
            pytest.fail(f"Circular import detected: {e}")
