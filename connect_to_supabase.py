import os
import psycopg2
import pandas as pd
from sqlalchemy import create_engine

def create_postgres_connection_sts.getenv("SUPABASE_PASSWORD", "postgres")ring():
    """
    Convert the Supabase URL to a proper PostgreSQL connection string
    """
    # Get the DATABASE_URL from environment
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        print("ERROR: DATABASE_URL environment variable not set")
        return None
    
    print(f"Original URL format: {db_url[:30]}...")
    
    # For Supabase, we need to format the connection string as:
    # postgresql://username:password@hostname:port/database
    
    # If it's a standard PostgreSQL connection string already, return it
    if db_url.startswith('postgresql://'):
        return db_url
    
    # If it's a Supabase URL format, we need to format it
    # Format: https://[project-ref].supabase.co
    if 'supabase.co' in db_url:
        # Extract the project reference
        project_ref = db_url.split('//')[1].split('.')[0]
        
        # Get password from the dedicated environment variable
        password = os.getenv("DATABASE_PASSWORD", "")
        
        if not password:
            print("ERROR: DATABASE_PASSWORD not set in environment variables")
            return None
            
        # Standard port for PostgreSQL
        port = 5432
        
        # Database name in Supabase is typically 'postgres'
        database = 'postgres'
        
        # Construct the connection string
        postgres_url = f"postgresql://postgres:{password}@db.{project_ref}.supabase.co:{port}/{database}"
        print(f"Constructed PostgreSQL URL: {postgres_url[:30]}...")
        
        return postgres_url
    
    return db_url

def test_connection():
    """Test connection to the Supabase PostgreSQL database."""
    # Get properly formatted connection string
    conn_string = create_postgres_connection_string()
    
    if not conn_string:
        return False
    
    try:
        # Connect using psycopg2
        print("Attempting to connect with psycopg2...")
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()
        
        # Test a simple query
        cursor.execute("SELECT current_timestamp;")
        result = cursor.fetchone()
        print(f"Current timestamp from database: {result[0]}")
        
        # Create a test table
        print("\nCreating test_stocks table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_stocks (
            id SERIAL PRIMARY KEY,
            ticker VARCHAR(20) NOT NULL,
            company_name VARCHAR(100),
            price DECIMAL(10,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Insert some sample data
        print("Inserting sample data...")
        stocks = [
            ('AAPL', 'Apple Inc.', 182.63),
            ('MSFT', 'Microsoft Corporation', 420.55),
            ('GOOGL', 'Alphabet Inc.', 176.20),
            ('AMZN', 'Amazon.com Inc.', 178.15),
            ('TSLA', 'Tesla Inc.', 245.9)
        ]
        
        for stock in stocks:
            cursor.execute(
                "INSERT INTO test_stocks (ticker, company_name, price) VALUES (%s, %s, %s)",
                stock
            )
        
        # Commit the transaction
        conn.commit()
        
        # Query the data
        cursor.execute("SELECT * FROM test_stocks ORDER BY price DESC")
        rows = cursor.fetchall()
        
        print("\nStock data inserted (ordered by price):")
        # Get column names
        col_names = [desc[0] for desc in cursor.description]
        print(f"Columns: {col_names}")
        
        # Print rows
        for row in rows:
            print(row)
        
        # Close the connection
        cursor.close()
        conn.close()
        
        print("\n✅ Successfully connected to Supabase and created test table!")
        return True
        
    except Exception as e:
        print(f"❌ Error connecting to database: {str(e)}")
        return False
    
if __name__ == "__main__":
    print("Supabase Database Connection Test")
    print("================================\n")
    test_connection()