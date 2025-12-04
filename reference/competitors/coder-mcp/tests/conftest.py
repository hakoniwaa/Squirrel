"""
Main pytest configuration and shared fixtures for the test suite.
"""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Generator
from unittest.mock import AsyncMock, Mock

import pytest
import pytest_asyncio
from faker import Faker
from redis import asyncio as aioredis

from coder_mcp.context import ContextManager
from coder_mcp.core.config import ServerConfig
from coder_mcp.core.config.models import FeatureFlags, Limits, ProviderConfig, ServerMeta
from coder_mcp.server import ModularMCPServer
from coder_mcp.storage.providers import OpenAIEmbeddingProvider, RedisVectorStore

# Configure pytest-asyncio
pytest_plugins = ["pytest_asyncio"]

# Initialize Faker for test data generation
fake = Faker()

# ============= Environment Detection =============

# Check if we have a real OpenAI API key
HAS_OPENAI_KEY = bool(
    os.environ.get("OPENAI_API_KEY")
    and os.environ.get("OPENAI_API_KEY") != "test-key-placeholder"
    and os.environ.get("OPENAI_API_KEY") != ""
)

# Check if AI features should be enabled
AI_FEATURES_ENABLED = (
    os.environ.get("AI_FEATURES_ENABLED", "false").lower() == "true" or HAS_OPENAI_KEY
)

# Check if we should skip AI tests
SKIP_AI_TESTS = (
    not AI_FEATURES_ENABLED or os.environ.get("SKIP_AI_TESTS", "false").lower() == "true"
)

# Check if Redis tests should be skipped
SKIP_REDIS_TESTS = os.environ.get("SKIP_REDIS_TESTS", "false").lower() == "true"

# Check if we're in test mode
TEST_MODE = os.environ.get("CODER_MCP_TEST_MODE", "false").lower() == "true"


# ============= Environment Configuration =============


@pytest.fixture(scope="session")
def test_env():
    """Set up test environment variables."""
    os.environ["MCP_TEST_MODE"] = "true"
    os.environ["CODER_MCP_TEST_MODE"] = "true"

    # Set Redis URL if not skipping Redis tests
    if not SKIP_REDIS_TESTS:
        os.environ["REDIS_URL"] = os.getenv("TEST_REDIS_URL", "redis://localhost:6379/15")

    # Only set OpenAI API key if we have a real one
    if HAS_OPENAI_KEY:
        # Key is already in environment from GitHub Actions
        pass
    else:
        # Don't set a fake key - let the config know we don't have one
        os.environ.pop("OPENAI_API_KEY", None)

    yield

    # Cleanup
    os.environ.pop("MCP_TEST_MODE", None)
    os.environ.pop("CODER_MCP_TEST_MODE", None)


# ============= Configuration Fixtures =============


@pytest.fixture
def base_config() -> Dict[str, Any]:
    """Base configuration for tests that respects available services."""
    config = {
        "server": {"name": "test-mcp-server", "version": "1.0.0"},
        "providers": {
            "embedding": "openai" if AI_FEATURES_ENABLED else "local",
            "vector_store": "redis" if not SKIP_REDIS_TESTS else "memory",
            "cache": "redis" if not SKIP_REDIS_TESTS else "memory",
        },
        "features": {
            "redis_enabled": not SKIP_REDIS_TESTS,
            "openai_enabled": AI_FEATURES_ENABLED,
            "local_fallback": True,
        },
        "ai": {
            "enabled": AI_FEATURES_ENABLED,
        },
        "limits": {
            "max_file_size": 1048576,  # 1MB for tests
            "max_files_to_index": 100,
            "cache_ttl": 3600,
        },
    }

    # Add OpenAI API key if available
    if HAS_OPENAI_KEY:
        config["ai"]["openai_api_key"] = os.environ["OPENAI_API_KEY"]

    return config


@pytest.fixture
def server_config(base_config, temp_workspace) -> ServerConfig:
    """Create a ServerConfig instance for tests."""
    # Check if we have a config path from GitHub Actions
    config_path = os.environ.get("CODER_MCP_CONFIG_PATH")
    if config_path and os.path.exists(config_path):
        # Load config from file if available
        import json

        with open(config_path) as f:
            file_config = json.load(f)
            # Merge with base config
            base_config.update(file_config)

    return ServerConfig(
        workspace_root=temp_workspace,
        server=ServerMeta(**base_config["server"]),
        providers=ProviderConfig(**base_config["providers"]),
        features=FeatureFlags(**base_config["features"]),
        limits=Limits(**base_config["limits"]),
    )


# ============= Temporary Directory Fixtures =============


