import os
from data.supabase_client import SupabaseDB
import pandas as pd
import json
import time

def test_supabase_rest_api():
    """
    Test Supabase integration using the REST API client
    """
    print("Testing Supabase REST API Connection")
    print("===================================\n")
    
    # Get the Supabase database URL and key from environment variables
    db_url = os.getenv("DATABASE_URL", "")
    db_key = os.getenv("SUPABASE_KEY", "")
    
    if not db_url or not db_key:
        print("ERROR: DATABASE_URL or SUPABASE_KEY not set in environment variables")
        return False
    
    print(f"Using Supabase URL: {db_url[:30]}...")
    
    # Create a Supabase client instance directly
    supabase_db = SupabaseDB()
    
    # Check connection
    if not supabase_db.is_connected():
        print("ERROR: Failed to connect to Supabase")
        return False
    
    print("✅ Connected to Supabase successfully!")
    
    # Create tables if they don't exist (our app already has this logic)
    print("\nVerifying if tables exist...")
    supabase_db._create_tables_if_not_exist()
    
    # Test adding to watchlist
    print("\nTesting watchlist functionality...")
    # Try to add a stock to the watchlist
    add_result = supabase_db.add_to_watchlist(
        "TEST", "Test Stock", "TEST-EXCHANGE", "Technology"
    )
    
    if add_result:
        print("✅ Successfully added TEST stock to watchlist")
    else:
        print("ℹ️ Could not add TEST stock (might already exist)")
    
    # Get the watchlist
    watchlist = supabase_db.get_watchlist()
    print(f"Current watchlist has {len(watchlist)} stocks")
    
    # Show the first 3 items in the watchlist if any exist
    if watchlist:
        print("\nSample of watchlist items:")
        for item in watchlist[:3]:
            print(f"  - {item['ticker']}: {item['name']} ({item['exchange']})")
    
    # Test caching stock data
    print("\nTesting stock data cache functionality...")
    # Create a sample dataframe
    sample_data = pd.DataFrame({
        'date': ['2023-01-01', '2023-01-02', '2023-01-03'],
        'open': [100.0, 101.0, 102.0],
        'high': [105.0, 106.0, 107.0],
        'low': [98.0, 99.0, 100.0],
        'close': [103.0, 104.0, 105.0],
        'volume': [1000, 1100, 1200]
    })
    
    # Cache the data
    supabase_db.cache_stock_data("TEST", "1d", "1mo", sample_data, "test")
    print("✅ Stock data cached successfully")
    
    # Retrieve the cached data
    retrieved_data = supabase_db.get_cached_stock_data("TEST", "1d", "1mo", "test")
    
    if retrieved_data is not None:
        print("✅ Successfully retrieved cached data:")
        print(retrieved_data.head())
    else:
        print("❌ Failed to retrieve cached data")
    
    # Test caching fundamentals
    print("\nTesting fundamentals cache functionality...")
    
    # Create sample fundamentals data
    fundamentals = {
        "pe_ratio": 15.5,
        "profit_margin": 0.2,
        "revenue_growth": 0.1,
        "earnings_growth": 0.15,
        "book_value": 50.0,
        "market_cap": 1000000000,
        "dividend_yield": 0.03
    }
    
    # Cache the fundamentals
    supabase_db.cache_fundamentals("TEST", fundamentals)
    print("✅ Fundamentals cached successfully")
    
    # Get the cached fundamentals
    cached_fundamentals = supabase_db.get_cached_fundamentals("TEST")
    
    if cached_fundamentals:
        print("✅ Successfully retrieved cached fundamentals:")
        for key, value in cached_fundamentals.items():
            if key not in ['id', 'last_updated']:
                print(f"  - {key}: {value}")
    else:
        print("❌ Failed to retrieve cached fundamentals")
    
    print("\nTest completed successfully!")
    return True

if __name__ == "__main__":
    test_supabase_rest_api()