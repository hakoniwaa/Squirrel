"""
Example usage tests for the mock utilities.

These examples demonstrate practical usage patterns for the mock utilities
in real testing scenarios. Use these as reference for your own tests.
"""

import json
import random
import time

import pytest
import pytest_asyncio

from tests.helpers.mocks import (
    create_full_mock_suite,
    create_indexed_context_manager,
    create_mock_context_manager,
    create_mock_embedding_provider,
    create_mock_openai_client,
    create_mock_redis,
    create_mock_server,
    create_mock_vector_store,
    create_populated_redis,
)


class TestBasicUsageExamples:
    """Basic usage examples for individual mocks."""

    @pytest.mark.asyncio
    async def test_mock_server_basic_usage(self):
        """Example: Basic server testing."""
        # Create and initialize mock server
        server = create_mock_server()
        await server.initialize()

        # Test file operations
        read_result = await server.handle_tool_call("read_file", {"path": "config.py"})
        assert read_result["content"] == "mock file content"

        write_result = await server.handle_tool_call(
            "write_file", {"path": "output.txt", "content": "Hello, World!"}
        )
        assert write_result["success"] is True

        # Check call tracking
        assert server.call_count == 2
        assert server.last_call_time is not None

    @pytest.mark.asyncio
    async def test_mock_redis_basic_usage(self):
        """Example: Basic Redis testing."""
        # Create Redis with initial data
        redis = create_mock_redis(
            {"user:1": json.dumps({"name": "Alice", "role": "admin"}), "session:abc123": "active"}
        )

        # Test basic operations
        user_data = await redis.get("user:1")
        user_info = json.loads(user_data)
        assert user_info["name"] == "Alice"

        # Test hash operations
        await redis.hset("preferences", "theme", "dark")
        await redis.hset("preferences", "language", "en")

        prefs = await redis.hgetall("preferences")
        assert prefs["theme"] == "dark"
        assert prefs["language"] == "en"

    @pytest.mark.asyncio
    async def test_mock_context_manager_basic_usage(self):
        """Example: Basic context manager testing."""
        cm = create_mock_context_manager()

        # Index some files
        await cm.index_file(
            "main.py",
            """
def main():
    print("Hello, World!")
    return 0
""",
        )

        await cm.index_file(
            "utils.py",
            """
def helper_function(data):
    return data.upper()
""",
        )

        # Search for content
        results = await cm.search_similar("function")
        assert len(results) == 1  # Only utils.py contains "function"

        # Verify result structure
        result = results[0]
        assert result["file"] == "utils.py"
        assert "snippet" in result
        assert "similarity" in result

    @pytest.mark.asyncio
    async def test_mock_openai_basic_usage(self):
        """Example: Basic OpenAI client testing."""
        client = create_mock_openai_client()

        # Test embeddings
        embedding_result = await client.create_embedding("test document")
        assert len(embedding_result["data"][0]["embedding"]) == 1536

        # Test chat completion
        chat_result = await client.create_chat_completion(
            [{"role": "user", "content": "Explain this error message"}]
        )

        response = chat_result["choices"][0]["message"]["content"]
        assert "debug" in response.lower()

        # Check usage stats
        stats = client.get_usage_stats()
        assert stats["embedding_requests"] == 1
        assert stats["chat_requests"] == 1


