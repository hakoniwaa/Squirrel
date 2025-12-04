"""
Unit tests for coder_mcp.storage.embeddings.providers module.
Tests re-exports and module imports.
"""

import sys
from unittest.mock import patch

# Import the module
import coder_mcp.storage.embeddings.providers as providers


class TestProvidersModule:
    """Test the providers module exports."""

    def test_module_imports(self):
        """Test that the module can be imported."""
        assert providers is not None
        assert hasattr(providers, "__all__")

    def test_all_exports(self):
        """Test that __all__ contains expected exports."""
        expected_exports = [
            "EmbeddingProvider",
            "OpenAIEmbeddingProvider",
            "LocalEmbeddingProvider",
            "CodeEmbeddingProvider",
        ]

        assert hasattr(providers, "__all__")
        assert set(providers.__all__) == set(expected_exports)

    def test_embedding_provider_available(self):
        """Test that EmbeddingProvider is available."""
        assert hasattr(providers, "EmbeddingProvider")
        # It should be a class or callable
        assert callable(providers.EmbeddingProvider) or isinstance(
            providers.EmbeddingProvider, type
        )

    def test_openai_embedding_provider_available(self):
        """Test that OpenAIEmbeddingProvider is available."""
        assert hasattr(providers, "OpenAIEmbeddingProvider")
        assert callable(providers.OpenAIEmbeddingProvider) or isinstance(
            providers.OpenAIEmbeddingProvider, type
        )

    def test_local_embedding_provider_available(self):
        """Test that LocalEmbeddingProvider is available."""
        assert hasattr(providers, "LocalEmbeddingProvider")
        assert callable(providers.LocalEmbeddingProvider) or isinstance(
            providers.LocalEmbeddingProvider, type
        )

    def test_code_embedding_provider_available(self):
        """Test that CodeEmbeddingProvider is available."""
        assert hasattr(providers, "CodeEmbeddingProvider")
        assert callable(providers.CodeEmbeddingProvider) or isinstance(
            providers.CodeEmbeddingProvider, type
        )

    def test_all_exports_are_accessible(self):
        """Test that all items in __all__ are actually accessible."""
        for item in providers.__all__:
            assert hasattr(providers, item), f"{item} is in __all__ but not accessible"

    def test_no_unexpected_exports(self):
        """Test that no unexpected items are exported."""
        # Get all public attributes (not starting with _)
        public_attrs = [attr for attr in dir(providers) if not attr.startswith("_")]

        # These are expected to be in the module but not necessarily in __all__
        expected_internal = []

        # All public attributes should either be in __all__ or be expected internal items
        for attr in public_attrs:
            assert (
                attr in providers.__all__ or attr in expected_internal
            ), f"Unexpected public attribute: {attr}"

    @patch("coder_mcp.storage.providers.EmbeddingProvider")
    @patch("coder_mcp.storage.providers.LocalEmbeddingProvider")
    @patch("coder_mcp.storage.providers.OpenAIEmbeddingProvider")
    @patch("coder_mcp.storage.embeddings.multi_model.CodeEmbeddingProvider")
    def test_imports_from_correct_locations(self, mock_code, mock_openai, mock_local, mock_base):
        """Test that imports come from expected locations."""
        # This test verifies the import structure by mocking the dependencies
        # The fact that we can patch these paths confirms the import structure

        # Force reload to use mocked versions
        if "coder_mcp.storage.embeddings.providers" in sys.modules:
            del sys.modules["coder_mcp.storage.embeddings.providers"]

        import coder_mcp.storage.embeddings.providers as providers_reloaded

        # The module should have imported from the mocked locations
        assert providers_reloaded.EmbeddingProvider is mock_base
        assert providers_reloaded.LocalEmbeddingProvider is mock_local
        assert providers_reloaded.OpenAIEmbeddingProvider is mock_openai
        assert providers_reloaded.CodeEmbeddingProvider is mock_code


class TestProviderIntegration:
    """Test integration with the actual provider classes."""

    def test_provider_inheritance(self):
        """Test that providers follow expected inheritance patterns."""
        # Base provider should be a class
        assert isinstance(providers.EmbeddingProvider, type)

        # Other providers should inherit from or relate to base provider
        # Note: We're testing the module structure, not the actual class inheritance
        # since that's tested in the provider class tests
        assert isinstance(providers.OpenAIEmbeddingProvider, type)
        assert isinstance(providers.LocalEmbeddingProvider, type)
        assert isinstance(providers.CodeEmbeddingProvider, type)

    def test_module_reexport_pattern(self):
        """Test that this follows the re-export pattern correctly."""
        # The module should be relatively small since it's just re-exports
        import inspect

        source = inspect.getsource(providers)

        # Should contain import statements
        assert "from" in source
        assert "import" in source
        assert "__all__" in source

        # Should be concise (re-export modules are typically small)
        line_count = len(source.strip().split("\n"))
        assert line_count < 50, "Re-export module should be concise"
