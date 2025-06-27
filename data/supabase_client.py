import os
import json
import pandas as pd
from datetime import datetime, timedelta
import time
from supabase import create_client, Client
from config import CACHE_EXPIRATION

class SupabaseDB:
    """
    Supabase database client wrapper for the stock analysis app.
    Uses the Supabase REST API to store and retrieve data.
    """
    
    def __init__(self):
        # Get Supabase credentials from environment variables
        self.supabase_url = os.getenv("SUPABASE_URL", "")
        self.supabase_key = os.getenv("SUPABASE_KEY", "")
        
        # Ensure URL starts with https://
        if self.supabase_url and not self.supabase_url.startswith("https://"):
            self.supabase_url = "https://" + self.supabase_url
        
        self.client = None
        if self.supabase_url and self.supabase_key:
            try:
                self.client = create_client(self.supabase_url, self.supabase_key)
                print(f"Connected to Supabase at {self.supabase_url}")
                # Initialize tables after successful connection
                self._create_tables_if_not_exist()
            except Exception as e:
                print(f"Error connecting to Supabase: {str(e)}")
                self.client = None

    def is_connected(self):
        """Check if connected to Supabase."""
        if not self.client:
            return False

        try:
            # Perform a simple test query to verify connection
            self.client.table("watchlist").select("id").limit(1).execute()
            return True
        except Exception as e:
            # If connection test fails, log it but don't repeatedly try
            if not hasattr(self, '_connection_error_logged'):
                print(f"Supabase connection test failed: {e}")
                self._connection_error_logged = True
            return False

    def _create_tables_if_not_exist(self):
        """
        Check if necessary tables exist in Supabase.
        Attempt to create missing tables if permissions allow.
        """
        if not self.is_connected():
            return

        # Tables we expect to exist
        tables = ["watchlist", "watchlist_collections", "watchlist_memberships", 
                "stock_data_cache", "fundamentals_cache", "analysis_results"]
        working_tables = 0

        for table in tables:
            try:
                # Try fetching a single row to verify table exists and is accessible
                response = self.client.table(table).select("*").limit(1).execute()
                print(f"Table {table} exists and is accessible")
                working_tables += 1
            except Exception as e:
                print(f"Table {table} might not exist: {str(e)}")

                # If we have admin permissions, try to create the missing table
                if table == "watchlist":
                    try:
                        self.client.postgrest.rpc(
                            'create_watchlist_table').execute()
                        print(f"Created {table} table")
                    except Exception as create_err:
                        print(f"Cannot create {table} table: {create_err}")

                elif table == "stock_data_cache":
                    try:
                        self.client.postgrest.rpc(
                            'create_stock_data_cache_table').execute()
                        print(f"Created {table} table")
                    except Exception as create_err:
                        print(f"Cannot create {table} table: {create_err}")

                elif table == "fundamentals_cache":
                    try:
                        self.client.postgrest.rpc(
                            'create_fundamentals_cache_table').execute()
                        print(f"Created {table} table")
                    except Exception as create_err:
                        print(f"Cannot create {table} table: {create_err}")

                elif table == "analysis_results":
                    try:
                        # SQL to create analysis_results table
                        sql = """
                        CREATE TABLE IF NOT EXISTS public.analysis_results (
                            id SERIAL PRIMARY KEY,
                            ticker VARCHAR(20) NOT NULL,
                            analysis_date VARCHAR(50) NOT NULL,
                            price FLOAT,
                            tech_score INTEGER,
                            signal VARCHAR(10),
                            above_ma40 BOOLEAN,
                            above_ma4 BOOLEAN,
                            rsi_value FLOAT,
                            rsi_above_50 BOOLEAN,
                            near_52w_high BOOLEAN,
                            pe_ratio FLOAT,
                            profit_margin FLOAT,
                            revenue_growth FLOAT,
                            is_profitable BOOLEAN,
                            data_source VARCHAR(20),
                            last_updated BIGINT,
                            CONSTRAINT analysis_results_unique UNIQUE (ticker, analysis_date)
                        );

                        CREATE INDEX IF NOT EXISTS idx_analysis_results_ticker ON public.analysis_results(ticker);
                        CREATE INDEX IF NOT EXISTS idx_analysis_results_date ON public.analysis_results(analysis_date);
                        """

                        # Try to create table using RPC (if you have an RPC function for this)
                        self.client.postgrest.rpc(
                            'run_sql', {'sql': sql}).execute()
                        print(f"Created {table} table")
                    except Exception as create_err:
                        print(f"Cannot create {table} table: {create_err}")
                        print(
                            "Consider manually running the SQL script to create the analysis_results table")

        if working_tables == len(tables):
            print("All tables are accessible! Database is ready.")
        else:
            print(f"{working_tables}/{len(tables)} tables are accessible. Some features may not work correctly.")

            # Provide SQL to create the analysis_results table for manual execution
            if "analysis_results" not in [table for table in tables if self.client.table(table).select("*").limit(1).execute()]:
                print("\nRun this SQL to create the analysis_results table:")
                print("""
    CREATE TABLE IF NOT EXISTS public.analysis_results (
        id SERIAL PRIMARY KEY,
        ticker VARCHAR(20) NOT NULL,
        analysis_date VARCHAR(50) NOT NULL,
        price FLOAT,
        tech_score INTEGER,
        signal VARCHAR(10),
        above_ma40 BOOLEAN,
        above_ma4 BOOLEAN,
        rsi_value FLOAT,
        rsi_above_50 BOOLEAN,
        near_52w_high BOOLEAN,
        pe_ratio FLOAT,
        profit_margin FLOAT,
        revenue_growth FLOAT,
        is_profitable BOOLEAN,
        data_source VARCHAR(20),
        last_updated BIGINT,
        CONSTRAINT analysis_results_unique UNIQUE (ticker, analysis_date)
    );

    CREATE INDEX IF NOT EXISTS idx_analysis_results_ticker ON public.analysis_results(ticker);
    CREATE INDEX IF NOT EXISTS idx_analysis_results_date ON public.analysis_results(analysis_date);
                """)

    # Watchlist collection methods
    def get_all_watchlist_collections(self):
        """Get all watchlist collections from Supabase."""
        if not self.is_connected():
            return []
        
        try:
            response = self.client.table("watchlist_collections").select("*").execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Error getting watchlist collections: {e}")
            return []

    def create_watchlist_collection(self, name, description="", is_default=False):
        """Create a new watchlist collection."""
        if not self.is_connected():
            return None
        
        try:
            data = {
                "name": name,
                "description": description,
                "created_date": datetime.now().strftime("%Y-%m-%d"),
                "is_default": is_default
            }
            response = self.client.table("watchlist_collections").insert(data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error creating watchlist collection: {e}")
            return None

    def add_to_watchlist_collection(self, collection_id, ticker):
        """Add a stock to a specific watchlist collection."""
        if not self.is_connected():
            return False
        
        try:
            data = {
                "collection_id": collection_id,
                "ticker": ticker,
                "added_date": datetime.now().strftime("%Y-%m-%d")
            }
            self.client.table("watchlist_memberships").insert(data).execute()
            return True
        except Exception as e:
            print(f"Error adding to watchlist collection: {e}")
            return False

    def get_watchlist_collection_stocks(self, collection_id):
        """Get all stocks in a specific watchlist collection."""
        if not self.is_connected():
            return []
        
        try:
            response = self.client.table("watchlist_memberships")\
                .select("ticker")\
                .eq("collection_id", collection_id)\
                .execute()
            return [item['ticker'] for item in response.data] if response.data else []
        except Exception as e:
            print(f"Error getting watchlist stocks: {e}")
            return []

    def remove_from_watchlist_collection(self, collection_id, ticker):
        """Remove a stock from a watchlist collection."""
        if not self.is_connected():
            return False
        
        try:
            self.client.table("watchlist_memberships")\
                .delete()\
                .eq("collection_id", collection_id)\
                .eq("ticker", ticker)\
                .execute()
            return True
        except Exception as e:
            print(f"Error removing from watchlist: {e}")
            return False

    # Legacy watchlist methods (for backward compatibility)
    def add_to_watchlist(self, ticker, name, exchange="", sector=""):
        """Add a ticker to the watchlist."""
        if not self.is_connected():
            return False
        
        try:
            current_date = datetime.now().strftime("%Y-%m-%d")
            
            # Check if already exists
            response = self.client.table("watchlist").select("*").eq("ticker", ticker).execute()
            if response.data:
                return False  # Already exists
            
            # Insert new record
            data = {
                "ticker": ticker,
                "name": name,
                "exchange": exchange,
                "sector": sector,
                "added_date": current_date
            }
            
            self.client.table("watchlist").insert(data).execute()
            return True
        except Exception as e:
            print(f"Error adding to watchlist: {str(e)}")
            return False
    
    def remove_from_watchlist(self, ticker):
        """Remove a ticker from the watchlist."""
        if not self.is_connected():
            return
        
        try:
            self.client.table("watchlist").delete().eq("ticker", ticker).execute()
        except Exception as e:
            print(f"Error removing from watchlist: {str(e)}")
    
    def get_watchlist(self):
        """Get all tickers in the watchlist."""
        if not self.is_connected():
            return []
        
        try:
            response = self.client.table("watchlist").select("*").order("added_date", desc=True).execute()
            return response.data
        except Exception as e:
            print(f"Error getting watchlist: {str(e)}")
            return []
    
    # Stock data cache methods
    def cache_stock_data(self, ticker, timeframe, period, data, source):
        """Cache stock data to reduce API calls."""
        if not self.is_connected():
            return
        
        try:
            # Convert DataFrame to JSON for storage
            json_data = data.to_json()
            current_timestamp = int(time.time())
            
            # Check if record exists
            response = self.client.table("stock_data_cache").select("id").eq("ticker", ticker).eq("timeframe", timeframe).eq("period", period).eq("source", source).execute()
            
            if response.data:
                # Update existing record
                record_id = response.data[0]["id"]
                self.client.table("stock_data_cache").update({
                    "data": json_data,
                    "timestamp": current_timestamp
                }).eq("id", record_id).execute()
            else:
                # Insert new record
                self.client.table("stock_data_cache").insert({
                    "ticker": ticker,
                    "timeframe": timeframe,
                    "period": period,
                    "data": json_data,
                    "timestamp": current_timestamp,
                    "source": source
                }).execute()
        except Exception as e:
            print(f"Error caching stock data: {str(e)}")

    def get_cached_stock_data(self, ticker, timeframe, period, source):
        """Retrieve cached stock data if available and not expired."""
        if not self.is_connected():
            return None

        try:
            response = self.client.table("stock_data_cache").select("*").eq("ticker", ticker).eq(
                "timeframe", timeframe).eq("period", period).eq("source", source).execute()

            if response.data:
                record = response.data[0]
                current_timestamp = int(time.time())

                # Check if data needs to be refreshed
                if (current_timestamp - record["timestamp"]) < CACHE_EXPIRATION:
                    # Convert JSON back to DataFrame - fix warning using StringIO
                    import io
                    return pd.read_json(io.StringIO(record["data"]))

            return None
        except Exception as e:
            print(f"Error getting cached stock data: {e}")
            return None

    # Fundamentals cache methods
    def cache_fundamentals(self, ticker, fundamentals_data):
        """Cache fundamental data for a ticker."""
        if not self.is_connected():
            return
            
        try:
            current_timestamp = int(time.time())
            
            # Check if record exists
            response = self.client.table("fundamentals_cache").select("id").eq("ticker", ticker).execute()
            
            data = {
                "ticker": ticker,
                "pe_ratio": fundamentals_data.get("pe_ratio"),
                "profit_margin": fundamentals_data.get("profit_margin"),
                "revenue_growth": fundamentals_data.get("revenue_growth"),
                "earnings_growth": fundamentals_data.get("earnings_growth"),
                "book_value": fundamentals_data.get("book_value"),
                "market_cap": fundamentals_data.get("market_cap"),
                "dividend_yield": fundamentals_data.get("dividend_yield"),
                "last_updated": current_timestamp
            }
            
            if response.data:
                # Update existing record
                record_id = response.data[0]["id"]
                self.client.table("fundamentals_cache").update(data).eq("id", record_id).execute()
            else:
                # Insert new record
                self.client.table("fundamentals_cache").insert(data).execute()
        except Exception as e:
            print(f"Error caching fundamentals: {str(e)}")
    
    def get_cached_fundamentals(self, ticker):
        """Retrieve cached fundamental data if available and not expired."""
        if not self.is_connected():
            return None
            
        try:
            response = self.client.table("fundamentals_cache").select("*").eq("ticker", ticker).execute()
            
            if response.data:
                record = response.data[0]
                current_timestamp = int(time.time())
                
                # Check if data needs to be refreshed
                if (current_timestamp - record["last_updated"]) < CACHE_EXPIRATION:
                    return record
            
            return None
        except Exception as e:
            print(f"Error getting cached fundamentals: {str(e)}")
            return None
    
    def get_all_cached_stocks(self):
        """Get all unique stock tickers in the cache."""
        if not self.is_connected():
            return []
            
        try:
            response = self.client.table("stock_data_cache").select("ticker").execute()
            tickers = list(set([item["ticker"] for item in response.data]))
            return tickers
        except Exception as e:
            print(f"Error getting cached stocks: {str(e)}")
            return []
    
    def get_all_fundamentals(self):
        """Get fundamental data for all stocks in cache."""
        if not self.is_connected():
            return []
            
        try:
            response = self.client.table("fundamentals_cache").select("*").execute()
            return response.data
        except Exception as e:
            print(f"Error getting all fundamentals: {str(e)}")
            return []

    def store_analysis_result(self, ticker, analysis_data):
        """Store analysis result in Supabase."""
        if not self.is_connected():
            return False

        try:
            # Create a deep copy with all values converted to JSON-serializable formats
            import json

            # Convert all boolean values recursively
            def make_serializable(obj):
                if isinstance(obj, bool):
                    return 1 if obj else 0
                elif isinstance(obj, dict):
                    return {k: make_serializable(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [make_serializable(item) for item in obj]
                elif isinstance(obj, (int, float, str, type(None))):
                    return obj
                else:
                    # Convert any other types to string
                    return str(obj)

            # Create serializable copy of all data
            serializable_data = make_serializable(analysis_data)

            # Remove any fields that might cause issues
            if 'historical_data' in serializable_data:
                del serializable_data['historical_data']

            # Check if record exists
            response = self.client.table("analysis_results").select("id").eq(
                "ticker", ticker).eq("analysis_date", analysis_data['analysis_date']).execute()

            if response.data:
                # Update existing record
                record_id = response.data[0]["id"]
                self.client.table("analysis_results").update(
                    serializable_data).eq("id", record_id).execute()
            else:
                # Insert new record
                self.client.table("analysis_results").insert(
                    serializable_data).execute()

            return True
        except Exception as e:
            print(f"Error storing analysis result in Supabase: {e}")
            return False

    def get_analysis_results(self, ticker=None, cutoff_time=None):
        """Get analysis results from Supabase."""
        if not self.is_connected():
            return None

        try:
            # Build a basic query
            query = "analysis_results"

            # Set up filters
            filters = {}
            if ticker:
                filters['ticker'] = ticker

            # Try a more direct approach that should work with any client version
            try:
                response = self.client.from_(query).select('*')
                if ticker:
                    response = response.filter('ticker', 'eq', ticker)

                # Get data - different clients have different ways to execute
                try:
                    data = response.execute().data
                except AttributeError:
                    # If execute() doesn't work, the response might already contain data
                    try:
                        data = response.data
                    except AttributeError:
                        # Or the response itself might be the data
                        data = response

                # Filter by cutoff time if needed
                if cutoff_time and data:
                    data = [item for item in data if item.get(
                        'last_updated', 0) >= cutoff_time]

                return data
            except Exception as inner_e:
                print(f"Direct query method failed: {inner_e}")
                return []

        except Exception as e:
            print(f"Error getting analysis results from Supabase: {e}")
            return []

    def get_analysis_results_fallback(self):
        """Fallback method to retrieve analysis results when all else fails."""
        if not self.is_connected():
            return None

        try:
            # Most basic query possible - just get all results
            response = self.client.from_("analysis_results").select("*")

            # Try to get data
            try:
                if hasattr(response, 'execute'):
                    data = response.execute().data
                elif hasattr(response, 'data'):
                    data = response.data
                else:
                    data = response

                return data
            except Exception as e:
                print(f"Fallback retrieval error: {e}")
                return None
        except Exception as e:
            print(f"Error in analysis results fallback: {e}")
            return None

# Singleton instance
_supabase_db = None

def get_supabase_db():
    """Get the singleton instance of SupabaseDB."""
    global _supabase_db
    if _supabase_db is None:
        _supabase_db = SupabaseDB()
    return _supabase_db