@pytest.fixture
def temp_workspace() -> Generator[Path, None, None]:
    """Create a temporary workspace directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir)
        # Create basic project structure
        (workspace / "src").mkdir()
        (workspace / "tests").mkdir()
        (workspace / "docs").mkdir()

        # Create sample files
        (workspace / "README.md").write_text("# Test Project\n")
        (workspace / "src" / "__init__.py").write_text("")
        (workspace / "src" / "main.py").write_text(
            "def hello_world():\n    return 'Hello, World!'\n"
        )

        yield workspace


# ============= Redis Fixtures =============


@pytest_asyncio.fixture
async def redis_client() -> AsyncGenerator[aioredis.Redis, None]:
    """Create an async Redis client for tests."""
    if SKIP_REDIS_TESTS:
        pytest.skip("Redis tests are disabled")

    try:
        client = await aioredis.from_url(
            os.getenv("TEST_REDIS_URL", "redis://localhost:6379/15"), decode_responses=True
        )

        # Test connection
        await client.ping()

        # Clear test database
        await client.flushdb()

        yield client

        # Cleanup
        await client.flushdb()
        await client.aclose()
    except Exception as e:
        pytest.skip(f"Redis not available: {e}")


@pytest.fixture
def mock_redis_client() -> AsyncMock:
    """Create a mock Redis client."""
    mock = AsyncMock(spec=aioredis.Redis)
    mock.ping.return_value = True
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = 1
    mock.exists.return_value = 0
    return mock


# ============= Provider Fixtures =============


@pytest.fixture
def mock_embedding_provider() -> Mock:
    """Create a mock embedding provider."""
    provider = Mock()
    provider.embed.return_value = [0.1] * 3072  # Standard embedding size
    provider.embed_batch.return_value = [[0.1] * 3072] * 10
    return provider


@pytest_asyncio.fixture
async def real_embedding_provider() -> OpenAIEmbeddingProvider:
    """Create a real embedding provider (requires API key)."""
    if not HAS_OPENAI_KEY:
        pytest.skip("OpenAI API key not available")

    return OpenAIEmbeddingProvider(api_key=os.environ["OPENAI_API_KEY"])


# ============= Storage Fixtures =============


@pytest_asyncio.fixture
async def vector_store(redis_client, mock_embedding_provider) -> RedisVectorStore:
    """Create a vector store instance."""
    if SKIP_REDIS_TESTS:
        pytest.skip("Redis tests are disabled")

    store = RedisVectorStore(
        redis_client=redis_client,
        embedding_provider=mock_embedding_provider,
        index_name="test_index",
    )
    await store.initialize()
    return store


@pytest.fixture
def mock_vector_store() -> Mock:
    """Create a mock vector store."""
    store = Mock()
    store.search.return_value = []
    store.add_documents.return_value = True
    store.delete_documents.return_value = True
    return store


# ============= Context Manager Fixtures =============


@pytest_asyncio.fixture
async def context_manager(server_config, mock_redis_client) -> ContextManager:
    """Create a ContextManager instance for tests."""
    # Use mock Redis if Redis tests are disabled
    if SKIP_REDIS_TESTS:
        # Inject mock Redis client
        manager = ContextManager(server_config)
        # TODO: Replace Redis client with mock when the interface allows it
        return manager
    else:
        return ContextManager(server_config)


@pytest_asyncio.fixture
async def initialized_context_manager(context_manager) -> ContextManager:
    """Create an initialized ContextManager with indexed files."""
    # ContextManager is already initialized in its constructor
    return context_manager


# ============= MCP Server Fixtures =============


@pytest_asyncio.fixture
async def mcp_server(server_config) -> ModularMCPServer:
    """Create an MCP server instance for tests."""
    server = ModularMCPServer(server_config.workspace_root)
    await server.initialize()
    return server


@pytest.fixture
def mock_mcp_server() -> Mock:
    """Create a mock MCP server."""
    server = Mock(spec=ModularMCPServer)
    server.handle_tool_call = AsyncMock()
    server.get_tools.return_value = []
    return server


# ============= Test Data Fixtures =============


@pytest.fixture
def sample_python_code() -> str:
    """Sample Python code for testing."""
    return """
import asyncio
from typing import List, Optional

class SampleClass:
    def __init__(self, name: str):
        self.name = name
        self.items: List[str] = []

    async def process_items(self, items: List[str]) -> Optional[str]:
        \"\"\"Process a list of items asynchronously.\"\"\"
        if not items:
            return None

        results = []
        for item in items:
            result = await self._process_single_item(item)
            results.append(result)

        return ", ".join(results)

    async def _process_single_item(self, item: str) -> str:
        # Simulate async processing
        await asyncio.sleep(0.1)
        return item.upper()

