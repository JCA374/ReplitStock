import os
from supabase import create_client, Client
import time

def setup_supabase_tables():
    """
    Set up the required tables in the Supabase database.
    This will create the tables needed for the stock analysis app.
    """
    print("Setting up Supabase database tables")
    print("==================================\n")
    
    # Get Supabase credentials from environment variables
    supabase_url = os.getenv("DATABASE_URL", "")
    supabase_key = os.getenv("SUPABASE_KEY", "")
    
    if not supabase_url or not supabase_key:
        print("ERROR: DATABASE_URL or SUPABASE_KEY not set in environment variables")
        return False
    
    # Ensure URL starts with https://
    if supabase_url and not supabase_url.startswith("https://"):
        supabase_url = "https://" + supabase_url
    
    print(f"Connecting to Supabase at {supabase_url[:30]}...")
    
    try:
        # Initialize the Supabase client
        client = create_client(supabase_url, supabase_key)
        print("✅ Connected to Supabase successfully!")
        
        # Instead of using SQL directly, we'll try using Supabase's REST API
        # to interact with the database.
        
        # 1. Test if watchlist table exists by trying to access it
        print("\nChecking and creating watchlist table...")
        try:
            # Try to fetch a row to see if table exists
            client.table("watchlist").select("*").limit(1).execute()
            print("✅ Watchlist table already exists!")
        except Exception as e:
            if "does not exist" in str(e):
                print("Watchlist table doesn't exist, let's create it through the Supabase dashboard")
                print("\nIMPORTANT: Please create the following tables in your Supabase dashboard:")
                print("\n1. watchlist")
                print("   - id: serial primary key")
                print("   - ticker: varchar(20), unique")
                print("   - name: varchar(100)")
                print("   - exchange: varchar(50)")
                print("   - sector: varchar(50)")
                print("   - added_date: varchar(20)")
                
                print("\n2. stock_data_cache")
                print("   - id: serial primary key")
                print("   - ticker: varchar(20)")
                print("   - timeframe: varchar(10)")
                print("   - period: varchar(10)")
                print("   - data: text")
                print("   - timestamp: bigint")
                print("   - source: varchar(20)")
                print("   - Add a unique constraint on (ticker, timeframe, period, source)")
                
                print("\n3. fundamentals_cache")
                print("   - id: serial primary key")
                print("   - ticker: varchar(20), unique")
                print("   - pe_ratio: float")
                print("   - profit_margin: float")
                print("   - revenue_growth: float")
                print("   - earnings_growth: float")
                print("   - book_value: float")
                print("   - market_cap: float")
                print("   - dividend_yield: float")
                print("   - last_updated: bigint")
                
                print("\nPlease confirm once you've created these tables.")
                return False
            else:
                raise
        
        print("✅ Fundamentals cache table created")
        
        # Test inserting data into the watchlist
        print("\nTesting table access by adding a test stock to watchlist...")
        current_date = time.strftime("%Y-%m-%d")
        
        test_stock = {
            "ticker": "TEST-DB",
            "name": "Test Stock",
            "exchange": "TEST",
            "sector": "Technology",
            "added_date": current_date
        }
        
        response = client.table("watchlist").insert(test_stock).execute()
        print("✅ Test stock added to watchlist")
        
        # Retrieve the watchlist to verify
        print("\nRetrieving watchlist data to verify:")
        response = client.table("watchlist").select("*").execute()
        if response.data:
            print(f"Found {len(response.data)} stocks in watchlist:")
            for stock in response.data:
                print(f"  - {stock['ticker']}: {stock['name']} ({stock['exchange']})")
        else:
            print("No stocks found in watchlist")
            
        print("\n✅ Database setup completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error setting up database: {str(e)}")
        return False

if __name__ == "__main__":
    setup_supabase_tables()