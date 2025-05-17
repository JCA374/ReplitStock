import os
import sys
import time
import json

# Add the root directory to the path so we can import modules
sys.path.insert(0, ".")

def get_supabase_config():
    """Get current Supabase configuration from environment variables."""
    print("Current Supabase Configuration:")
    print("-" * 30)
    
    # Get current values
    database_url = os.getenv("DATABASE_URL", "")
    supabase_key = os.getenv("SUPABASE_KEY", "")
    supabase_password = os.getenv("SUPABASE_DB_PASSWORD", "")
    
    # Print sanitized values
    masked_db_url = database_url[:20] + "..." if database_url else "Not set"
    masked_key = "Set" if supabase_key else "Not set"
    masked_password = "Set" if supabase_password else "Not set"
    
    print(f"DATABASE_URL: {masked_db_url}")
    print(f"SUPABASE_KEY: {masked_key}")
    print(f"SUPABASE_DB_PASSWORD: {masked_password}")
    
    return {
        "database_url": database_url,
        "supabase_key": supabase_key,
        "supabase_password": supabase_password
    }

def analyze_database_url(url):
    """Analyze the database URL format and convert if needed."""
    print("\nDatabase URL Analysis:")
    print("-" * 30)
    
    if not url:
        print("❌ ERROR: DATABASE_URL is not set")
        return None
    
    # Check if it's a PostgreSQL connection string
    if url.startswith("postgresql://"):
        print("✅ URL is already in PostgreSQL format")
        return url
    
    # Check if it's a Supabase project URL
    if url.startswith("https://") and "supabase.co" in url:
        print("ℹ️ URL is in Supabase project format, needs conversion")
        
        # Extract project reference
        project_ref = url.split("//")[1].split(".")[0]
        print(f"ℹ️ Project reference: {project_ref}")
        
        # Get password
        password = os.getenv("SUPABASE_DB_PASSWORD", "")
        if not password:
            print("❌ ERROR: SUPABASE_DB_PASSWORD is not set")
            print("You need to set this secret in Replit environment variables")
            return None
        
        # Format PostgreSQL connection string
        postgres_url = f"postgresql://postgres:{password}@db.{project_ref}.supabase.co:5432/postgres"
        masked_url = postgres_url.replace(password, "********")
        print(f"✅ Converted to PostgreSQL format: {masked_url}")
        
        return postgres_url
    
    print(f"❌ Unrecognized URL format: {url[:20]}...")
    return None

def test_sqlite_connection():
    """Test SQLite database connection."""
    print("\nTesting SQLite Connection:")
    print("-" * 30)
    
    try:
        import sqlite3
        conn = sqlite3.connect("stock_data.db")
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        if tables:
            print(f"✅ SQLite connection successful, found {len(tables)} tables")
            print(f"Tables: {', '.join([t[0] for t in tables])}")
        else:
            print("ℹ️ SQLite connection successful but no tables found")
        
        conn.close()
        return True
    except Exception as e:
        print(f"❌ SQLite connection error: {str(e)}")
        return False

def test_postgres_connection(postgres_url):
    """Test PostgreSQL connection with the formatted URL."""
    if not postgres_url:
        return False
    
    print("\nTesting PostgreSQL Connection:")
    print("-" * 30)
    
    try:
        import psycopg2
        
        # Set a short timeout to avoid hanging
        print("Attempting connection (5 second timeout)...")
        conn = psycopg2.connect(postgres_url, connect_timeout=5)
        cursor = conn.cursor()
        
        # Run a simple query
        cursor.execute("SELECT current_timestamp")
        result = cursor.fetchone()
        print(f"✅ PostgreSQL connection successful!")
        print(f"Server timestamp: {result[0]}")
        
        # Close connection
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ PostgreSQL connection error: {str(e)}")
        return False

def update_config_file():
    """Update the config.py file if needed."""
    print("\nUpdating config.py:")
    print("-" * 30)
    
    try:
        import re
        
        # Read current config
        with open("config.py", "r") as file:
            config_content = file.read()
        
        # Check if SQLite is already set as default
        if "DB_PATH = " in config_content and "DATABASE_URL = " in config_content:
            print("✅ Config file already has database configuration")
            
            # Ensure SQLite is prioritized as fallback
            if "# Always use SQLite" not in config_content:
                print("ℹ️ Adding comment to clarify SQLite fallback")
                new_content = config_content.replace(
                    "DB_PATH = ",
                    "# Use SQLite as reliable fallback when Supabase is unavailable\nDB_PATH = "
                )
                with open("config.py", "w") as file:
                    file.write(new_content)
                print("✅ Updated config.py with fallback clarification")
        else:
            print("❌ Config file does not have expected database configuration")
        
        return True
    except Exception as e:
        print(f"❌ Error updating config file: {str(e)}")
        return False

def main():
    """Main function to diagnose and fix Supabase connection issues."""
    print("\n=== Supabase Connection Diagnostics ===\n")
    
    # Step 1: Get current configuration
    config = get_supabase_config()
    
    # Step 2: Analyze DATABASE_URL format
    postgres_url = analyze_database_url(config["database_url"])
    
    # Step 3: Test SQLite connection as fallback
    sqlite_ok = test_sqlite_connection()
    
    # Step 4: Test PostgreSQL connection if URL formatting was successful
    postgres_ok = False
    if postgres_url:
        postgres_ok = test_postgres_connection(postgres_url)
    
    # Step 5: Update config file if needed
    update_config_file()
    
    # Summary
    print("\n=== Diagnostic Summary ===")
    print("SQLite fallback: " + ("✅ Working" if sqlite_ok else "❌ Not working"))
    print("Supabase PostgreSQL: " + ("✅ Working" if postgres_ok else "❌ Not working"))
    
    if postgres_ok:
        print("\n✅ Success! Your Supabase connection is working.")
    elif sqlite_ok:
        print("\nℹ️ Fallback mode: Your app will use SQLite for local storage.")
        print("This is normal in Replit as external database connections may be restricted.")
        print("Your app will continue to function normally with local data storage.")
    else:
        print("\n❌ Critical error: Neither Supabase nor SQLite connections are working.")
        print("Please check your configuration and try again.")

if __name__ == "__main__":
    main()