class TestAdvancedUsageExamples:
    """Advanced usage examples with custom configurations."""

    @pytest.mark.asyncio
    async def test_custom_tool_handlers(self):
        """Example: Adding custom tool handlers to mock server."""
        server = create_mock_server()
        await server.initialize()

        # Add custom tool that uses external data
        test_data = {"projects": ["project1", "project2"], "status": "active"}

        async def get_projects_tool(args):
            return {
                "projects": test_data["projects"],
                "count": len(test_data["projects"]),
                "status": test_data["status"],
            }

        server.tool_handlers.handlers["get_projects"] = get_projects_tool

        # Test custom tool
        result = await server.handle_tool_call("get_projects", {})
        assert result["count"] == 2
        assert "project1" in result["projects"]

    @pytest.mark.asyncio
    async def test_redis_with_expiry_simulation(self):
        """Example: Testing Redis expiry behavior."""
        redis = create_mock_redis()

        # Set keys with different expiry times
        await redis.set("temp_session", "session_data", ex=60)
        await redis.set("cache_key", "cached_data", ex=3600)
        await redis.set("permanent_key", "permanent_data")

        # Test TTL
        temp_ttl = await redis.ttl("temp_session")
        cache_ttl = await redis.ttl("cache_key")
        perm_ttl = await redis.ttl("permanent_key")

        assert 0 < temp_ttl <= 60
        assert 0 < cache_ttl <= 3600
        assert perm_ttl == -1  # No expiry

    @pytest.mark.asyncio
    async def test_embedding_with_vector_store_workflow(self):
        """Example: Complete embedding and search workflow."""
        provider = create_mock_embedding_provider()
        store = create_mock_vector_store()

        # Simulate indexing documents
        documents = [
            {"id": "doc1", "text": "Python programming tutorial", "category": "tutorial"},
            {"id": "doc2", "text": "Machine learning with Python", "category": "ml"},
            {"id": "doc3", "text": "Web development using Flask", "category": "web"},
            {"id": "doc4", "text": "Data analysis with pandas", "category": "data"},
        ]

        # Create embeddings and store them
        for doc in documents:
            embedding = await provider.create_embedding(doc["text"])
            await store.add_vector(
                doc["id"], embedding, {"text": doc["text"], "category": doc["category"]}
            )

        # Search for Python-related content
        query_embedding = await provider.create_embedding("Python programming")
        results = await store.search_similar(query_embedding, top_k=3, threshold=-1.0)

        # Should find Python-related documents
        assert len(results) > 0

        # Verify result structure
        for result in results:
            assert "id" in result
            assert "similarity" in result
            assert "metadata" in result
            assert "text" in result["metadata"]

    @pytest.mark.asyncio
    async def test_contextual_chat_responses(self):
        """Example: Testing context-aware chat responses."""
        client = create_mock_openai_client()

        # Test different conversation contexts
        test_scenarios = [
            {
                "context": "debugging",
                "message": "I'm getting a TypeError in my Python code",
                "expected_keywords": ["debug", "error"],
            },
            {
                "context": "explanation",
                "message": "Can you explain how async/await works?",
                "expected_keywords": ["explain", "step"],
            },
            {
                "context": "code_example",
                "message": "Write code to calculate fibonacci numbers",
                "expected_keywords": ["python", "implementation", "example"],
            },
        ]

        for scenario in test_scenarios:
            result = await client.create_chat_completion(
                [{"role": "user", "content": scenario["message"]}]
            )

            response_content = result["choices"][0]["message"]["content"].lower()

            # Check that response contains expected keywords
            found_keywords = [kw for kw in scenario["expected_keywords"] if kw in response_content]
            assert len(found_keywords) > 0, (
                f"No expected keywords found in response for {scenario['context']}. "
                f"Response was: {response_content}"
            )


class TestIntegrationExamples:
    """Examples of using multiple mocks together."""

    @pytest.mark.asyncio
    async def test_complete_ai_analysis_workflow(self):
        """Example: Complete AI-powered code analysis workflow."""
        # Setup all components
        server = create_mock_server()
        redis = create_mock_redis()
        context_manager = create_mock_context_manager()
        openai_client = create_mock_openai_client()

        await server.initialize()

        # Simulate code analysis workflow
        code_content = """
def calculate_metrics(data):
    if not data:
        return None

    total = sum(data)
    count = len(data)
    average = total / count

    return {
        'total': total,
        'count': count,
        'average': average
    }
"""

        # 1. Index the code file
        await context_manager.index_file("metrics.py", code_content)

        # 2. Store analysis results in Redis
        analysis_key = "analysis:metrics.py"
        analysis_data = {
            "complexity": 3,
            "quality_score": 8.5,
            "issues": ["Missing type hints", "No docstring"],
            "last_analyzed": "2024-01-01T12:00:00Z",
        }
        await redis.set(analysis_key, json.dumps(analysis_data))

        # 3. Get AI analysis
        ai_response = await openai_client.create_chat_completion(
            [{"role": "user", "content": f"Analyze this code:\n{code_content}"}]
        )

        # 4. Verify workflow
        assert context_manager.indexed_files["metrics.py"]["content"] == code_content

        stored_analysis = await redis.get(analysis_key)
        stored_data = json.loads(stored_analysis)
        assert stored_data["quality_score"] == 8.5

        ai_analysis = ai_response["choices"][0]["message"]["content"]
        assert len(ai_analysis) > 0

    @pytest.mark.asyncio
    async def test_caching_and_performance_optimization(self):
        """Example: Testing caching mechanisms."""
        redis = create_mock_redis()
        embedding_provider = create_mock_embedding_provider()

        # Simulate expensive operations with caching
        cache_key = "embedding:expensive_query"
        query_text = "complex machine learning algorithm optimization"

        # Check cache first
        cached_result = await redis.get(cache_key)

        if cached_result:
            # Use cached embedding
            embedding = json.loads(cached_result)
        else:
            # Generate new embedding and cache it
            embedding = await embedding_provider.create_embedding(query_text)
            await redis.set(cache_key, json.dumps(embedding), ex=3600)

        # Verify caching worked
        assert len(embedding) == 1536

        # Second call should use cache
        cached_embedding_str = await redis.get(cache_key)
        cached_embedding = json.loads(cached_embedding_str)
        assert cached_embedding == embedding

    @pytest.mark.asyncio
    async def test_error_handling_and_fallbacks(self):
        """Example: Testing error handling and fallback mechanisms."""
        server = create_mock_server()
        redis = create_mock_redis()

        await server.initialize()

        # Add a tool that might fail and fallback to Redis
        async def unreliable_tool(args):
            # Simulate 30% failure rate
            if random.random() < 0.3:
                raise Exception("Service temporarily unavailable")
            return {"result": "success", "data": args.get("data", "")}

        async def fallback_tool(args):
            # Use Redis as fallback storage
            fallback_key = f"fallback:{args.get('operation', 'default')}"
            cached_result = await redis.get(fallback_key)

            if cached_result:
                return {"result": "fallback", "data": cached_result}
            else:
                # Store fallback data
                fallback_data = "fallback_value"
                await redis.set(fallback_key, fallback_data)
                return {"result": "fallback", "data": fallback_data}

        server.tool_handlers.handlers["unreliable_operation"] = unreliable_tool
        server.tool_handlers.handlers["fallback_operation"] = fallback_tool

        # Test fallback mechanism
        try:
            result = await server.handle_tool_call("unreliable_operation", {"data": "test"})
            assert result["result"] == "success"
        except Exception:
            # Use fallback
            result = await server.handle_tool_call("fallback_operation", {"operation": "test"})
            assert result["result"] == "fallback"


