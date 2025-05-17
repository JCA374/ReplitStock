import os
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, MetaData, Table, text
import time
import psycopg2

def test_supabase_connection():
    """Test connection to Supabase PostgreSQL database and create a test table."""
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        return False
    
    print("Attempting to connect to Supabase directly with psycopg2...")
    
    try:
        # First, try direct connection using psycopg2 instead of SQLAlchemy
        conn = psycopg2.connect(database_url)
        print("Connected to database successfully via psycopg2!")
        
        # Create a cursor
        cursor = conn.cursor()
        
        # Create a test table
        print("Creating test table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_stocks (
                id SERIAL PRIMARY KEY,
                ticker VARCHAR(20) NOT NULL,
                name VARCHAR(100),
                price NUMERIC(10, 2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert some test data
        print("Inserting test data...")
        test_data = [
            ("AAPL", "Apple Inc.", 175.25),
            ("MSFT", "Microsoft Corporation", 332.42),
            ("GOOGL", "Alphabet Inc.", 138.21),
            ("TSLA", "Tesla, Inc.", 250.98),
            ("AMZN", "Amazon.com, Inc.", 142.55)
        ]
        
        for ticker, name, price in test_data:
            cursor.execute(
                "INSERT INTO test_stocks (ticker, name, price) VALUES (%s, %s, %s)",
                (ticker, name, price)
            )
        
        # Commit the transaction
        conn.commit()
        
        # Query and display the data
        print("\nQuerying test data:")
        cursor.execute("SELECT * FROM test_stocks")
        rows = cursor.fetchall()
        
        # Display the column names
        col_names = [desc[0] for desc in cursor.description]
        print(f"Columns: {col_names}")
        
        # Display the data
        for row in rows:
            print(row)
        
        # Close the cursor and connection
        cursor.close()
        conn.close()
        
        print("\nTest completed successfully!")
        return True
    
    except Exception as e:
        print(f"Error connecting with psycopg2: {str(e)}")
    
    # If psycopg2 direct connection fails, try with SQLAlchemy
    print("\nAttempting with SQLAlchemy as fallback...")
    
    try:
        # Create engine with the PostgreSQL connection string
        engine = create_engine(database_url)
        
        # Test connection
        with engine.connect() as conn:
            # Check connection
            result = conn.execute(text("SELECT 1"))
            print("Connection successful!")
            
            # Create a test table
            print("Creating test table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS test_stocks (
                    id SERIAL PRIMARY KEY,
                    ticker VARCHAR(20) NOT NULL,
                    name VARCHAR(100),
                    price NUMERIC(10, 2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Insert some test data
            print("Inserting test data...")
            test_data = [
                ("AAPL", "Apple Inc.", 175.25),
                ("MSFT", "Microsoft Corporation", 332.42),
                ("GOOGL", "Alphabet Inc.", 138.21),
                ("TSLA", "Tesla, Inc.", 250.98),
                ("AMZN", "Amazon.com, Inc.", 142.55)
            ]
            
            for ticker, name, price in test_data:
                conn.execute(text(
                    "INSERT INTO test_stocks (ticker, name, price) VALUES (:ticker, :name, :price)"
                ), {"ticker": ticker, "name": name, "price": price})
            
            # Query and display the data
            print("\nQuerying test data:")
            result = conn.execute(text("SELECT * FROM test_stocks"))
            rows = result.fetchall()
            
            # Convert to DataFrame for nice display
            df = pd.DataFrame(rows, columns=result.keys())
            print(df)
            
            print("\nTest completed successfully!")
            return True
            
    except Exception as e:
        print(f"Error connecting to database: {str(e)}")
        return False

if __name__ == "__main__":
    test_supabase_connection()