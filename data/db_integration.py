from datetime import datetime
import time
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

# Use Supabase if it's properly connected
supabase_db = get_supabase_db()
USE_SUPABASE = supabase_db.is_connected()  # Enable Supabase if connected

def add_to_watchlist(ticker, name, exchange="", sector=""):
    """Add a ticker to the watchlist."""
    # Try Supabase first if connected
    if USE_SUPABASE:
        success = supabase_db.add_to_watchlist(ticker, name, exchange, sector)
        if success:
            return True
    
    # Fall back to SQLite
    return add_to_sqlite_watchlist(ticker, name, exchange, sector)

def store_analysis_result(ticker, analysis_data):
    """Store analysis result in the database."""
    current_timestamp = int(time.time())

    # Format the analysis data for storage
    analysis_record = {
        'ticker': ticker,
        'analysis_date': analysis_data.get('date', datetime.now().strftime("%Y-%m-%d")),
        'price': analysis_data.get('price'),
        'tech_score': analysis_data.get('tech_score'),
        'signal': 'BUY' if analysis_data.get('buy_signal') else 'SELL' if analysis_data.get('sell_signal') else 'HOLD',
        'above_ma40': analysis_data.get('above_ma40'),
        'above_ma4': analysis_data.get('above_ma4'),
        'rsi_value': analysis_data.get('rsi'),
        'rsi_above_50': analysis_data.get('rsi_above_50'),
        'near_52w_high': analysis_data.get('near_52w_high'),
        'pe_ratio': analysis_data.get('pe_ratio'),
        'profit_margin': analysis_data.get('profit_margin'),
        'revenue_growth': analysis_data.get('revenue_growth'),
        'is_profitable': analysis_data.get('is_profitable'),
        'data_source': analysis_data.get('data_source', 'unknown'),
        'last_updated': current_timestamp
    }

    # Try Supabase first if connected
    if USE_SUPABASE:
        success = supabase_db.store_analysis_result(ticker, analysis_record)
        if success:
            return True

    # Fall back to SQLite
    from data.db_models import AnalysisResults
    session = get_db_session()
    try:
        # Check if record exists
        existing = session.query(AnalysisResults).filter(
            AnalysisResults.ticker == ticker,
            AnalysisResults.analysis_date == analysis_record['analysis_date']
        ).first()

        if existing:
            # Update existing record
            for key, value in analysis_record.items():
                setattr(existing, key, value)
        else:
            # Create new record
            new_record = AnalysisResults(**analysis_record)
            session.add(new_record)

        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error storing analysis result: {e}")
        return False
    finally:
        session.close()

def get_analysis_results(ticker=None, days=30):
    """Get stored analysis results, optionally filtered by ticker and date range."""
    current_time = int(time.time())
    cutoff_time = current_time - (days * 86400)  # Convert days to seconds

    # Try Supabase first if connected
    if USE_SUPABASE:
        results = supabase_db.get_analysis_results(ticker, cutoff_time)
        if results:
            return results

    # Fall back to SQLite
    from data.db_models import AnalysisResults
    session = get_db_session()
    try:
        query = session.query(AnalysisResults).filter(
            AnalysisResults.last_updated >= cutoff_time
        )

        if ticker:
            query = query.filter(AnalysisResults.ticker == ticker)

        query = query.order_by(AnalysisResults.last_updated.desc())

        results = query.all()
        return [
            {
                'ticker': r.ticker,
                'analysis_date': r.analysis_date,
                'price': r.price,
                'tech_score': r.tech_score,
                'signal': r.signal,
                'above_ma40': r.above_ma40,
                'above_ma4': r.above_ma4,
                'rsi_value': r.rsi_value,
                'rsi_above_50': r.rsi_above_50,
                'near_52w_high': r.near_52w_high,
                'pe_ratio': r.pe_ratio,
                'profit_margin': r.profit_margin,
                'revenue_growth': r.revenue_growth,
                'is_profitable': r.is_profitable,
                'data_source': r.data_source,
                'last_updated': r.last_updated
            }
            for r in results
        ]
    except Exception as e:
        print(f"Error getting analysis results: {e}")
        return []
    finally:
        session.close()

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