# PostgreSQL Support for Memori

This directory contains PostgreSQL integration tests and setup scripts for Memori's cross-database compatibility.

## Prerequisites

### PostgreSQL Installation

**macOS (Homebrew):**
```bash
brew install postgresql
brew services start postgresql
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**Python Dependencies:**
```bash
pip install psycopg2-binary
```

## Setup

### 1. Environment Variables (Optional)
You can customize PostgreSQL connection parameters with environment variables:

```bash
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_USER=postgres
# POSTGRES_PASSWORD is optional for local development
```

### 2. Database Setup
Run the setup script to create the test database:

```bash
python tests/postgresql_support/setup_postgresql.py
```

This will:
- Check PostgreSQL installation and server status
- Create `memori_test` database
- Configure UTF-8 encoding
- Enable useful extensions (unaccent, pg_trgm if available)
- Verify tsvector full-text search capabilities
- Test SQLAlchemy integration

## Testing

### Basic PostgreSQL Test
```bash
python tests/postgresql_support/postgresql_test_suite.py
```

### LiteLLM + PostgreSQL Integration Test
```bash
python tests/postgresql_support/litellm_postgresql_test_suite.py
```

### Comprehensive Database Comparison
```bash
python tests/comprehensive_database_comparison.py
```

## Features Tested

### PostgreSQL-Specific Features
- **tsvector Full-Text Search**: Native PostgreSQL full-text search with ranking
- **GIN Indexes**: Optimized indexing for full-text search
- **Extensions**: Optional unaccent and pg_trgm for enhanced search
- **ACID Compliance**: Full transaction support
- **Advanced SQL**: Complex queries and window functions

### Cross-Database Compatibility
- **Identical APIs**: Same interface across SQLite, MySQL, and PostgreSQL
- **Search Abstraction**: Automatic fallback between native and LIKE-based search
- **Schema Management**: SQLAlchemy handles database differences
- **Connection Pooling**: Optimized connection management

## Connection String Format

```
postgresql+psycopg2://user:password@host:port/database
```

Example:
```
postgresql+psycopg2://postgres@localhost:5432/memori_test
```

## Test Scenarios

The LiteLLM test suite includes 6 scenarios testing different ingestion configurations:

1. `conscious_ingest=False, auto_ingest=None`
2. `conscious_ingest=True, auto_ingest=None`
3. `conscious_ingest=None, auto_ingest=True`
4. `conscious_ingest=None, auto_ingest=False`
5. `conscious_ingest=False, auto_ingest=False`
6. `conscious_ingest=True, auto_ingest=True`

## Performance Notes

- **Full-Text Search**: PostgreSQL tsvector provides excellent performance for complex queries
- **Indexing**: GIN indexes are automatically created for search columns
- **Connection Pooling**: Enabled by default for production workloads
- **Query Optimization**: PostgreSQL's query planner handles complex joins efficiently

## Troubleshooting

### PostgreSQL Not Running
```bash
# macOS
brew services start postgresql

# Linux
sudo systemctl start postgresql
```

### Permission Issues
```bash
# Create user if needed
createuser -s postgres

# Or use existing user
export POSTGRES_USER=$(whoami)
```

### Extension Errors
Extensions like `unaccent` and `pg_trgm` are optional. The tests will work without them but may have reduced search functionality.

### Connection Issues
Verify PostgreSQL is accepting connections:
```bash
pg_isready
```

## Architecture

PostgreSQL integration is implemented through:

- **SQLAlchemy Manager**: `memori/database/sqlalchemy_manager.py`
- **Search Service**: `memori/database/search_service.py`
- **Models**: `memori/database/models.py`
- **PostgreSQL FTS Setup**: Automatic tsvector column and GIN index creation

The implementation maintains full compatibility with existing Memori APIs while leveraging PostgreSQL's advanced features for optimal performance.