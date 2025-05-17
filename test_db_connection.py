import os
import psycopg2
import pandas as pd
from sqlalchemy import create_engine, text

def test_connection():
    """Test connection to PostgreSQL database using DATABASE_URL."""
    # Get the connection URL from environment variables
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("Error: DATABASE_URL environment variable is not set!")
        return
    
    print(f"Testing connection to Supabase database...")
    
    # For Supabase, the connection string should be in the format:
    # postgresql://postgres:[YOUR-PASSWORD]@db.dgfudgctsgmcjtgdoxsi.supabase.co:5432/postgres
    
    try:
        # Connect to the database
        conn = psycopg2.connect(database_url)
        print("✅ Connection successful!")
        
        # Create a cursor
        cur = conn.cursor()
        
        # Create a test table
        print("Creating test table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS test_table (
                id SERIAL PRIMARY KEY,
                ticker VARCHAR(10) NOT NULL,
                company_name VARCHAR(100),
                price NUMERIC(10, 2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert some test data
        print("Inserting test data...")
        test_stocks = [
            ('AAPL', 'Apple Inc.', 190.25),
            ('MSFT', 'Microsoft Corporation', 420.15),
            ('TSLA', 'Tesla Inc.', 242.50),
            ('NVDA', 'NVIDIA Corporation', 950.75),
            ('GOOGL', 'Alphabet Inc.', 180.20)
        ]
        
        for ticker, name, price in test_stocks:
            cur.execute(
                "INSERT INTO test_table (ticker, company_name, price) VALUES (%s, %s, %s)",
                (ticker, name, price)
            )
        
        # Commit the changes
        conn.commit()
        
        # Query the data to verify it was inserted
        print("\nRetrieving data from test_table:")
        cur.execute("SELECT * FROM test_table")
        rows = cur.fetchall()
        
        # Print column names and data
        colnames = [desc[0] for desc in cur.description]
        print(f"Columns: {colnames}")
        
        # Print each row
        for row in rows:
            print(row)
        
        # Close cursor and connection
        cur.close()
        conn.close()
        
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_connection()