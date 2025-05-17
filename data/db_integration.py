from data.db_manager import (
    get_db_session, add_to_watchlist as add_to_sqlite_watchlist,
    remove_from_watchlist as remove_from_sqlite_watchlist,
    get_watchlist as get_sqlite_watchlist,
    cache_stock_data as cache_stock_data_sqlite,
    get_cached_stock_data as get_cached_stock_data_sqlite,
    cache_fundamentals as cache_fundamentals_sqlite,
    get_cached_fundamentals as get_cached_fundamentals_sqlite,
    get_all_cached_stocks as get_all_cached_stocks_sqlite,
    get_all_fundamentals as get_all_fundamentals_sqlite,
    initialize_database
)
from data.supabase_client import get_supabase_db
import os

# Make sure SQLite database is initialized properly
initialize_database()

# Only use Supabase if the connection is properly set up and tables are accessible
supabase_db = get_supabase_db()
USE_SUPABASE = False  # Temporarily disable Supabase until tables are properly set up

def add_to_watchlist(ticker, name, exchange="", sector=""):
    """Add a ticker to the watchlist."""
    # Try Supabase first if connected
    if USE_SUPABASE:
        success = supabase_db.add_to_watchlist(ticker, name, exchange, sector)
        if success:
            return True
    
    # Fall back to SQLite
    return add_to_sqlite_watchlist(ticker, name, exchange, sector)

def remove_from_watchlist(ticker):
    """Remove a ticker from the watchlist."""
    # Try Supabase first if connected
    if USE_SUPABASE:
        supabase_db.remove_from_watchlist(ticker)
    
    # Also remove from SQLite for consistency
    remove_from_sqlite_watchlist(ticker)

def get_watchlist():
    """Get all tickers in the watchlist."""
    # Try Supabase first if connected
    if USE_SUPABASE:
        watchlist = supabase_db.get_watchlist()
        if watchlist:
            return watchlist
    
    # Fall back to SQLite
    return get_sqlite_watchlist()

def cache_stock_data(ticker, timeframe, period, data, source):
    """Cache stock data to reduce API calls."""
    # Try Supabase first if connected
    if USE_SUPABASE:
        supabase_db.cache_stock_data(ticker, timeframe, period, data, source)
    
    # Also cache in SQLite for local performance
    cache_stock_data_sqlite(ticker, timeframe, period, data, source)

def get_cached_stock_data(ticker, timeframe, period, source):
    """Retrieve cached stock data if available and not expired."""
    # Try Supabase first if connected
    if USE_SUPABASE:
        data = supabase_db.get_cached_stock_data(ticker, timeframe, period, source)
        if data is not None:
            return data
    
    # Fall back to SQLite
    return get_cached_stock_data_sqlite(ticker, timeframe, period, source)

def cache_fundamentals(ticker, fundamentals_data):
    """Cache fundamental data for a ticker."""
    # Try Supabase first if connected
    if USE_SUPABASE:
        supabase_db.cache_fundamentals(ticker, fundamentals_data)
    
    # Also cache in SQLite for local performance
    cache_fundamentals_sqlite(ticker, fundamentals_data)

def get_cached_fundamentals(ticker):
    """Retrieve cached fundamental data if available and not expired."""
    # Try Supabase first if connected
    if USE_SUPABASE:
        data = supabase_db.get_cached_fundamentals(ticker)
        if data is not None:
            return data
    
    # Fall back to SQLite
    return get_cached_fundamentals_sqlite(ticker)

def get_all_cached_stocks():
    """Get all unique stock tickers in the cache."""
    # Try Supabase first if connected
    if USE_SUPABASE:
        stocks = supabase_db.get_all_cached_stocks()
        if stocks:
            return stocks
    
    # Fall back to SQLite
    return get_all_cached_stocks_sqlite()

def get_all_fundamentals():
    """Get fundamental data for all stocks in cache."""
    # Try Supabase first if connected
    if USE_SUPABASE:
        fundamentals = supabase_db.get_all_fundamentals()
        if fundamentals:
            return fundamentals
    
    # Fall back to SQLite
    return get_all_fundamentals_sqlite()

def create_supabase_tables():
    """Initialize the Supabase tables."""
    if USE_SUPABASE:
        # This will check and inform about any missing tables
        supabase_db._create_tables_if_not_exist()