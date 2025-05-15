import sqlite3
import json
import time
from datetime import datetime
import pandas as pd
import os
from config import DB_PATH, CACHE_EXPIRATION

def get_db_connection():
    """Create a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_database():
    """Initialize the database tables if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create watchlist table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS watchlist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT UNIQUE,
        name TEXT,
        exchange TEXT,
        sector TEXT,
        added_date TEXT
    )
    ''')
    
    # Create stock data cache table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stock_data_cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT,
        timeframe TEXT,
        period TEXT,
        data TEXT,
        timestamp INTEGER,
        source TEXT,
        UNIQUE(ticker, timeframe, period, source)
    )
    ''')
    
    # Create fundamentals cache table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS fundamentals_cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT UNIQUE,
        pe_ratio REAL,
        profit_margin REAL,
        revenue_growth REAL,
        earnings_growth REAL,
        book_value REAL,
        market_cap REAL,
        dividend_yield REAL,
        last_updated INTEGER
    )
    ''')
    
    conn.commit()
    conn.close()

def add_to_watchlist(ticker, name, exchange="", sector=""):
    """Add a ticker to the watchlist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        current_date = datetime.now().strftime("%Y-%m-%d")
        cursor.execute(
            "INSERT INTO watchlist (ticker, name, exchange, sector, added_date) VALUES (?, ?, ?, ?, ?)",
            (ticker, name, exchange, sector, current_date)
        )
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        # Ticker already exists in watchlist
        success = False
    finally:
        conn.close()
    
    return success

def remove_from_watchlist(ticker):
    """Remove a ticker from the watchlist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM watchlist WHERE ticker = ?", (ticker,))
    conn.commit()
    conn.close()

def get_watchlist():
    """Get all tickers in the watchlist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM watchlist ORDER BY added_date DESC")
    watchlist = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return watchlist

def cache_stock_data(ticker, timeframe, period, data, source):
    """Cache stock data to reduce API calls."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Convert DataFrame to JSON for storage
    json_data = data.to_json()
    current_timestamp = int(time.time())
    
    cursor.execute(
        """
        INSERT OR REPLACE INTO stock_data_cache 
        (ticker, timeframe, period, data, timestamp, source) 
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (ticker, timeframe, period, json_data, current_timestamp, source)
    )
    
    conn.commit()
    conn.close()

def get_cached_stock_data(ticker, timeframe, period, source):
    """Retrieve cached stock data if available and not expired."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    current_timestamp = int(time.time())
    cursor.execute(
        """
        SELECT data, timestamp FROM stock_data_cache 
        WHERE ticker = ? AND timeframe = ? AND period = ? AND source = ?
        """,
        (ticker, timeframe, period, source)
    )
    
    result = cursor.fetchone()
    conn.close()
    
    if result and (current_timestamp - result['timestamp']) < CACHE_EXPIRATION:
        # Cache not expired, convert JSON back to DataFrame
        return pd.read_json(result['data'])
    
    return None

def cache_fundamentals(ticker, fundamentals_data):
    """Cache fundamental data for a ticker."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    current_timestamp = int(time.time())
    
    cursor.execute(
        """
        INSERT OR REPLACE INTO fundamentals_cache 
        (ticker, pe_ratio, profit_margin, revenue_growth, earnings_growth, 
        book_value, market_cap, dividend_yield, last_updated) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ticker, 
            fundamentals_data.get('pe_ratio', None),
            fundamentals_data.get('profit_margin', None),
            fundamentals_data.get('revenue_growth', None),
            fundamentals_data.get('earnings_growth', None),
            fundamentals_data.get('book_value', None),
            fundamentals_data.get('market_cap', None),
            fundamentals_data.get('dividend_yield', None),
            current_timestamp
        )
    )
    
    conn.commit()
    conn.close()

def get_cached_fundamentals(ticker):
    """Retrieve cached fundamental data if available and not expired."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    current_timestamp = int(time.time())
    cursor.execute(
        "SELECT * FROM fundamentals_cache WHERE ticker = ?",
        (ticker,)
    )
    
    result = cursor.fetchone()
    conn.close()
    
    if result and (current_timestamp - result['last_updated']) < CACHE_EXPIRATION:
        # Return as dictionary
        return dict(result)
    
    return None

def get_all_cached_stocks():
    """Get all unique stock tickers in the cache."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT ticker FROM stock_data_cache")
    tickers = [row['ticker'] for row in cursor.fetchall()]
    
    conn.close()
    return tickers

def get_all_fundamentals():
    """Get fundamental data for all stocks in cache."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM fundamentals_cache")
    fundamentals = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return fundamentals
