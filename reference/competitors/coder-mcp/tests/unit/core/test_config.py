"""
Unit tests for configuration models.

Tests all dataclasses, validation logic, properties, and methods in core config models.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from coder_mcp.core.config.models import (
    FeatureFlags,
    Limits,
    MCPConfiguration,
    ProviderConfig,
    RedisConfig,
    ServerConfig,
    ServerMeta,
    StorageConfig,
    VectorConfig,
)


class TestRedisConfig:
    """Test RedisConfig dataclass validation and functionality."""

    def test_default_initialization(self):
        """Test default values are set correctly."""
        config = RedisConfig()

        assert config.host == "localhost"
        assert config.port == 6379
        assert config.password is None
        assert config.decode_responses is False
        assert config.socket_timeout == 5
        assert config.socket_connect_timeout == 5
        assert config.retry_on_timeout is True
        assert config.max_connections == 50

    def test_custom_initialization(self):
        """Test initialization with custom values."""
        config = RedisConfig(
            host="redis-server",
            port=6380,
            password="secret",  # pragma: allowlist secret
            decode_responses=True,
            socket_timeout=10,
            max_connections=100,
        )

        assert config.host == "redis-server"
        assert config.port == 6380
        assert config.password == "secret"
        assert config.decode_responses is True
        assert config.socket_timeout == 10
        assert config.max_connections == 100

    @pytest.mark.parametrize("invalid_port", [0, -1, 65536, 100000])
    def test_invalid_port_validation(self, invalid_port):
        """Test port validation rejects invalid values."""
        with pytest.raises(ValueError, match="Invalid Redis port"):
            RedisConfig(port=invalid_port)

    @pytest.mark.parametrize("valid_port", [1, 6379, 65535])
    def test_valid_port_validation(self, valid_port):
        """Test port validation accepts valid values."""
        config = RedisConfig(port=valid_port)
        assert config.port == valid_port

    def test_invalid_max_connections(self):
        """Test max_connections validation."""
        with pytest.raises(ValueError, match="Invalid max_connections"):
            RedisConfig(max_connections=0)

        with pytest.raises(ValueError, match="Invalid max_connections"):
            RedisConfig(max_connections=-5)

    def test_invalid_socket_timeout(self):
        """Test socket_timeout validation."""
        with pytest.raises(ValueError, match="Invalid socket_timeout"):
            RedisConfig(socket_timeout=-1)

    def test_connection_url_without_password(self):
        """Test connection URL generation without password."""
        config = RedisConfig(host="redis-host", port=6380)
        expected = "redis://redis-host:6380"
        assert config.connection_url == expected

    def test_connection_url_with_password(self):
        """Test connection URL generation with password."""
        config = RedisConfig(host="redis-host", port=6380, password="secret")
        expected = "redis://:secret@redis-host:6380"
        assert config.connection_url == expected

    @pytest.mark.parametrize(
        "host,password,expected",
        [
            ("localhost", None, True),
            ("127.0.0.1", None, True),
            ("localhost", "password", False),
            ("127.0.0.1", "password", False),
            ("remote-host", None, False),
            ("remote-host", "password", False),
        ],
    )
    def test_is_local(self, host, password, expected):
        """Test is_local() method logic."""
        config = RedisConfig(host=host, password=password)
        assert config.is_local() == expected


class TestVectorConfig:
    """Test VectorConfig dataclass validation and functionality."""

    def test_default_initialization(self):
        """Test default values are set correctly."""
        config = VectorConfig()

        assert config.index_name == "mcp_vectors"
        assert config.dimension == 3072
        assert config.distance_metric == "COSINE"
        assert config.algorithm == "FLAT"
        assert config.prefix == "mcp:doc:"

    def test_custom_initialization(self):
        """Test initialization with custom values."""
        config = VectorConfig(
            index_name="custom_index",
            dimension=768,
            distance_metric="IP",
            algorithm="HNSW",
            prefix="custom:",
        )

        assert config.index_name == "custom_index"
        assert config.dimension == 768
        assert config.distance_metric == "IP"
        assert config.algorithm == "HNSW"
        assert config.prefix == "custom:"

    @pytest.mark.parametrize("invalid_dimension", [0, -1, -100])
    def test_invalid_dimension_validation(self, invalid_dimension):
        """Test dimension validation rejects invalid values."""
        with pytest.raises(ValueError, match="Invalid vector dimension"):
            VectorConfig(dimension=invalid_dimension)

    @pytest.mark.parametrize("valid_dimension", [1, 256, 768, 3072, 2048])
    def test_valid_dimension_validation(self, valid_dimension):
        """Test dimension validation accepts valid values."""
        config = VectorConfig(dimension=valid_dimension)
        assert config.dimension == valid_dimension

    @pytest.mark.parametrize("invalid_metric", ["INVALID", "euclidean", "manhattan", ""])
    def test_invalid_distance_metric_validation(self, invalid_metric):
        """Test distance metric validation rejects invalid values."""
        with pytest.raises(ValueError, match="Invalid distance metric"):
            VectorConfig(distance_metric=invalid_metric)

    @pytest.mark.parametrize("valid_metric", ["COSINE", "IP", "L2"])
    def test_valid_distance_metric_validation(self, valid_metric):
        """Test distance metric validation accepts valid values."""
        config = VectorConfig(distance_metric=valid_metric)
        assert config.distance_metric == valid_metric

    @pytest.mark.parametrize("invalid_algorithm", ["INVALID", "BruteForce", "LSH", ""])
    def test_invalid_algorithm_validation(self, invalid_algorithm):
        """Test algorithm validation rejects invalid values."""
        with pytest.raises(ValueError, match="Invalid algorithm"):
            VectorConfig(algorithm=invalid_algorithm)

    @pytest.mark.parametrize("valid_algorithm", ["FLAT", "HNSW"])
    def test_valid_algorithm_validation(self, valid_algorithm):
        """Test algorithm validation accepts valid values."""
        config = VectorConfig(algorithm=valid_algorithm)
        assert config.algorithm == valid_algorithm

    def test_empty_index_name_validation(self):
        """Test index name validation rejects empty values."""
        with pytest.raises(ValueError, match="Index name cannot be empty"):
            VectorConfig(index_name="")


class TestStorageConfig:
    """Test StorageConfig dataclass validation and functionality."""

    def test_default_initialization(self):
        """Test default values are set correctly."""
        config = StorageConfig()

        assert config.context_dir == ".mcp"
        assert config.cache_ttl == 86400  # 24 hours
        assert config.max_file_size == 10 * 1024 * 1024  # 10MB
        assert config.max_files_to_index == 1000

    def test_custom_initialization(self):
        """Test initialization with custom values."""
        config = StorageConfig(
            context_dir=".custom",
            cache_ttl=3600,
            max_file_size=5 * 1024 * 1024,
            max_files_to_index=500,
        )

        assert config.context_dir == ".custom"
        assert config.cache_ttl == 3600
        assert config.max_file_size == 5 * 1024 * 1024
        assert config.max_files_to_index == 500

    def test_invalid_cache_ttl_validation(self):
        """Test cache_ttl validation."""
        with pytest.raises(ValueError, match="Invalid cache_ttl"):
            StorageConfig(cache_ttl=-1)

    def test_invalid_max_file_size_validation(self):
        """Test max_file_size validation."""
        with pytest.raises(ValueError, match="Invalid max_file_size"):
            StorageConfig(max_file_size=0)

        with pytest.raises(ValueError, match="Invalid max_file_size"):
            StorageConfig(max_file_size=-1)

    def test_invalid_max_files_to_index_validation(self):
        """Test max_files_to_index validation."""
        with pytest.raises(ValueError, match="Invalid max_files_to_index"):
            StorageConfig(max_files_to_index=0)

        with pytest.raises(ValueError, match="Invalid max_files_to_index"):
            StorageConfig(max_files_to_index=-1)


class TestServerMeta:
    """Test ServerMeta dataclass."""

    def test_default_initialization(self):
        """Test default values are set correctly."""
        meta = ServerMeta()

        assert meta.name == "coder-mcp-server"
        assert meta.version == "1.0.0"

    def test_custom_initialization(self):
        """Test initialization with custom values."""
        meta = ServerMeta(name="custom-server", version="2.0.0")

        assert meta.name == "custom-server"
        assert meta.version == "2.0.0"


class TestProviderConfig:
    """Test ProviderConfig dataclass."""

    def test_default_initialization(self):
        """Test default values are set correctly."""
        config = ProviderConfig()

        assert config.embedding == "openai"
        assert config.vector_store == "redis"
        assert config.cache == "redis"

    def test_custom_initialization(self):
        """Test initialization with custom values."""
        config = ProviderConfig(embedding="local", vector_store="memory", cache="memory")

        assert config.embedding == "local"
        assert config.vector_store == "memory"
        assert config.cache == "memory"


class TestFeatureFlags:
    """Test FeatureFlags dataclass."""

    def test_default_initialization(self):
        """Test default values are set correctly."""
        flags = FeatureFlags()

        assert flags.redis_enabled is True
        assert flags.openai_enabled is True
        assert flags.local_fallback is True

    def test_custom_initialization(self):
        """Test initialization with custom values."""
        flags = FeatureFlags(redis_enabled=False, openai_enabled=False, local_fallback=False)

        assert flags.redis_enabled is False
        assert flags.openai_enabled is False
        assert flags.local_fallback is False


class TestLimits:
    """Test Limits dataclass."""

    def test_default_initialization(self):
        """Test default values are set correctly."""
        limits = Limits()

        assert limits.max_file_size == 10 * 1024 * 1024  # 10 MB
        assert limits.max_files_to_index == 1000
        assert limits.cache_ttl == 3600  # seconds

    def test_custom_initialization(self):
        """Test initialization with custom values."""
        limits = Limits(max_file_size=5 * 1024 * 1024, max_files_to_index=500, cache_ttl=1800)

        assert limits.max_file_size == 5 * 1024 * 1024
        assert limits.max_files_to_index == 500
        assert limits.cache_ttl == 1800


class TestServerConfig:
    """Test ServerConfig dataclass and functionality."""

    def test_default_initialization(self):
        """Test default values are set correctly."""
        config = ServerConfig()

        assert isinstance(config.server, ServerMeta)
        assert isinstance(config.providers, ProviderConfig)
        assert isinstance(config.features, FeatureFlags)
        assert isinstance(config.limits, Limits)
        assert isinstance(config.workspace_root, Path)

    def test_custom_initialization(self):
        """Test initialization with custom values."""
        custom_server = ServerMeta(name="test-server", version="1.5.0")
        custom_providers = ProviderConfig(embedding="local")
        custom_features = FeatureFlags(redis_enabled=False)
        custom_limits = Limits(max_file_size=1024)
        custom_workspace = Path("/tmp/test")

        config = ServerConfig(
            server=custom_server,
            providers=custom_providers,
            features=custom_features,
            limits=custom_limits,
            workspace_root=custom_workspace,
        )

        assert config.server == custom_server
        assert config.providers == custom_providers
        assert config.features == custom_features
        assert config.limits == custom_limits
        assert config.workspace_root == custom_workspace

    def test_name_property(self):
        """Test name property delegates to server.name."""
        config = ServerConfig()
        config.server.name = "custom-name"

        assert config.name == "custom-name"

    def test_version_property(self):
        """Test version property delegates to server.version."""
        config = ServerConfig()
        config.server.version = "2.1.0"

        assert config.version == "2.1.0"


class TestMCPConfiguration:
    """Test MCPConfiguration dataclass and validation."""

    def test_default_initialization(self):
        """Test default values are set correctly."""
        config = MCPConfiguration()

        assert isinstance(config.redis, RedisConfig)
        assert isinstance(config.vector, VectorConfig)
        assert isinstance(config.storage, StorageConfig)
        assert isinstance(config.server, ServerConfig)
        assert config.embedding_provider_type == "openai"
        assert config.vector_store_type == "redis"
        assert config.cache_provider_type == "redis"
        assert config.openai_api_key is None

    def test_custom_initialization(self):
        """Test initialization with custom values."""
        config = MCPConfiguration(
            embedding_provider_type="openai",
            vector_store_type="redis",
            cache_provider_type="redis",
            openai_api_key="test-key",  # pragma: allowlist secret
        )

        assert config.embedding_provider_type == "openai"
        assert config.vector_store_type == "redis"
        assert config.cache_provider_type == "redis"
        assert config.openai_api_key == "test-key"

    @pytest.mark.parametrize("invalid_provider", ["invalid", "huggingface", ""])
    def test_invalid_embedding_provider_validation(self, invalid_provider):
        """Test embedding provider validation."""
        with pytest.raises(ValueError, match="Invalid embedding provider"):
            MCPConfiguration(embedding_provider_type=invalid_provider)

    @pytest.mark.parametrize("valid_provider", ["openai", "local"])
    def test_valid_embedding_provider_validation(self, valid_provider):
        """Test valid embedding provider values."""
        config = MCPConfiguration(embedding_provider_type=valid_provider)
        assert config.embedding_provider_type == valid_provider

    @pytest.mark.parametrize("invalid_store", ["invalid", "postgresql", ""])
    def test_invalid_vector_store_validation(self, invalid_store):
        """Test vector store validation."""
        with pytest.raises(ValueError, match="Invalid vector store type"):
            MCPConfiguration(vector_store_type=invalid_store)

    @pytest.mark.parametrize("valid_store", ["redis", "memory"])
    def test_valid_vector_store_validation(self, valid_store):
        """Test valid vector store values."""
        config = MCPConfiguration(vector_store_type=valid_store)
        assert config.vector_store_type == valid_store

    @pytest.mark.parametrize("invalid_cache", ["invalid", "memcached", ""])
    def test_invalid_cache_provider_validation(self, invalid_cache):
        """Test cache provider validation."""
        with pytest.raises(ValueError, match="Invalid cache provider type"):
            MCPConfiguration(cache_provider_type=invalid_cache)

    @pytest.mark.parametrize("valid_cache", ["redis", "memory"])
    def test_valid_cache_provider_validation(self, valid_cache):
        """Test valid cache provider values."""
        config = MCPConfiguration(cache_provider_type=valid_cache)
        assert config.cache_provider_type == valid_cache

    @patch("coder_mcp.core.config.models.logger")
    def test_openai_warning_when_no_api_key(self, mock_logger):
        """Test warning is logged when OpenAI is selected but no API key provided."""
        MCPConfiguration(embedding_provider_type="openai", openai_api_key=None)

        # Check that the specific OpenAI warning was called
        warning_calls = [call.args[0] for call in mock_logger.warning.call_args_list]
        assert any(
            "OpenAI embedding provider selected but no API key provided" in call
            for call in warning_calls
        )

    @patch("coder_mcp.core.config.models.logger")
    def test_no_warning_when_openai_has_api_key(self, mock_logger):
        """Test no warning when OpenAI is selected with API key."""
        MCPConfiguration(embedding_provider_type="openai", openai_api_key="test-key")

        # Check that the specific OpenAI warning was NOT called
        warning_calls = [call.args[0] for call in mock_logger.warning.call_args_list]
        assert not any(
            "OpenAI embedding provider selected but no API key provided" in call
            for call in warning_calls
        )

    @patch("coder_mcp.core.config.models.logger")
    def test_no_warning_when_local_provider(self, mock_logger):
        """Test no warning when local provider is used."""
        MCPConfiguration(embedding_provider_type="local")

        # Check that the specific OpenAI warning was NOT called
        warning_calls = [call.args[0] for call in mock_logger.warning.call_args_list]
        assert not any(
            "OpenAI embedding provider selected but no API key provided" in call
            for call in warning_calls
        )

    def test_get_summary(self):
        """Test get_summary() returns correct structure."""
        config = MCPConfiguration()
        summary = config.get_summary()

        assert isinstance(summary, dict)
        assert "server" in summary
        assert "providers" in summary
        assert "features" in summary
        assert "limits" in summary

        # Check nested structure
        assert "name" in summary["server"]
        assert "version" in summary["server"]
        assert "embedding" in summary["providers"]
        assert "vector_store" in summary["providers"]
        assert "cache" in summary["providers"]

    @pytest.mark.parametrize(
        "vector_store,cache,expected",
        [
            ("redis", "redis", True),
            ("redis", "memory", True),
            ("memory", "redis", True),
            ("memory", "memory", False),
        ],
    )
    def test_is_redis_required(self, vector_store, cache, expected):
        """Test is_redis_required() logic."""
        config = MCPConfiguration(vector_store_type=vector_store, cache_provider_type=cache)
        assert config.is_redis_required() == expected

    @pytest.mark.parametrize(
        "provider,expected",
        [
            ("openai", True),
            ("local", False),
        ],
    )
    def test_is_openai_required(self, provider, expected):
        """Test is_openai_required() logic."""
        config = MCPConfiguration(embedding_provider_type=provider)
        assert config.is_openai_required() == expected
