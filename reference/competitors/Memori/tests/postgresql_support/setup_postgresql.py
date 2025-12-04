#!/usr/bin/env python3
"""
PostgreSQL Setup for Memori Cross-Database Testing
Sets up PostgreSQL database, creates test database, and configures tsvector full-text search
"""

import os
import subprocess
import sys
from pathlib import Path

# Add the memori package to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def check_postgresql_installation():
    """Check if PostgreSQL is installed and running"""
    try:
        result = subprocess.run(
            ["psql", "--version"], capture_output=True, text=True, check=True
        )
        version = result.stdout.strip()
        print(f"   {version}")

        # Check if PostgreSQL server is running
        result = subprocess.run(["pg_isready"], capture_output=True, text=True)

        if result.returncode == 0:
            print("   PostgreSQL server is running")
            return True
        else:
            print("   ⚠️  PostgreSQL server is not running")
            print(
                "   💡 Start PostgreSQL with: brew services start postgresql (macOS) or systemctl start postgresql (Linux)"
            )
            return False

    except (subprocess.CalledProcessError, FileNotFoundError):
        print("   ❌ PostgreSQL not found")
        print(
            "   💡 Install with: brew install postgresql (macOS) or apt-get install postgresql (Linux)"
        )
        return False


def get_postgresql_connection_params():
    """Get PostgreSQL connection parameters"""
    # Try to get connection parameters from environment or use defaults
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    user = os.environ.get("POSTGRES_USER", os.environ.get("USER", "postgres"))

    return {
        "host": host,
        "port": port,
        "user": user,
    }


def setup_test_database():
    """Create and configure test database"""
    params = get_postgresql_connection_params()

    # Database name for testing
    test_db_name = "memori_test"

    try:
        # Connect to PostgreSQL to create database
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

        # Connection for administrative tasks (connect to 'postgres' database)
        admin_conn_params = {
            "host": params["host"],
            "port": params["port"],
            "user": params["user"],
            "database": "postgres",  # Connect to default database
        }

        if params["password"]:
            admin_conn_params["password"] = params["password"]

        conn = psycopg2.connect(**admin_conn_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Drop database if it exists, then create it
        cursor.execute(f"DROP DATABASE IF EXISTS {test_db_name}")
        cursor.execute(f"CREATE DATABASE {test_db_name}")
        print(f"✅ Created database '{test_db_name}'")

        # Set UTF-8 encoding
        cursor.execute(f"ALTER DATABASE {test_db_name} SET client_encoding TO 'UTF8'")
        print("✅ Set UTF-8 encoding")

        cursor.close()
        conn.close()

        # Connect to the test database to check extensions
        test_conn_params = admin_conn_params.copy()
        test_conn_params["database"] = test_db_name

        test_conn = psycopg2.connect(**test_conn_params)
        test_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        test_cursor = test_conn.cursor()

        # Check available extensions
        test_cursor.execute(
            "SELECT name FROM pg_available_extensions WHERE name IN ('unaccent', 'pg_trgm')"
        )
        extensions = [row[0] for row in test_cursor.fetchall()]

        # Enable useful extensions if available
        for ext in extensions:
            try:
                test_cursor.execute(f"CREATE EXTENSION IF NOT EXISTS {ext}")
                print(f"✅ Enabled extension '{ext}'")
            except Exception as e:
                print(f"⚠️  Could not enable extension '{ext}': {e}")

        # Check full-text search capabilities
        test_cursor.execute(
            "SELECT to_tsvector('english', 'Test full-text search capabilities')"
        )
        result = test_cursor.fetchone()
        if result:
            print("✅ Full-text search (tsvector) is available")
            print(f"📊 Test tsvector: {result[0]}")

        test_cursor.close()
        test_conn.close()

        return True

    except ImportError:
        print("❌ psycopg2 not installed")
        print("💡 Install with: pip install psycopg2-binary")
        return False

    except Exception as e:
        print(f"❌ Failed to setup database: {e}")
        return False


def verify_sqlalchemy_integration():
    """Verify SQLAlchemy can connect to PostgreSQL"""
    params = get_postgresql_connection_params()

    # Build connection string
    password_part = f":{params['password']}" if params["password"] else ""
    connection_string = f"postgresql+psycopg2://{params['user']}{password_part}@{params['host']}:{params['port']}/memori_test"

    try:
        from memori.database.sqlalchemy_manager import SQLAlchemyDatabaseManager

        # Test connection
        db_manager = SQLAlchemyDatabaseManager(connection_string)

        # Get database info
        info = db_manager.get_database_info()
        print(f"   ✅ SQLAlchemy connection successful: {info['database_type']}")
        print(f"   📊 Server version: {info.get('server_version', 'Unknown')}")
        print(f"   🔍 tsvector support: {info.get('supports_fulltext', 'Unknown')}")

        db_manager.close()

        return connection_string

    except Exception as e:
        print(f"   ❌ SQLAlchemy integration failed: {e}")
        return None


def main():
    """Main setup function"""
    print("🛠️  PostgreSQL Setup for Memori Cross-Database Testing")
    print("=" * 55)

    # Step 1: Check PostgreSQL installation
    print("1. Checking PostgreSQL installation...")
    if not check_postgresql_installation():
        return 1

    # Step 2: Setup test database
    print("\n2. Setting up test database...")
    if not setup_test_database():
        return 1

    # Step 3: Verify SQLAlchemy integration
    print("\n3. Verifying SQLAlchemy integration...")
    connection_string = verify_sqlalchemy_integration()
    if not connection_string:
        return 1

    # Success
    print("\n" + "=" * 55)
    print("🎉 PostgreSQL setup completed successfully!")
    print("\n📋 Ready to run tests:")
    print("   python tests/postgresql_support/postgresql_test_suite.py")

    print("\n🔧 Connection details:")
    params = get_postgresql_connection_params()
    print(f"   Host: {params['host']}")
    print(f"   Port: {params['port']}")
    print(f"   User: {params['user']}")
    print("   Database: memori_test")
    print(f"   URL: {connection_string}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
