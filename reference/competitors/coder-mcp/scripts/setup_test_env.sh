#!/bin/bash
# Setup complete test environment for MCP Server

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 is not installed. Please install it first."
        return 1
    fi
    return 0
}

# Main setup
main() {
    log_info "Setting up MCP Server test environment..."

    # Check prerequisites
    log_info "Checking prerequisites..."

    MISSING_DEPS=0

    if ! check_command "python3"; then
        MISSING_DEPS=1
    fi

    if ! check_command "poetry"; then
        log_warning "Poetry not found. Installing Poetry..."
        curl -sSL https://install.python-poetry.org | python3 -
        export PATH="$HOME/.local/bin:$PATH"
    fi

    if ! check_command "docker"; then
        log_warning "Docker not found. Please install Docker Desktop."
        MISSING_DEPS=1
    fi

    if ! check_command "docker-compose"; then
        log_warning "docker-compose not found. Please install Docker Compose."
        MISSING_DEPS=1
    fi

    if [ $MISSING_DEPS -eq 1 ]; then
        log_error "Missing required dependencies. Please install them and run again."
        exit 1
    fi

    log_success "All prerequisites installed!"

    # Install Python dependencies
    log_info "Installing Python dependencies..."
    poetry install --with test,dev
    log_success "Python dependencies installed!"

    # Install pre-commit hooks
    log_info "Installing pre-commit hooks..."
    poetry run pre-commit install
    poetry run pre-commit install --hook-type commit-msg
    log_success "Pre-commit hooks installed!"

    # Create necessary directories
    log_info "Creating directory structure..."
    mkdir -p reports/{coverage,performance,allure}
    mkdir -p tests/fixtures/{sample_projects,test_files,mock_responses}
    log_success "Directory structure created!"

    # Start Docker services
    log_info "Starting Docker services..."
    docker-compose -f tests/docker-compose.yml up -d redis

    # Wait for Redis to be ready
    log_info "Waiting for Redis to be ready..."
    for i in {1..30}; do
        if docker-compose -f tests/docker-compose.yml exec -T redis redis-cli ping &> /dev/null; then
            log_success "Redis is ready!"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "Redis failed to start in time"
            exit 1
        fi
        sleep 1
    done

    # Create sample test data
    log_info "Creating sample test data..."
    cat > tests/fixtures/mock_responses/completions.json << 'EOF'
{
  "analyze": {
    "id": "chatcmpl-test-analyze",
    "object": "chat.completion",
    "created": 1234567890,
    "model": "gpt-3.5-turbo",
    "choices": [
      {
        "index": 0,
        "message": {
          "role": "assistant",
          "content": "The code analysis is complete. The structure is well-organized with proper error handling."
        },
        "finish_reason": "stop"
      }
    ],
    "usage": {
      "prompt_tokens": 10,
      "completion_tokens": 15,
      "total_tokens": 25
    }
  }
}
EOF

    # Create test configuration
    log_info "Creating test configuration..."
    cat > .env.test << EOF
# Test Environment Configuration
TEST_REDIS_URL=redis://localhost:6379/15
TEST_OPENAI_API_KEY=test-key-12345
TEST_OPENAI_API_BASE=http://localhost:8080/v1
MCP_TEST_MODE=true
LOG_LEVEL=DEBUG
EOF

    # Run initial tests to verify setup
    log_info "Running verification tests..."
    if poetry run pytest tests/unit/test_context_manager.py::TestContextManagerInitialization::test_init_with_valid_config -v; then
        log_success "Test environment is working!"
    else
        log_warning "Some tests failed. This might be expected for initial setup."
    fi

    # Generate initial coverage report
    log_info "Generating initial coverage report..."
    poetry run pytest tests/unit --cov=coder_mcp --cov-report=html:reports/coverage --cov-report=term || true

    # Final summary
    echo
    echo "========================================"
    echo "   Test Environment Setup Complete!     "
    echo "========================================"
    echo
    echo "Next steps:"
    echo "1. Run all tests:          make test"
    echo "2. Run unit tests:         make test-unit"
    echo "3. Run integration tests:  make test-integration"
    echo "4. View coverage report:   open reports/coverage/index.html"
    echo "5. Run tests in watch:     make test-watch"
    echo
    echo "Docker services running:"
    docker-compose -f tests/docker-compose.yml ps
    echo
    log_success "Happy testing! 🧪"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up..."
    docker-compose -f tests/docker-compose.yml down
}

# Set trap for cleanup
trap cleanup EXIT

# Run main function
main "$@"
