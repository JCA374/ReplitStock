# File: debug_with_ip.py

import os
import sys
import socket
import time
import toml
from pathlib import Path
import psycopg2
from sqlalchemy import create_engine, text


def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 50)
    print(f" {title}")
    print("=" * 50)


def print_success(message):
    """Print a success message"""
    print(f"✅ {message}")


def print_error(message, exception=None):
    """Print an error message with optional exception details"""
    print(f"❌ {message}")
    if exception:
        print(f"   Error details: {str(exception)}")


def load_secrets():
    """Load secrets from .streamlit/secrets.toml file"""
    secrets_path = Path(".streamlit/secrets.toml")
    if not secrets_path.exists():
        print_error(f"Secrets file not found at {secrets_path}")
        return None

    try:
        return toml.load(secrets_path)
    except Exception as e:
        print_error("Failed to load secrets.toml", e)
        return None


def test_direct_ip_connection(password, ip_address="2a05:d016:571:a404:436b:e71:5af3:970"):
    """Test connection using direct IP address"""
    print_section(f"Direct IP Connection Test")

    # Format connection string with IP
    # Note: Enclosing IPv6 address in square brackets
    conn_string = f"postgresql://postgres:{password}@[{ip_address}]:5432/postgres"

    if ":" in ip_address:  # This is an IPv6 address
        print(f"Testing connection to IPv6 address: {ip_address}")
    else:
        print(f"Testing connection to IPv4 address: {ip_address}")

    try:
        # Try connection with 10-second timeout
        print("Connecting with a 10-second timeout...")
        conn = psycopg2.connect(
            conn_string,
            connect_timeout=10
        )

        # Test query
        cursor = conn.cursor()
        cursor.execute("SELECT current_timestamp")
        result = cursor.fetchone()

        print_success("Direct IP connection successful!")
        print(f"Database timestamp: {result[0]}")

        cursor.close()
        conn.close()

        return True
    except Exception as e:
        print_error("Direct IP connection failed", e)
        return False


def test_with_hardcoded_credentials():
    """Test connection with hardcoded credentials"""
    print_section("Direct IP Connection with Hardcoded Credentials")

    secrets = load_secrets()
    if not secrets:
        print_error("Failed to load secrets")
        return False

    password = secrets.get("DATABASE_PASSWORD")
    if not password:
        print_error("DATABASE_PASSWORD not found in secrets")
        return False

    # Try IPv6 connection first
    ipv6_address = "2a05:d016:571:a404:436b:e71:5af3:970"
    if test_direct_ip_connection(password, ipv6_address):
        print_success("IPv6 connection successful!")
        return True

    # If IPv6 fails, try to get an IPv4 address if it exists
    # If you have an IPv4 address, add it here
    ipv4_address = input(
        "Enter the IPv4 address for your database (leave empty to skip IPv4 test): ")
    if ipv4_address:
        if test_direct_ip_connection(password, ipv4_address):
            print_success("IPv4 connection successful!")
            return True

    return False


def test_db_operations():
    """Test database operations with working connection"""
    print_section("Database Operations Test")

    secrets = load_secrets()
    if not secrets:
        return False

    password = secrets.get("DATABASE_PASSWORD")
    if not password:
        return False

    # Use the IPv6 address that worked
    ip_address = "2a05:d016:571:a404:436b:e71:5af3:970"
    conn_string = f"postgresql://postgres:{password}@[{ip_address}]:5432/postgres"

    try:
        # Connect and create SQLAlchemy engine
        engine = create_engine(conn_string)

        with engine.connect() as conn:
            # Test if we can create a table
            print("Testing table creation...")
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS direct_ip_test (
                id SERIAL PRIMARY KEY,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """))

            # Insert test data
            insert_result = conn.execute(
                text("INSERT INTO direct_ip_test (message) VALUES (:msg) RETURNING id"),
                {"msg": f"Direct IP test at {time.time()}"}
            )
            new_id = insert_result.fetchone()[0]
            print_success(f"Inserted row with ID {new_id}")

            # Query the data
            result = conn.execute(
                text(
                    "SELECT id, message, created_at FROM direct_ip_test ORDER BY id DESC LIMIT 5")
            )
            rows = result.fetchall()

            print_success(f"Retrieved {len(rows)} rows from test table:")
            for row in rows:
                print(f"  ID: {row[0]}, Message: {row[1]}, Created: {row[2]}")

        print_success("Database operations completed successfully!")
        return True

    except Exception as e:
        print_error("Database operations failed", e)
        return False


def generate_connection_code():
    """Generate code for connection using direct IP"""
    print_section("Connection Code for Your Application")

    print("""
# Add this to your db_connection.py file:

import socket
import psycopg2
import streamlit as st
from sqlalchemy import create_engine

def get_db_connection():
    \"\"\"Get database connection using direct IP address\"\"\"
    try:
        # Get credentials from secrets
        password = st.secrets["DATABASE_PASSWORD"]
        
        # Use direct IPv6 address instead of hostname
        ipv6_address = "2a05:d016:571:a404:436b:e71:5af3:970"
        conn_string = f"postgresql://postgres:{password}@[{ipv6_address}]:5432/postgres"
        
        # Create SQLAlchemy engine with appropriate parameters
        engine = create_engine(
            conn_string,
            connect_args={
                "connect_timeout": 10,
                "application_name": "stock_analyzer",
                "keepalives": 1,
                "keepalives_idle": 30
            }
        )
        
        return engine
    except Exception as e:
        print(f"Database connection error: {e}")
        # Fall back to SQLite
        return create_engine("sqlite:///stock_data.db")
    """)


if __name__ == "__main__":
    print_section("Supabase Direct IP Connection Test")
    print("This script will test connection using the direct IP address")

    if test_with_hardcoded_credentials():
        # If direct connection works, test database operations
        if test_db_operations():
            print_success(
                "All tests passed! Your database connection works with direct IP address.")

            # Generate code for the application
            generate_connection_code()

            print_section("Next Steps")
            print("1. Update your db_connection.py file with the generated code")
            print("2. Restart your Streamlit application")
            print("3. If connection issues persist, try using the IPv4 address instead")
    else:
        print_error(
            "Direct IP connection failed. Try these troubleshooting steps:")
        print("1. Check your network connectivity and firewall settings")
        print("2. Verify your Supabase database is online and accessible")
        print("3. Contact Supabase support if issues persist")
