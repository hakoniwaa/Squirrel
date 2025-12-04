# Memori Test Suite

This directory contains comprehensive tests for the Memori project, organized into different categories based on their purpose and scope.

## 📁 Test Structure

```
tests/
├── __init__.py              # Test package initialization
├── conftest.py              # Shared pytest fixtures and configuration
├── pytest.ini              # Pytest configuration
├── run_tests.py            # Test runner script
├── README.md               # This file
├── unit/                   # Unit tests
│   ├── test_core_memory.py
│   ├── test_core_database.py
│   ├── test_config_settings.py
│   └── test_utils_pydantic_models.py
├── integration/            # Integration tests
│   ├── test_database_operations.py
│   └── test_llm_integrations.py
├── performance/            # Performance and benchmark tests
│   └── test_memory_performance.py
└── fixtures/               # Test data and utilities
    ├── sample_data.py
    └── test_helpers.py
```

## 🧪 Test Categories

### Unit Tests (`tests/unit/`)
Test individual components in isolation using mocks and fixtures:
- **Core Memory**: Memory management operations
- **Core Database**: Database manager functionality
- **Config Settings**: Configuration and settings validation
- **Pydantic Models**: Data model validation and serialization

### Integration Tests (`tests/integration/`)
Test component interactions and external integrations:
- **Database Operations**: End-to-end database workflows
- **LLM Integrations**: OpenAI, Anthropic, and LiteLLM integrations

### Performance Tests (`tests/performance/`)
Test system performance under various conditions:
- **Memory Performance**: Throughput, latency, and stress testing
- **Benchmark Tests**: Standardized performance measurements

## 🚀 Running Tests

### Quick Start

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run all tests
python tests/run_tests.py

# Run specific test types
python tests/run_tests.py --type unit
python tests/run_tests.py --type integration
python tests/run_tests.py --type performance
```

### Using pytest directly

```bash
# Run all tests with coverage
pytest --cov=memori --cov-report=html

# Run unit tests only
pytest -m unit

# Run integration tests only
pytest -m integration

# Run without slow tests
pytest -m "not slow"

# Run specific test file
pytest tests/unit/test_core_memory.py

# Run with verbose output
pytest -v

# Run in parallel
pytest -n auto
```

### Test Runner Options

The `run_tests.py` script provides convenient options:

```bash
# Run tests with coverage (default)
python tests/run_tests.py --coverage

# Skip slow tests
python tests/run_tests.py --fast

# Run in parallel
python tests/run_tests.py --parallel 4

# Run with custom markers
python tests/run_tests.py --markers "not slow and not requires_network"

# Run specific file
python tests/run_tests.py --file tests/unit/test_core_memory.py

# Run quality checks only
python tests/run_tests.py quality

# Run full CI pipeline
python tests/run_tests.py ci
```

## 🏷️ Test Markers

Tests are marked with the following markers for easy filtering:

- `unit`: Unit tests that test individual components
- `integration`: Integration tests that test component interactions
- `performance`: Performance and benchmark tests
- `slow`: Tests that take a long time to run
- `requires_db`: Tests that require a database connection
- `requires_llm`: Tests that require LLM API access
- `requires_network`: Tests that require network access

### Example Usage

```bash
# Run only fast unit tests
pytest -m "unit and not slow"

# Run integration tests that don't require network
pytest -m "integration and not requires_network"

