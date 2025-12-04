#!/usr/bin/env python3
"""
MySQL Setup Script for Memori Testing
Helps prepare MySQL environment for cross-database testing
"""

import subprocess
import sys
from pathlib import Path


def check_mysql_installation():
    """Check if MySQL is installed and running"""
    try:
        # Try to connect to MySQL
        import mysql.connector

        conn = mysql.connector.connect(
            host="127.0.0.1",
            port=3306,
            user="root",
            password="",
        )

        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        conn.close()

        return True, f"MySQL {version} is running"

    except ImportError:
        return False, "mysql-connector-python not installed"
    except Exception as e:
        return False, f"MySQL connection failed: {e}"


def install_mysql_connector():
    """Install mysql-connector-python"""
    try:
        print("📦 Installing mysql-connector-python...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "mysql-connector-python"]
        )
        print("✅ mysql-connector-python installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install mysql-connector-python: {e}")
        return False


def create_test_database():
    """Create the test database and configure it"""
    try:
        import mysql.connector

        conn = mysql.connector.connect(
            host="127.0.0.1",
            port=3306,
            user="root",
            password="",
        )

        cursor = conn.cursor()

        # Create test database
        cursor.execute("CREATE DATABASE IF NOT EXISTS memori_test")
        print("✅ Created database 'memori_test'")

        # Set proper character set and collation for Unicode support
        cursor.execute(
            "ALTER DATABASE memori_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        print("✅ Set UTF8MB4 character set")

        # Show database info
        cursor.execute("SHOW CREATE DATABASE memori_test")
        db_info = cursor.fetchone()[1]
        print(f"📊 Database info: {db_info}")

        # Check InnoDB availability (required for FULLTEXT on MySQL 5.6+)
        cursor.execute("SHOW ENGINES")
        engines = cursor.fetchall()
        innodb_available = any(
            engine[0] == "InnoDB" and engine[1] in ("YES", "DEFAULT")
            for engine in engines
        )

        if innodb_available:
            print("✅ InnoDB engine available (supports FULLTEXT indexes)")
        else:
            print("⚠️  InnoDB engine not available - FULLTEXT search may be limited")

        # Check FULLTEXT support
        cursor.execute("SHOW VARIABLES LIKE 'ft_min_word_len'")
        result = cursor.fetchone()
        if result:
            print(f"📊 FULLTEXT minimum word length: {result[1]}")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Failed to setup test database: {e}")
        return False


def main():
    """Main setup routine"""
    print("🛠️  MySQL Setup for Memori Cross-Database Testing")
    print("=" * 55)

    # Step 1: Check MySQL installation
    print("1. Checking MySQL installation...")
    mysql_ok, mysql_msg = check_mysql_installation()
    print(f"   {mysql_msg}")

    if not mysql_ok:
        if "mysql-connector-python not installed" in mysql_msg:
            if input("\n   Install mysql-connector-python? (y/n): ").lower() == "y":
                if not install_mysql_connector():
                    return 1
                # Recheck after installation
                mysql_ok, mysql_msg = check_mysql_installation()
                print(f"   {mysql_msg}")

        if not mysql_ok:
            print("\n❌ MySQL setup failed. Please ensure:")
            print("   - MySQL server is installed and running")
            print("   - MySQL server is accessible on localhost:3306")
            print("   - User 'root' has appropriate permissions")
            print("\n💡 On macOS: brew install mysql && brew services start mysql")
            print("💡 On Ubuntu: sudo apt install mysql-server")
            print("💡 On Windows: Download from https://dev.mysql.com/downloads/mysql/")
            return 1

    # Step 2: Create test database
    print("\n2. Setting up test database...")
    if not create_test_database():
        return 1

    # Step 3: Verify SQLAlchemy integration
    print("\n3. Verifying SQLAlchemy integration...")
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from memori.database.sqlalchemy_manager import SQLAlchemyDatabaseManager

        # Test connection - use mysql+mysqlconnector for the mysql-connector-python driver
        db_manager = SQLAlchemyDatabaseManager(
            "mysql+mysqlconnector://root:@127.0.0.1:3306/memori_test"
        )
        db_manager.initialize_schema()

        db_info = db_manager.get_database_info()
        print(f"   ✅ SQLAlchemy connection successful: {db_info['database_type']}")

        db_manager.close()

    except Exception as e:
        print(f"   ❌ SQLAlchemy integration failed: {e}")
        return 1

    print("\n" + "=" * 55)
    print("🎉 MySQL setup completed successfully!")
    print("\n📋 Ready to run tests:")
    print("   python tests/mysql_support/mysql_test_suite.py")
    print("\n🔧 Connection details:")
    print("   Host: localhost (127.0.0.1)")
    print("   Port: 3306")
    print("   User: root")
    print("   Database: memori_test")
    print("   URL: mysql://root:@127.0.0.1:3306/memori_test")

    return 0


if __name__ == "__main__":
    sys.exit(main())
