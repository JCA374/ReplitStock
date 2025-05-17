import os
import psycopg2
from sqlalchemy import create_engine, text

def fix_supabase_connection():
    """
    Fix the Supabase connection by testing the connection with the updated connection string format.
    """
    # Get the base URL from environment
    database_url = os.getenv("DATABASE_URL", "")
    password = os.getenv("SUPABASE_DB_PASSWORD", "")
    
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        return False
    
    if not password:
        print("ERROR: SUPABASE_DB_PASSWORD environment variable not set")
        return False
    
    # Format into a proper PostgreSQL connection string
    if database_url.startswith("https://") and "supabase.co" in database_url:
        # Extract project reference from the URL
        project_ref = database_url.split("//")[1].split(".")[0]
        
        # Format PostgreSQL connection string
        postgres_url = f"postgresql://postgres:{password}@db.{project_ref}.supabase.co:5432/postgres"
        
        # Hide actual password in logs
        masked_url = postgres_url.replace(password, "********")
        print(f"Converted Supabase URL to PostgreSQL format: {masked_url}")
    else:
        # Use as-is if already in PostgreSQL format
        postgres_url = database_url
        print("Using provided DATABASE_URL as-is")
    
    # Test the connection
    try:
        print("Testing PostgreSQL connection...")
        conn = psycopg2.connect(postgres_url)
        cursor = conn.cursor()
        
        # Run a simple query
        cursor.execute("SELECT current_timestamp;")
        result = cursor.fetchone()
        print(f"Current database timestamp: {result[0]}")
        
        # Close connection
        cursor.close()
        conn.close()
        print("✅ Supabase connection test successful!")
        return True
    except Exception as e:
        print(f"❌ Error connecting to Supabase database: {str(e)}")
        return False

if __name__ == "__main__":
    print("\nSupabase Connection Fix Tool")
    print("===========================\n")
    success = fix_supabase_connection()
    
    if success:
        print("\nYour Supabase connection is now working correctly!")
        print("You may need to update your application to use the correct connection string format.")
    else:
        print("\nUnable to fix Supabase connection. Please check your credentials and try again.")