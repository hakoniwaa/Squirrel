# MCP Server Test Suite - Quick Start Guide

## 🚀 Quick Start

### 1. Install Dependencies
```bash
# Install all dependencies including test dependencies
poetry install --with test,dev

# Install pre-commit hooks
poetry run pre-commit install
```

### 2. Run Tests
```bash
# Run all tests
make test

# Run specific test types
make test-unit          # Unit tests only
make test-integration   # Integration tests
make test-e2e          # End-to-end tests
make test-performance  # Performance benchmarks

# Run tests in watch mode (auto-rerun on changes)
make test-watch

# Run tests for specific file
poetry run pytest tests/unit/test_context_manager.py -v
```

### 3. Check Coverage
```bash
# Generate coverage report
make coverage

# View coverage in browser
open reports/coverage/index.html
```

## 📊 Test Suite Overview

### Test Categories

1. **Unit Tests** (`tests/unit/`)
   - Fast, isolated tests for individual components
   - No external dependencies (uses mocks)
   - Target: >90% coverage
   - Runtime: <10ms per test

2. **Integration Tests** (`tests/integration/`)
   - Tests component interactions
   - Uses real Redis, mock OpenAI
   - Target: >80% coverage
   - Runtime: <100ms per test

3. **End-to-End Tests** (`tests/e2e/`)
   - Complete user workflows
   - Full system testing
   - Target: Critical paths covered
   - Runtime: <5s per test

4. **Performance Tests** (`tests/performance/`)
   - Benchmarks and load tests
   - Memory usage monitoring
   - Scalability testing
   - Runtime: Varies

### Key Features

- ✅ **Comprehensive Fixtures** - Reusable test components
- ✅ **Custom Assertions** - Better error messages
- ✅ **Mock Services** - Predictable testing
- ✅ **Docker Environment** - Consistent test infrastructure
- ✅ **CI/CD Integration** - Automated testing
- ✅ **Pre-commit Hooks** - Catch issues early
- ✅ **Multi-Python Support** - Test on Python 3.9-3.12
- ✅ **Performance Monitoring** - Track speed regressions
- ✅ **Test Data Builders** - Easy test data creation
- ✅ **Debug Utilities** - Enhanced troubleshooting

## 🛠️ Common Tasks

### Running Tests with Docker
```bash
# Start test services
docker-compose -f tests/docker-compose.yml up -d

# Run tests
make test-integration

# Stop services
docker-compose -f tests/docker-compose.yml down
```

### Debugging Failed Tests
```bash
# Run with debugger on failure
poetry run pytest --pdb tests/unit/test_failing.py

# Show print statements
poetry run pytest -s tests/unit/test_module.py

# Verbose output
poetry run pytest -vv tests/unit/test_module.py

# Run last failed tests
poetry run pytest --lf
```

### Writing New Tests
```python
# 1. Use appropriate fixtures
def test_file_operations(initialized_context_manager, temp_workspace):
    # Your test here
    pass

# 2. Follow AAA pattern
def test_example():
    # Arrange
    data = create_test_data()

    # Act
    result = process_data(data)

    # Assert
    assert result.status == "success"

# 3. Use custom assertions
from tests.helpers.assertions import FileAssertions

def test_file_creation():
    create_file("test.txt")
    FileAssertions.assert_file_exists("test.txt")
```

### Creating Test Data
```python
from tests.helpers.builders import FileBuilder, ProjectBuilder

# Create a test file
test_file = FileBuilder()\
    .with_name("complex_module.py")\
    .with_complexity("high")\
    .with_syntax_errors()\
    .build()

# Create a test project
project = ProjectBuilder()\
    .with_type("python")\
    .with_size("medium")\
    .with_tests()\
    .build()
```

## 📈 Test Metrics

### Coverage Goals
- Overall: >85%
- Unit tests: >90%
- Integration tests: >80%
- Critical paths: 100%

### Performance Targets
- Unit test suite: <30 seconds
- Integration test suite: <2 minutes
- Full test suite: <5 minutes
- Individual unit test: <10ms
- Individual integration test: <100ms

### Quality Standards
- Zero flaky tests
- Clear failure messages
- Fast feedback cycle
- Easy debugging
- Comprehensive documentation

## 🔍 Troubleshooting

### Common Issues

1. **Redis Connection Failed**
   ```bash
   # Check Redis is running
   docker ps | grep redis

   # Restart Redis
   docker-compose -f tests/docker-compose.yml restart redis
   ```

2. **Import Errors**
   ```bash
   # Reinstall dependencies
   poetry install --with test

   # Check Python path
   echo $PYTHONPATH
   ```

3. **Slow Tests**
   ```bash
   # Profile test execution
   poetry run pytest --profile-svg

   # Run parallel tests
   poetry run pytest -n auto
   ```

4. **Coverage Below Threshold**
   ```bash
   # Find uncovered lines
   poetry run coverage report --show-missing

   # Generate HTML report
   poetry run coverage html
   ```

## 🎯 Best Practices

1. **Test Naming**
   - Be descriptive: `test_read_file_raises_error_when_file_not_found`
   - Group related tests in classes
   - Use consistent naming patterns

2. **Test Independence**
   - Each test should be independent
   - Use fixtures for setup/teardown
   - Avoid test order dependencies

3. **Mocking**
   - Mock external dependencies only
   - Use `spec` for type safety
   - Verify mock interactions

4. **Assertions**
   - One logical assertion per test
   - Use custom assertions for clarity
   - Include helpful error messages

5. **Performance**
   - Keep unit tests fast (<10ms)
   - Use markers for slow tests
   - Run slow tests separately in CI

## 📚 Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Testing Best Practices](./README.md)
- [Custom Assertions Guide](./helpers/assertions.py)
- [Test Data Builders](./helpers/builders.py)
- [Debug Utilities](./helpers/debug.py)

## 🤝 Contributing

When adding new features:
1. Write tests first (TDD)
2. Ensure all tests pass
3. Maintain coverage above 80%
4. Update test documentation
5. Run pre-commit hooks

Happy testing! 🧪✨
