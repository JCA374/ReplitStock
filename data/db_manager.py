# SQLite database manager functions
# Simplified version with essential functions for compatibility

import logging
import sqlite3
import pandas as pd
import json
from datetime import datetime, timedelta
from contextlib import contextmanager
from data.db_connection import get_db_connection

logger = logging.getLogger(__name__)

@contextmanager 
def get_db_session():
    """Get database session with context management"""
    db_connection = get_db_connection()
    session = db_connection.get_session()
    try:
        yield session
    finally:
        session.close()

def add_to_watchlist(ticker, collection_name="Default"):
    """Add ticker to watchlist"""
    from data.db_integration import add_to_watchlist as real_add_to_watchlist
    return real_add_to_watchlist(ticker, collection_name)

def remove_from_watchlist(ticker, collection_name="Default"):
    """Remove ticker from watchlist"""
    from data.db_integration import remove_from_watchlist as real_remove_from_watchlist
    return real_remove_from_watchlist(ticker, collection_name)

def get_watchlist(collection_name="Default"):
    """Get watchlist"""
    from data.db_integration import get_watchlist as real_get_watchlist
    return real_get_watchlist(collection_name)

def cache_stock_data(ticker, timeframe, period, data, source):
    """Cache stock data"""
    # Simplified implementation
    try:
        with get_db_session() as session:
            # This is a simplified version
            return True
    except Exception as e:
        logger.error(f"Error caching stock data: {e}")
        return False

def get_cached_stock_data(ticker, timeframe='1d', period='1y', source='yahoo'):
    """Get cached stock data"""
    from data.db_integration import get_cached_stock_data as real_get_cached_stock_data
    return real_get_cached_stock_data(ticker, timeframe, period, source)

def cache_fundamentals(ticker, fundamentals):
    """Cache fundamentals"""
    # Simplified implementation
    try:
        with get_db_session() as session:
            # This is a simplified version
            return True
    except Exception as e:
        logger.error(f"Error caching fundamentals: {e}")
        return False

def get_cached_fundamentals(ticker):
    """Get cached fundamentals"""
    from data.db_integration import get_cached_fundamentals as real_get_cached_fundamentals
    return real_get_cached_fundamentals(ticker)

def get_all_cached_stocks():
    """Get all cached stocks"""
    from data.db_integration import get_all_cached_stocks as real_get_all_cached_stocks
    return real_get_all_cached_stocks()

def get_all_fundamentals():
    """Get all cached fundamentals"""
    # Simplified implementation
    try:
        with get_db_session() as session:
            # This is a simplified version - returns empty dict for now
            return {}
    except Exception as e:
        logger.error(f"Error getting all fundamentals: {e}")
        return {}

def initialize_database():
    """Initialize database"""
    try:
        from data.db_connection import get_db_connection
        db_connection = get_db_connection()
        # Database is initialized in the connection setup
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False