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
        self.supabase_url = os.getenv("DATABASE_URL", "")
        self.supabase_key = os.getenv("DATABASE_PASSWORD", "")
        
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
        return self.client is not None
    
    def _create_tables_if_not_exist(self):
        """
        Check if necessary tables exist.
        """
        if not self.is_connected():
            return
        
        # Verify tables exist by trying to fetch a row
        tables = ["watchlist", "stock_data_cache", "fundamentals_cache"]
        working_tables = 0
        
        for table in tables:
            try:
                # Try fetching a single row
                response = self.client.table(table).select("*").limit(1).execute()
                print(f"Table {table} exists and is accessible")
                working_tables += 1
            except Exception as e:
                print(f"Table {table} might not exist: {str(e)}")
        
        if working_tables == len(tables):
            print("All tables are accessible! Database is ready.")
        else:
            print(f"{working_tables}/{len(tables)} tables are accessible. Some features may not work correctly.")
    
    # Watchlist methods
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
            response = self.client.table("stock_data_cache").select("*").eq("ticker", ticker).eq("timeframe", timeframe).eq("period", period).eq("source", source).execute()
            
            if response.data:
                record = response.data[0]
                current_timestamp = int(time.time())
                
                # Check if data needs to be refreshed
                if (current_timestamp - record["timestamp"]) < CACHE_EXPIRATION:
                    # Convert JSON back to DataFrame
                    return pd.read_json(record["data"])
            
            return None
        except Exception as e:
            print(f"Error getting cached stock data: {str(e)}")
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

# Singleton instance
_supabase_db = None

def get_supabase_db():
    """Get the singleton instance of SupabaseDB."""
    global _supabase_db
    if _supabase_db is None:
        _supabase_db = SupabaseDB()
    return _supabase_db