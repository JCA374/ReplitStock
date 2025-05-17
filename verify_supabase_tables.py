import os
from supabase import create_client
import time

def verify_supabase_setup():
    """Verify that all tables exist and are accessible in Supabase."""
    print("Verifying Supabase Database Setup")
    print("=================================\n")
    
    # Get Supabase credentials from environment variables
    supabase_url = os.getenv("DATABASE_URL", "")
    supabase_key = os.getenv("SUPABASE_KEY", "")
    
    if not supabase_url or not supabase_key:
        print("ERROR: DATABASE_URL or SUPABASE_KEY not set in environment variables")
        return False
    
    # Ensure URL starts with https://
    if supabase_url and not supabase_url.startswith("https://"):
        supabase_url = "https://" + supabase_url
    
    try:
        # Initialize the Supabase client
        client = create_client(supabase_url, supabase_key)
        print(f"✅ Connected to Supabase at {supabase_url}")
        
        # Check if tables exist
        print("\nChecking tables...")
        tables = ["watchlist", "stock_data_cache", "fundamentals_cache"]
        accessible_tables = 0
        
        for table in tables:
            try:
                # Try to fetch a row from each table
                response = client.table(table).select("*").limit(1).execute()
                print(f"✅ Table '{table}' exists and is accessible")
                accessible_tables += 1
            except Exception as e:
                print(f"❌ Error accessing table '{table}': {str(e)}")
        
        if accessible_tables == len(tables):
            print(f"\n✅ All {len(tables)} tables are accessible! Database is ready for use.")
            
            # Try fetching data from the watchlist
            print("\nFetching test data from watchlist:")
            response = client.table("watchlist").select("*").execute()
            
            if response.data:
                print(f"Found {len(response.data)} stocks in watchlist:")
                for stock in response.data:
                    print(f"  - {stock['ticker']}: {stock['name']} ({stock['exchange']})")
            else:
                print("No data found in watchlist table.")
                
                # Try inserting a test stock
                print("\nInserting a test stock into watchlist...")
                current_date = time.strftime("%Y-%m-%d")
                
                test_data = {
                    "ticker": "TEST123",
                    "name": "Test Stock",
                    "exchange": "TEST",
                    "sector": "Technology",
                    "added_date": current_date
                }
                
                try:
                    response = client.table("watchlist").insert(test_data).execute()
                    print("✅ Test stock added successfully!")
                except Exception as e:
                    print(f"❌ Error adding test stock: {str(e)}")
            
            return True
        else:
            print(f"\n⚠️ Only {accessible_tables}/{len(tables)} tables are accessible.")
            return False
    
    except Exception as e:
        print(f"❌ Error connecting to Supabase: {str(e)}")
        return False

if __name__ == "__main__":
    verify_supabase_setup()