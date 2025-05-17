import os
import psycopg2
import sqlite3
import logging
from sqlalchemy import create_engine, Column, Integer, String, Float, BigInteger, Text, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SQLAlchemy Base class for ORM
Base = declarative_base()

# Default SQLite database path
SQLITE_DB_PATH = "stock_analysis.db"

# Global database connection variables
engine = None
Session = None
connection_type = "sqlite"  # Default to SQLite

def get_supabase_connection_string():
    """
    Get a properly formatted PostgreSQL connection string for Supabase.
    
    Returns:
        str or None: Formatted connection string or None if not available
    """
    # Get the base URL and password from environment
    database_url = os.getenv("DATABASE_URL", "")
    password = os.getenv("SUPABASE_DB_PASSWORD", "")
    
    if not database_url or not password:
        logger.warning("DATABASE_URL or SUPABASE_DB_PASSWORD not set")
        return None
    
    # Format into a proper PostgreSQL connection string
    if database_url.startswith("https://") and "supabase.co" in database_url:
        # Extract project reference from the URL
        project_ref = database_url.split("//")[1].split(".")[0]
        
        # Format PostgreSQL connection string
        postgres_url = f"postgresql://postgres:{password}@db.{project_ref}.supabase.co:5432/postgres"
        return postgres_url
    elif database_url.startswith("postgresql://"):
        # Already in the correct format
        return database_url
    
    return None

def test_supabase_connection():
    """
    Test the connection to Supabase database.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    conn_string = get_supabase_connection_string()
    if not conn_string:
        return False
    
    try:
        # Try to connect with a short timeout
        conn = psycopg2.connect(conn_string, connect_timeout=5)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.warning(f"Supabase connection test failed: {str(e)}")
        return False

def init_sqlite_db():
    """Initialize SQLite database."""
    global engine, Session
    
    logger.info("Initializing SQLite database...")
    sqlite_url = f"sqlite:///{SQLITE_DB_PATH}"
    
    try:
        engine = create_engine(sqlite_url)
        Session = sessionmaker(bind=engine)
        
        # Create tables if they don't exist
        Base.metadata.create_all(engine)
        logger.info("SQLite database initialized successfully!")
        return True
    except Exception as e:
        logger.error(f"Error initializing SQLite database: {str(e)}")
        return False

def init_postgres_db():
    """Initialize PostgreSQL database with Supabase."""
    global engine, Session, connection_type
    
    logger.info("Testing Supabase connection...")
    
    # Get connection string
    conn_string = get_supabase_connection_string()
    if not conn_string:
        logger.warning("No valid Supabase connection string available")
        return False
    
    try:
        # Create SQLAlchemy engine and session
        engine = create_engine(conn_string)
        Session = sessionmaker(bind=engine)
        
        # Test the connection
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        
        # Create tables if they don't exist
        Base.metadata.create_all(engine)
        
        # Set connection type to PostgreSQL
        connection_type = "postgresql"
        logger.info("Successfully connected to Supabase PostgreSQL database")
        return True
    except Exception as e:
        logger.warning(f"Supabase connection failed: {str(e)}")
        return False

def initialize_database():
    """
    Initialize the database (either PostgreSQL or SQLite).
    
    Returns:
        tuple: (engine, Session, connection_type)
    """
    global engine, Session, connection_type
    
    logger.info("Starting database initialization...")
    
    # First try to connect to Supabase
    if init_postgres_db():
        logger.info("Using Supabase PostgreSQL database")
    else:
        # Fall back to SQLite
        logger.info("Using SQLite database for local storage")
        init_sqlite_db()
    
    return engine, Session, connection_type

def get_db_session():
    """
    Get a database session.
    
    Returns:
        Session: A SQLAlchemy session
    """
    global Session
    if Session is None:
        initialize_database()
    return Session()

def get_db_engine():
    """
    Get the database engine.
    
    Returns:
        Engine: SQLAlchemy engine
    """
    global engine
    if engine is None:
        initialize_database()
    return engine

def get_connection_type():
    """
    Get the type of database connection being used.
    
    Returns:
        str: 'postgresql' or 'sqlite'
    """
    global connection_type
    return connection_type