class TestPresetConfigurationExamples:
    """Examples using preset mock configurations."""

    @pytest.mark.asyncio
    async def test_populated_redis_usage(self):
        """Example: Using pre-populated Redis mock."""
        redis = create_populated_redis()

        # Access pre-loaded user data
        user_data = await redis.get("user:123")
        user_info = json.loads(user_data)
        assert user_info["name"] == "Test User"
        assert user_info["email"] == "test@example.com"

        # Access session data
        session_status = await redis.get("session:abc")
        assert session_status == "active"

        # Access configuration
        config_data = await redis.get("config:app")
        config = json.loads(config_data)
        assert config["debug"] is True
        assert config["version"] == "1.0.0"

    def test_full_mock_suite_usage(self):
        """Example: Using the complete mock suite."""
        suite = create_full_mock_suite()

        # Access all components
        server = suite["server"]
        redis = suite["redis"]
        context_manager = suite["context_manager"]
        openai = suite["openai"]
        embedding_provider = suite["embedding_provider"]
        vector_store = suite["vector_store"]

        # Verify all components are properly initialized
        assert not server.is_initialized  # Needs explicit initialization
        assert len(redis._data) == 0  # Empty by default
        assert context_manager.project_info["name"] == "test-project"
        assert openai.usage_stats["total_tokens"] == 0
        assert embedding_provider.dimensions == 1536
        assert vector_store.dimensions == 1536

    @pytest.mark.asyncio
    async def test_realistic_testing_scenario(self):
        """Example: Realistic end-to-end testing scenario."""
        # Setup: Create a realistic testing environment
        server = create_mock_server()
        redis = create_populated_redis()
        context_manager = create_indexed_context_manager()
        openai = create_mock_openai_client()

        await server.initialize()

        # Scenario: User requests code analysis
        user_request = {
            "action": "analyze_project",
            "project_path": "/workspace/my-project",
            "focus": "quality",
        }

        # 1. Get project context
        context = await context_manager.get_context("project analysis", max_results=10)
        assert context["query"] == "project analysis"

        # 2. Check if analysis is cached
        cache_key = f"analysis:{user_request['project_path']}"
        cached_analysis = await redis.get(cache_key)

        if not cached_analysis:
            # 3. Perform AI analysis
            ai_prompt = f"Analyze project quality for: {user_request['focus']}"
            ai_response = await openai.create_chat_completion(
                [{"role": "user", "content": ai_prompt}]
            )

            analysis_result = {
                "quality_score": 8.2,
                "issues_found": 3,
                "recommendations": ai_response["choices"][0]["message"]["content"],
                "timestamp": "2024-01-01T12:00:00Z",
            }

            # 4. Cache the analysis
            await redis.set(cache_key, json.dumps(analysis_result), ex=3600)
        else:
            analysis_result = json.loads(cached_analysis)

        # 5. Simulate returning results through server
        async def analysis_tool(args):
            return analysis_result

        server.tool_handlers.handlers["analyze_project"] = analysis_tool

        # 6. Execute the complete workflow
        final_result = await server.handle_tool_call("analyze_project", user_request)

        # Verify the complete workflow
        assert final_result["quality_score"] == 8.2
        assert final_result["issues_found"] == 3
        assert "recommendations" in final_result

        # Verify caching worked
        cached_data = await redis.get(cache_key)
        assert cached_data is not None