def calculate_complexity(code: str) -> int:
    \"\"\"Calculate cyclomatic complexity of code.\"\"\"
    complexity = 1
    for line in code.split('\\n'):
        if any(keyword in line for keyword in ['if', 'elif', 'for', 'while', 'except']):
            complexity += 1
    return complexity
"""


@pytest.fixture
def sample_project_structure() -> Dict[str, str]:
    """Sample project file structure for testing."""
    return {
        "src/__init__.py": "",
        "src/main.py": "def main():\n    print('Hello')\n",
        "src/utils.py": "def helper():\n    return 42\n",
        "src/models.py": "class User:\n    pass\n",
        "tests/test_main.py": "def test_main():\n    assert True\n",
        "README.md": "# Test Project\nA sample project for testing.",
        "pyproject.toml": "[tool.poetry]\nname = 'test-project'\n",
    }


# ============= Async Test Helpers =============


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def async_timeout():
    """Helper fixture for testing timeouts."""

    async def _timeout(seconds: float):
        await asyncio.sleep(seconds)
        raise asyncio.TimeoutError(f"Test timeout after {seconds} seconds")

    return _timeout


# ============= Performance Testing Fixtures =============


@pytest.fixture
def performance_monitor():
    """Monitor performance metrics during tests."""
    import time

    class PerformanceMonitor:
        def __init__(self):
            self.metrics = {}

        def start(self, operation: str):
            self.metrics[operation] = {"start": time.perf_counter()}

        def end(self, operation: str):
            if operation in self.metrics:
                self.metrics[operation]["end"] = time.perf_counter()
                self.metrics[operation]["duration"] = (
                    self.metrics[operation]["end"] - self.metrics[operation]["start"]
                )

        def get_duration(self, operation: str) -> float:
            return self.metrics.get(operation, {}).get("duration", 0)

    return PerformanceMonitor()


# ============= Cleanup Fixtures =============


@pytest_asyncio.fixture(autouse=True)
async def cleanup_after_test():
    """Automatic cleanup after each test."""
    yield
    # Add any global cleanup logic here
    # For example, clearing caches, closing connections, etc.


# ============= Markers and Hooks =============


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "redis: marks tests that require Redis")
    config.addinivalue_line("markers", "unit: marks unit tests")
    config.addinivalue_line("markers", "e2e: marks end-to-end tests")
    config.addinivalue_line("markers", "performance: marks performance tests")
    config.addinivalue_line("markers", "openai: marks tests that require OpenAI API")
    config.addinivalue_line("markers", "requires_openai: marks tests that require OpenAI API")
    config.addinivalue_line("markers", "benchmark: marks performance benchmark tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers and skip tests based on environment."""
    # Skip markers
    skip_openai = pytest.mark.skip(reason="OpenAI API key not available")
    skip_redis = pytest.mark.skip(reason="Redis not available or tests disabled")

    for item in items:
        # Add markers based on test file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)

        # Skip tests based on environment
        if SKIP_AI_TESTS:
            if "openai" in item.keywords or "requires_openai" in item.keywords:
                item.add_marker(skip_openai)

        if SKIP_REDIS_TESTS:
            if "redis" in item.keywords:
                item.add_marker(skip_redis)


# ============= Configuration Override =============

# Override configuration loading if needed
if TEST_MODE:
    import coder_mcp.core.config

    # Store original function
    _original_load_config = getattr(coder_mcp.core.config, "load_config", None)

    def _test_load_config(*args, **kwargs):
        """Load test configuration that respects environment."""
        # Check for GitHub Actions config
        config_path = os.environ.get("CODER_MCP_CONFIG_PATH")
        if config_path and os.path.exists(config_path):
            import json

            with open(config_path) as f:
                return json.load(f)

        # Otherwise return a safe test config
        return {
            "server": {"name": "test-server", "version": "1.0.0"},
            "ai": {"enabled": AI_FEATURES_ENABLED},
            "providers": {
                "embedding": "openai" if AI_FEATURES_ENABLED else "local",
                "vector_store": "redis" if not SKIP_REDIS_TESTS else "memory",
                "cache": "redis" if not SKIP_REDIS_TESTS else "memory",
            },
            "features": {
                "smart_analysis": {"enabled": AI_FEATURES_ENABLED},
                "semantic_search": {"enabled": AI_FEATURES_ENABLED},
            },
            "security": {
                "rate_limit_enabled": False,
                "cache_enabled": False,
            },
        }

    # Replace the function if it exists
    if _original_load_config:
        coder_mcp.core.config.load_config = _test_load_config
