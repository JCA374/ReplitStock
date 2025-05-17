import os
import requests
import json

def create_tables_via_api():
    """Create tables in Supabase using the REST API."""
    
    # Get Supabase credentials
    supabase_url = os.getenv("DATABASE_URL", "")
    supabase_key = os.getenv("SUPABASE_KEY", "")
    
    if not supabase_url or not supabase_key:
        print("ERROR: DATABASE_URL or SUPABASE_KEY not set")
        return False
    
    # Ensure URL format is correct
    if supabase_url.startswith("https://"):
        # Extract the project reference
        project_ref = supabase_url.split("//")[1].split(".")[0]
        base_url = f"https://{project_ref}.supabase.co"
    else:
        base_url = supabase_url
    
    print(f"Using Supabase URL: {base_url}")
    
    # SQL for creating the tables
    create_tables_sql = """
    -- Create watchlist table
    CREATE TABLE IF NOT EXISTS public.watchlist (
        id SERIAL PRIMARY KEY,
        ticker VARCHAR(20) NOT NULL UNIQUE,
        name VARCHAR(100),
        exchange VARCHAR(50),
        sector VARCHAR(50),
        added_date VARCHAR(20)
    );

    -- Create stock_data_cache table
    CREATE TABLE IF NOT EXISTS public.stock_data_cache (
        id SERIAL PRIMARY KEY,
        ticker VARCHAR(20) NOT NULL,
        timeframe VARCHAR(10) NOT NULL,
        period VARCHAR(10) NOT NULL,
        data TEXT,
        timestamp BIGINT,
        source VARCHAR(20),
        CONSTRAINT stock_data_cache_unique UNIQUE (ticker, timeframe, period, source)
    );

    -- Create fundamentals_cache table
    CREATE TABLE IF NOT EXISTS public.fundamentals_cache (
        id SERIAL PRIMARY KEY,
        ticker VARCHAR(20) NOT NULL UNIQUE,
        pe_ratio FLOAT,
        profit_margin FLOAT,
        revenue_growth FLOAT,
        earnings_growth FLOAT,
        book_value FLOAT,
        market_cap FLOAT,
        dividend_yield FLOAT,
        last_updated BIGINT
    );
    """
    
    # Execute SQL via REST API
    try:
        # Endpoint for SQL execution (PostgreSQL REST API)
        sql_url = f"{base_url}/rest/v1/sql"
        
        # Headers
        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        
        # Query
        data = {
            "query": create_tables_sql
        }
        
        # Make the request
        print("Executing SQL to create tables...")
        response = requests.post(sql_url, headers=headers, json=data)
        
        # Check response
        if response.status_code == 200:
            print("✅ Tables created successfully!")
            return True
        else:
            print(f"❌ Error creating tables: {response.status_code}")
            print(response.text)
            
            # Try to connect to see if tables were created anyway
            print("\nChecking if tables exist...")
            check_tables(base_url, supabase_key)
            
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def check_tables(base_url, api_key):
    """Check if tables exist by trying to access them."""
    tables = ["watchlist", "stock_data_cache", "fundamentals_cache"]
    
    headers = {
        "apikey": api_key,
        "Authorization": f"Bearer {api_key}"
    }
    
    for table in tables:
        try:
            url = f"{base_url}/rest/v1/{table}?limit=1"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                print(f"✅ Table '{table}' exists and is accessible")
            else:
                print(f"❌ Table '{table}' might not exist or is inaccessible: {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"❌ Error checking table '{table}': {str(e)}")

if __name__ == "__main__":
    print("Creating tables in Supabase...")
    create_tables_via_api()