class TestFixtureExamples:
    """Examples of using mocks as pytest fixtures."""

    @pytest_asyncio.fixture
    async def mock_server_fixture(self):
        """Fixture providing an initialized mock server."""
        server = create_mock_server()
        await server.initialize()
        yield server  # Properly yield the server instead of returning a generator

    @pytest.fixture
    def redis_with_test_data(self):
        """Example fixture for Redis with test data."""
        test_data = {
            "test:key1": "value1",
            "test:key2": "value2",
            "config:test": json.dumps({"env": "test", "debug": True}),
        }
        return create_mock_redis(test_data)

    @pytest.fixture
    def complete_mock_environment(self):
        """Example fixture for complete mock environment."""
        return create_full_mock_suite()

    @pytest.mark.asyncio
    async def test_using_server_fixture(self, mock_server_fixture):
        """Example: Using server fixture in tests."""
        server = mock_server_fixture

        # Server should already be initialized
        assert server.is_initialized

        # Test basic functionality
        result = await server.handle_tool_call("read_file", {"path": "test.py"})
        assert result["content"] == "mock file content"

    @pytest.mark.asyncio
    async def test_using_redis_fixture(self, redis_with_test_data):
        """Example: Using Redis fixture in tests."""
        redis = redis_with_test_data

        # Test data should be pre-loaded
        value = await redis.get("test:key1")
        assert value == "value1"

        config_str = await redis.get("config:test")
        config = json.loads(config_str)
        assert config["env"] == "test"

    def test_using_complete_environment(self, complete_mock_environment):
        """Example: Using complete mock environment fixture."""
        env = complete_mock_environment

        # All components should be available
        assert "server" in env
        assert "redis" in env
        assert "openai" in env

        # Can customize any component
        env["server"].health_status = "testing"
        assert env["server"].health_status == "testing"


@pytest.mark.asyncio
async def test_performance_testing_example():
    """Example: Using mocks for performance testing."""
    provider = create_mock_embedding_provider()

    # Test batch embedding performance
    large_text_batch = [f"Document {i} with some content" for i in range(100)]

    start_time = time.time()
    embeddings = await provider.create_embeddings(large_text_batch)
    end_time = time.time()

    # Verify results
    assert len(embeddings) == 100
    assert all(len(emb) == 1536 for emb in embeddings)

    # Mock should be fast (much faster than real API)
    elapsed_time = end_time - start_time
    assert elapsed_time < 1.0  # Should complete in under 1 second

    # Check caching effectiveness
    stats = provider.get_stats()
    assert stats["cached_embeddings"] == 100
    assert stats["total_calls"] == 1  # Only one batch call


@pytest.mark.asyncio
async def test_error_simulation_example():
    """Example: Simulating and testing error conditions."""
    server = create_mock_server()
    await server.initialize()

    # Add a tool that simulates different error conditions
    error_scenarios = ["network_error", "timeout", "invalid_input", "success"]
    current_scenario = 0

    async def error_prone_tool(args):
        nonlocal current_scenario
        scenario = error_scenarios[current_scenario % len(error_scenarios)]
        current_scenario += 1

        if scenario == "network_error":
            raise ConnectionError("Network unreachable")
        elif scenario == "timeout":
            raise TimeoutError("Operation timed out")
        elif scenario == "invalid_input":
            raise ValueError("Invalid input provided")
        else:
            return {"status": "success", "data": args}

    server.tool_handlers.handlers["error_test"] = error_prone_tool

    # Test different error scenarios
    with pytest.raises(ConnectionError):
        await server.handle_tool_call("error_test", {})

    with pytest.raises(TimeoutError):
        await server.handle_tool_call("error_test", {})

    with pytest.raises(ValueError):
        await server.handle_tool_call("error_test", {})

    # Success case
    result = await server.handle_tool_call("error_test", {"input": "valid"})
    assert result["status"] == "success"