# Run all tests except performance tests
pytest -m "not performance"
```

## 📊 Coverage Reports

Coverage reports are generated in multiple formats:

- **HTML**: `htmlcov/index.html` - Interactive coverage report
- **Terminal**: Displayed during test execution
- **XML**: `coverage.xml` - For CI/CD integration

### Coverage Configuration

Coverage settings are configured in `pytest.ini`:
- Source: `memori/` package
- Minimum coverage: 80%
- Excludes test files and generated code

## 🔧 Test Configuration

### Pytest Configuration (`pytest.ini`)

Key configuration options:
- Test discovery patterns
- Default command-line options
- Coverage settings
- Warning filters
- Logging configuration

### Shared Fixtures (`conftest.py`)

Common fixtures available to all tests:
- `test_settings`: Test configuration
- `db_manager`: Database manager with in-memory DB
- `memory_manager`: Memory manager instance
- `sample_processed_memory`: Sample memory data
- Mock clients for LLM integrations

## 🧰 Test Utilities

### Sample Data (`fixtures/sample_data.py`)

Provides realistic test data:
- Sample conversations and processed memories
- Large datasets for performance testing
- Various entity types and categories

### Test Helpers (`fixtures/test_helpers.py`)

Utility functions for testing:
- Database setup and teardown
- Mock creation helpers
- Assertion helpers
- Performance measurement utilities

## 🔄 Continuous Integration

### GitHub Actions Integration

Tests are automatically run on:
- Pull requests to main branches
- Push to main branch
- Scheduled runs (security scans)

### Test Matrix

Tests run on multiple configurations:
- **OS**: Ubuntu, Windows, macOS
- **Python**: 3.8, 3.9, 3.10, 3.11, 3.12
- **Database**: SQLite, PostgreSQL (in CI)

## 📝 Writing Tests

### Best Practices

1. **Use descriptive test names** that explain what is being tested
2. **Follow the AAA pattern**: Arrange, Act, Assert
3. **Use appropriate fixtures** from `conftest.py`
4. **Mock external dependencies** to ensure isolation
5. **Test both success and failure cases**
6. **Add appropriate markers** for test categorization

### Example Test Structure

```python
import pytest
from memori.core.memory import MemoryManager

class TestMemoryManager:
    """Test the MemoryManager class."""

    def test_store_memory_success(
        self, memory_manager: MemoryManager, 
        sample_processed_memory: ProcessedMemory
    ):
        """Test successful memory storage."""
        # Arrange
        session_id = "test_session"
        namespace = "test_namespace"
        
        # Act
        memory_id = memory_manager.store_memory(
            processed_memory=sample_processed_memory,
            session_id=session_id,
            namespace=namespace,
        )
        
        # Assert
        assert memory_id is not None
        assert isinstance(memory_id, str)
```

### Adding New Tests

1. **Determine test category** (unit/integration/performance)
2. **Create test file** in appropriate directory
3. **Add necessary imports** and fixtures
4. **Write test classes and methods**
5. **Add appropriate markers**
6. **Update this README** if needed

## 🐛 Debugging Tests

### Common Issues

1. **Database connection errors**: Ensure test database is properly configured
2. **Import errors**: Check that the package is properly installed
3. **Fixture errors**: Verify fixture dependencies in `conftest.py`
4. **Mock issues**: Ensure mocks are properly configured

### Debugging Commands

```bash
# Run with maximum verbosity
pytest -vvv --tb=long

# Run single test with debugging
pytest -vvv --tb=long tests/unit/test_core_memory.py::TestMemoryManager::test_store_memory_success

# Show fixture setup
pytest --fixtures

# Drop into debugger on failure
pytest --pdb

# Show print statements
pytest -s
```

## 📈 Performance Testing

Performance tests are designed to:
- Measure throughput and latency
- Test under concurrent load
- Validate performance with large datasets
- Benchmark critical operations

### Running Performance Tests

```bash
# Run all performance tests
python tests/run_tests.py --type performance

# Run performance tests with benchmarking
pytest -m performance --benchmark-only

# Skip slow performance tests
pytest -m "performance and not slow"
```

## 🔒 Security Testing

Security-focused tests verify:
- Input validation and sanitization
- Error handling without information leakage
- Proper authentication and authorization
- Secure data storage and transmission

Security tests are integrated into the regular test suite and also run as part of the security scanning workflows.

## 📚 Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [pytest-benchmark Documentation](https://pytest-benchmark.readthedocs.io/)
- [Factory Boy Documentation](https://factoryboy.readthedocs.io/)

For questions or issues with the test suite, please check the GitHub issues or create a new one with the `testing` label.