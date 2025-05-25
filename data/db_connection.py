import os
import socket
import psycopg2
import sqlite3
import pandas as pd
import json
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Constants
SQLITE_DB_PATH = "stock_data.db"  # Fallback local database
SECRETS_PATH = ".streamlit/secrets.toml"


def parse_toml(file_path):
    """Simple TOML parser for secrets.toml file"""
    secrets = {}
    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    secrets[key] = value
        return secrets
    except Exception as e:
        print(f"Error parsing TOML file: {e}")
        return {}


def get_credentials():
    """Get database credentials from secrets.toml or environment variables"""
    credentials = {}

    # Try loading from secrets.toml
    secrets_file = SECRETS_PATH
    if os.path.exists(secrets_file):
        secrets = parse_toml(secrets_file)
        credentials["supabase_url"] = secrets.get("DATABASE_URL")
        credentials["supabase_key"] = secrets.get("SUPABASE_KEY")
        credentials["database_password"] = secrets.get("DATABASE_PASSWORD")

        if credentials["supabase_url"] and credentials["database_password"]:
            print(f"Loaded credentials from {secrets_file}")
            return credentials

    # Try loading from the root directory as well
    root_secrets = os.path.join(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))), SECRETS_PATH)
    if os.path.exists(root_secrets):
        secrets = parse_toml(root_secrets)
        credentials["supabase_url"] = secrets.get("DATABASE_URL")
        credentials["supabase_key"] = secrets.get("SUPABASE_KEY")
        credentials["database_password"] = secrets.get("DATABASE_PASSWORD")

        if credentials["supabase_url"] and credentials["database_password"]:
            print(f"Loaded credentials from {root_secrets}")
            return credentials

    # Try Streamlit secrets if running in Streamlit
    try:
        import streamlit as st
        credentials["supabase_url"] = st.secrets["DATABASE_URL"]
        credentials["supabase_key"] = st.secrets["SUPABASE_KEY"]
        credentials["database_password"] = st.secrets["DATABASE_PASSWORD"]

        if credentials["supabase_url"] and credentials["database_password"]:
            print("Loaded credentials from Streamlit secrets")
            return credentials
    except:
        print("Not running in Streamlit or secrets not available")

    # Try environment variables
    credentials["supabase_url"] = os.environ.get("DATABASE_URL")
    credentials["supabase_key"] = os.environ.get("SUPABASE_KEY")
    credentials["database_password"] = os.environ.get("DATABASE_PASSWORD")

    if credentials["supabase_url"] and credentials["database_password"]:
        print("Loaded credentials from environment variables")
        return credentials

    print("No valid credentials found - using fallback SQLite")
    return {}


class DatabaseConnection:
    """Database connection manager for both Supabase and SQLite"""

    def __init__(self):
        """Initialize connection based on available credentials"""
        self.engine = None
        self.Session = None
        self.connection_type = "sqlite"  # Default to SQLite

        # Try Supabase first, fall back to SQLite
        if not self._init_supabase():
            self._init_sqlite()

    def _get_supabase_pooler_connection_string(self):
        """Get PostgreSQL connection string using the Supabase Session Pooler for IPv4 compatibility"""
        try:
            # Get credentials
            credentials = get_credentials()
            db_password = credentials.get("database_password")
            supabase_url = credentials.get("supabase_url", "")

            if not db_password or not supabase_url:
                print("Missing database credentials")
                return None

            # Extract project reference from the URL
            if "https://" in supabase_url:
                project_ref = supabase_url.split("https://")[1].split(".")[0]
            else:
                project_ref = supabase_url.split(".")[0]

            # Session pooler connection string
            conn_string = f"postgresql://postgres.{project_ref}:{db_password}@aws-0-eu-north-1.pooler.supabase.com:5432/postgres"
            print(
                f"Using Session Pooler connection for project: {project_ref}")
            return conn_string
        except Exception as e:
            print(f"Error creating connection string: {e}")
            return None

    def _init_supabase(self):
        """Initialize connection to Supabase using Session Pooler"""
        conn_string = self._get_supabase_pooler_connection_string()
        if not conn_string:
            print("No valid Supabase connection string available")
            return False

        try:
            print("Connecting to Supabase PostgreSQL database via Session Pooler...")

            # Create SQLAlchemy engine with IPv4 compatible pooler
            self.engine = create_engine(
                conn_string,
                connect_args={
                    "connect_timeout": 10,  # 10-second connection timeout
                    "application_name": "stock_analyzer"
                }
            )

            # Test connection
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1")).fetchone()
                if result[0] == 1:
                    print("Supabase connection successful via Session Pooler!")
                else:
                    raise Exception(
                        "Connection test returned unexpected result")

            # Create session factory
            self.Session = sessionmaker(bind=self.engine)
            self.connection_type = "postgresql"
            return True

        except Exception as e:
            print(f"Supabase connection failed: {e}")
            return False

    def _init_sqlite(self):
        """Initialize SQLite database as fallback"""
        try:
            print("Initializing SQLite database...")
            sqlite_url = f"sqlite:///{SQLITE_DB_PATH}"
            self.engine = create_engine(sqlite_url)
            self.Session = sessionmaker(bind=self.engine)

            # Test connection
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1")).fetchone()
                if result[0] == 1:
                    print("SQLite connection successful!")
                else:
                    raise Exception(
                        "Connection test returned unexpected result")

            self.connection_type = "sqlite"
            return True
        except Exception as e:
            print(f"Error initializing SQLite database: {e}")
            return False

    def get_session(self):
        """Get a database session"""
        if self.Session is None:
            raise Exception("Database not initialized")
        return self.Session()

    def get_engine(self):
        """Get the SQLAlchemy engine"""
        if self.engine is None:
            raise Exception("Database not initialized")
        return self.engine

    def execute_query(self, query, params=None):
        """Execute a SQL query and return results as DataFrame"""
        try:
            with self.engine.connect() as conn:
                if params:
                    result = conn.execute(text(query), params)
                else:
                    result = conn.execute(text(query))

                # Convert to DataFrame
                columns = result.keys()
                data = result.fetchall()
                return pd.DataFrame(data, columns=columns)
        except Exception as e:
            print(f"Error executing query: {e}")
            return pd.DataFrame()


# Singleton instance
_db_connection = None


def get_db_connection():
    """Get the singleton database connection instance"""
    global _db_connection
    if _db_connection is None:
        _db_connection = DatabaseConnection()
    return _db_connection


def get_db_session():
    """Get a database session"""
    return get_db_connection().get_session()


def get_db_engine():
    """Get the SQLAlchemy engine"""
    return get_db_connection().get_engine()


@contextmanager
def get_db_session_context():
    """
    Context manager for safe database session handling.
    
    Automatically handles commit, rollback, and closing the session.
    
    Example:
        with get_db_session_context() as session:
            # Do database operations
            session.query(...)
            
        # Session is automatically committed and closed when exiting the block
        # If an exception occurs, the session is rolled back and closed
    """
    session = get_db_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_connection_type():
    """Get the type of database connection ('postgresql' or 'sqlite')"""
    return get_db_connection().connection_type


def test_connection():
    """Test the database connection and print status"""
    try:
        db = get_db_connection()
        engine = db.get_engine()

        with engine.connect() as conn:
            result = conn.execute(text("SELECT current_timestamp")).fetchone()
            timestamp = result[0]

        print(f"✅ Connected to {db.connection_type} database!")
        print(f"Current database timestamp: {timestamp}")
        return True
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False


# If this file is run directly, run the test
if __name__ == "__main__":
    test_connection()
