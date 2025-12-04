# MySQL Support Testing for Memori v2.0

This directory contains test suites for MySQL cross-database compatibility in Memori.

## 🚀 Quick Start

### 1. Setup MySQL Environment
```bash
# Run the setup script
python tests/mysql_support/setup_mysql.py
```

### 2. Run MySQL Tests
```bash
# Run the complete test suite
python tests/mysql_support/mysql_test_suite.py
```

## 📋 Prerequisites

### MySQL Server
- MySQL 5.6+ (for FULLTEXT support with InnoDB)
- Running on `localhost:3306`
- Root user access (or configure credentials in test scripts)

### Python Dependencies
```bash
pip install mysql-connector-python>=8.0.0
pip install sqlalchemy>=2.0.0
```

## 🧪 Test Coverage

### Basic Integration Tests
- ✅ Database connection and initialization
- ✅ Schema creation with SQLAlchemy models
- ✅ Chat history storage and retrieval
- ✅ Memory search functionality
- ✅ Database statistics and cleanup

### MySQL-Specific Tests
- ✅ FULLTEXT index creation and configuration
- ✅ Natural language search queries
- ✅ Performance benchmarking
- ✅ Character encoding (UTF8MB4) support
- ✅ InnoDB engine compatibility

### Cross-Database Compatibility
- ✅ Seamless migration from SQLite
- ✅ Identical API interface
- ✅ Fallback search mechanisms
- ✅ Error handling consistency

## 🔧 Configuration

### Database Connection URLs
```python
# Local MySQL (default) - using mysql-connector-python
mysql+mysqlconnector://root:@127.0.0.1:3306/memori_test

# With password
mysql+mysqlconnector://user:password@localhost:3306/memori

# Remote MySQL
mysql+mysqlconnector://user:password@mysql.example.com:3306/memori_prod

# Alternative drivers:
# mysql+pymysql://user:password@localhost:3306/memori  # PyMySQL
# mysql://user:password@localhost:3306/memori          # MySQLdb (requires mysqlclient)
```

### Environment Variables
You can also set these environment variables:
```bash
export MEMORI_DB_URL="mysql://root:@127.0.0.1:3306/memori_test"
export MYSQL_ROOT_PASSWORD="your_password"
```

## 🚨 Troubleshooting

### Common Issues

**Connection Refused**
```
mysql.connector.errors.InterfaceError: 2003: Can't connect to MySQL server
```
- Ensure MySQL server is running: `brew services start mysql` (macOS)
- Check port accessibility: `telnet localhost 3306`

**Access Denied**
```
mysql.connector.errors.ProgrammingError: 1045: Access denied for user 'root'@'localhost'
```
- Reset MySQL root password
- Update connection credentials in test scripts

**FULLTEXT Indexes Not Working**
```
MySQL FULLTEXT indexes not found, search will use fallback
```
- Ensure MySQL 5.6+ with InnoDB engine
- Check `ft_min_word_len` setting: `SHOW VARIABLES LIKE 'ft_min_word_len'`

### MySQL Commands for Debugging
```sql
-- Check database and tables
SHOW DATABASES;
USE memori_test;
SHOW TABLES;

-- Check FULLTEXT indexes
SELECT * FROM information_schema.STATISTICS 
WHERE table_schema = 'memori_test' AND index_type = 'FULLTEXT';

-- Check character set
SHOW CREATE DATABASE memori_test;

-- Test FULLTEXT search manually
SELECT * FROM short_term_memory WHERE MATCH(searchable_content, summary) AGAINST('test' IN NATURAL LANGUAGE MODE);
```

## 🎯 Integration with Main Codebase

The MySQL support is integrated into the main Memori class through the SQLAlchemy database manager:

```python
from memori import Memori

# Use MySQL instead of SQLite
memory = Memori(
    database_connect="mysql+mysqlconnector://root:@localhost:3306/memori",
    template="basic",
    verbose=True
)

# All existing APIs work the same
results = memory.db_manager.search_memories("my query")
stats = memory.db_manager.get_memory_stats()
```

## 📊 Performance Expectations

### MySQL vs SQLite Performance
- **Connection**: MySQL ~50ms vs SQLite ~1ms (network overhead)
- **Bulk inserts**: MySQL ~2x slower due to network + ACID compliance
- **FULLTEXT search**: MySQL comparable to SQLite FTS5
- **Concurrent access**: MySQL significantly better scaling

### Recommended MySQL Configuration
```sql
-- For development/testing
SET GLOBAL innodb_buffer_pool_size = 268435456;  -- 256MB
SET GLOBAL ft_min_word_len = 3;
SET GLOBAL ft_boolean_syntax = ' +-><()~*:""&|';

-- For production
-- Consider dedicated MySQL tuning based on your workload
```

## 🔮 Future Enhancements

- [ ] Connection pooling optimization
- [ ] MySQL-specific query optimizations
- [ ] Automated database migration tools
- [ ] Master-slave replication support
- [ ] Performance monitoring integration