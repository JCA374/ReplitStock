import sqlite3
import json
import time
from datetime import datetime, timedelta
import pandas as pd
import os
import io
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, BigInteger, UniqueConstraint, MetaData, Table, select, insert, delete, update, and_, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text

from config import DB_PATH, CACHE_EXPIRATION, DATA_REFRESH_INTERVAL

# Create SQLAlchemy Base
Base = declarative_base()

# Define ORM models
class Watchlist(Base):
    __tablename__ = 'watchlist'
    
    id = Column(Integer, primary_key=True)
    ticker = Column(String(20), unique=True)
    name = Column(String(100))
    exchange = Column(String(50))
    sector = Column(String(50))
    added_date = Column(String(20))

class StockDataCache(Base):
    __tablename__ = 'stock_data_cache'
    
    id = Column(Integer, primary_key=True)
    ticker = Column(String(20))
    timeframe = Column(String(10))
    period = Column(String(10))
    data = Column(Text)
    timestamp = Column(BigInteger)
    source = Column(String(20))
    
    __table_args__ = (
        UniqueConstraint('ticker', 'timeframe', 'period', 'source', name='stock_data_cache_unique'),
    )

class FundamentalsCache(Base):
    __tablename__ = 'fundamentals_cache'
    
    id = Column(Integer, primary_key=True)
    ticker = Column(String(20), unique=True)
    pe_ratio = Column(Float)
    profit_margin = Column(Float)
    revenue_growth = Column(Float)
    earnings_growth = Column(Float)
    book_value = Column(Float)
    market_cap = Column(Float)
    dividend_yield = Column(Float)
    last_updated = Column(BigInteger)

# Database connection
engine = None
Session = None

def get_db_engine():
    """Get a database engine - SQLAlchemy connection."""
    global engine
    
    if engine is not None:
        return engine
    
    # Due to Replit's network limitations with external PostgreSQL connections,
    # we'll use SQLite for local storage which works reliably
    print("Using SQLite database for local storage")
    engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"timeout": 30})
    
    return engine

def get_db_session():
    """Get a database session."""
    global Session
    
    if Session is None:
        engine = get_db_engine()
        Session = sessionmaker(bind=engine)
    
    return Session()

def get_db_connection():
    """Create a connection to the SQLite database (for backward compatibility)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_database_exists():
    """
    Ensure the local SQLite database exists and is properly initialized.
    This is safe to call multiple times.
    """
    try:
        # Check if database file exists
        if not os.path.exists(DB_PATH):
            print(f"Database file {DB_PATH} does not exist. Creating...")

        # Initialize database connection and tables
        engine = get_db_engine()

        # Import all models to ensure they're registered
        from data.db_models import Base, Watchlist, StockDataCache, FundamentalsCache, AnalysisResults

        # Create all tables
        Base.metadata.create_all(engine)

        print(f"Database {DB_PATH} initialized successfully")
        return True

    except Exception as e:
        print(f"Error ensuring database exists: {e}")
        return False

def initialize_database():
    """Initialize the database tables if they don't exist."""
    print("Starting database initialization...")
    try:
        # Ensure local SQLite database exists first
        if not ensure_database_exists():
            print("Failed to ensure local database exists")
            return False

        # Always use SQLite for now due to connection issues with PostgreSQL on Replit
        print("Initializing SQLite database...")

        # Create tables using SQLAlchemy
        engine = get_db_engine()

        # Import all models to ensure they're registered with the Base
        from data.db_models import Watchlist, StockDataCache, FundamentalsCache, AnalysisResults

        Base.metadata.create_all(engine)
        print("SQLite database initialized successfully!")

        # Try connecting to Supabase if credentials are available
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        if supabase_url and supabase_key:
            try:
                print("Testing Supabase connection...")
                from data.supabase_client import get_supabase_db
                supabase_db = get_supabase_db()
                if supabase_db.is_connected():
                    print("Supabase connection successful!")
                else:
                    print("Supabase connection failed, but continuing with SQLite")
            except Exception as e:
                print(
                    f"Supabase connection error (continuing with SQLite): {e}")
        else:
            print("No Supabase credentials found, using SQLite only")

        return True
    except Exception as e:
        print(f"Database initialization error: {e}")
        import traceback
        print(traceback.format_exc())
        # Return True anyway to allow the app to continue
        return True

def add_to_watchlist(ticker, name, exchange="", sector=""):
    """Add a ticker to the watchlist."""
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    supabase_url = os.getenv("SUPABASE_URL")
    if supabase_url:
        # Use SQLAlchemy for PostgreSQL
        session = get_db_session()
        try:
            # Check if ticker already exists
            existing = session.query(Watchlist).filter(Watchlist.ticker == ticker).first()
            if existing:
                session.close()
                return False
            
            # Create new watchlist entry
            new_item = Watchlist(
                ticker=ticker,
                name=name,
                exchange=exchange,
                sector=sector,
                added_date=current_date
            )
            session.add(new_item)
            session.commit()
            success = True
        except Exception:
            session.rollback()
            success = False
        finally:
            session.close()
    else:
        # Fallback to SQLite
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
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
    supabase_url = os.getenv("SUPABASE_URL")
    if supabase_url:
        # Use SQLAlchemy for PostgreSQL
        session = get_db_session()
        try:
            item = session.query(Watchlist).filter(Watchlist.ticker == ticker).first()
            if item:
                session.delete(item)
                session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()
    else:
        # Fallback to SQLite
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM watchlist WHERE ticker = ?", (ticker,))
        conn.commit()
        conn.close()

def get_watchlist():
    """Get all tickers in the watchlist."""
    supabase_url = os.getenv("SUPABASE_URL")
    if supabase_url:
        # Use SQLAlchemy for PostgreSQL
        session = get_db_session()
        try:
            items = session.query(Watchlist).order_by(Watchlist.added_date.desc()).all()
            watchlist = [
                {
                    'id': item.id,
                    'ticker': item.ticker,
                    'name': item.name,
                    'exchange': item.exchange,
                    'sector': item.sector,
                    'added_date': item.added_date
                }
                for item in items
            ]
        finally:
            session.close()
    else:
        # Fallback to SQLite
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM watchlist ORDER BY added_date DESC")
        watchlist = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
    
    return watchlist

def is_market_open():
    """Check if the market is likely open (simplistic approach)."""
    now = datetime.now()
    
    # Market is typically closed on weekends
    if now.weekday() > 4:  # 5 = Saturday, 6 = Sunday
        return False
    
    # Consider market hours roughly 9:30 AM to 4:00 PM EST
    # This is simplistic - doesn't account for holidays or pre/post market
    if 9 <= now.hour < 16:
        return True
    
    return False

def should_refresh_data(timestamp):
    """Determine if data should be refreshed based on timestamp and market hours."""
    if timestamp is None:
        return True
    
    current_time = int(time.time())
    age = current_time - timestamp
    
    # Always refresh if older than the configured interval
    if age > DATA_REFRESH_INTERVAL:
        # Additional check: if market is closed and data is less than 24h old (86400 seconds),
        # we might not need to refresh as frequently
        if not is_market_open() and age < 86400:
            return False
        return True
    
    return False

def cache_stock_data(ticker, timeframe, period, data, source):
    """Cache stock data to reduce API calls."""
    # Convert DataFrame to JSON for storage
    json_data = data.to_json()
    current_timestamp = int(time.time())
    
    supabase_url = os.getenv("SUPABASE_URL")
    if supabase_url:
        # Use SQLAlchemy for PostgreSQL
        session = get_db_session()
        try:
            # Look for existing record
            existing = session.query(StockDataCache).filter(
                StockDataCache.ticker == ticker,
                StockDataCache.timeframe == timeframe,
                StockDataCache.period == period,
                StockDataCache.source == source
            ).first()
            
            if existing:
                # Update existing record
                existing.data = json_data
                existing.timestamp = current_timestamp
            else:
                # Create new record
                new_record = StockDataCache(
                    ticker=ticker,
                    timeframe=timeframe,
                    period=period,
                    data=json_data,
                    timestamp=current_timestamp,
                    source=source
                )
                session.add(new_record)
            
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error caching data: {e}")
        finally:
            session.close()
    else:
        # Fallback to SQLite
        conn = get_db_connection()
        cursor = conn.cursor()
        
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
    timestamp = None
    data = None
    
    supabase_url = os.getenv("SUPABASE_URL")
    if supabase_url:
        # Use SQLAlchemy for PostgreSQL
        session = get_db_session()
        try:
            record = session.query(StockDataCache).filter(
                StockDataCache.ticker == ticker,
                StockDataCache.timeframe == timeframe,
                StockDataCache.period == period,
                StockDataCache.source == source
            ).first()
            
            if record:
                timestamp = record.timestamp
                data = record.data
        finally:
            session.close()
    else:
        # Fallback to SQLite
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT data, timestamp FROM stock_data_cache 
            WHERE ticker = ? AND timeframe = ? AND period = ? AND source = ?
            """,
            (ticker, timeframe, period, source)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            timestamp = result['timestamp']
            data = result['data']
    
    # Check if we need to refresh the data
    if data and not should_refresh_data(timestamp):
        # Convert JSON back to DataFrame
        return pd.read_json(io.StringIO(data))
    
    return None

def cache_fundamentals(ticker, fundamentals_data):
    """Cache fundamental data for a ticker."""
    current_timestamp = int(time.time())
    
    supabase_url = os.getenv("SUPABASE_URL")
    if supabase_url:
        # Use SQLAlchemy for PostgreSQL
        session = get_db_session()
        try:
            # Look for existing record
            existing = session.query(FundamentalsCache).filter(
                FundamentalsCache.ticker == ticker
            ).first()
            
            if existing:
                # Update existing record
                existing.pe_ratio = fundamentals_data.get('pe_ratio', None)
                existing.profit_margin = fundamentals_data.get('profit_margin', None)
                existing.revenue_growth = fundamentals_data.get('revenue_growth', None)
                existing.earnings_growth = fundamentals_data.get('earnings_growth', None)
                existing.book_value = fundamentals_data.get('book_value', None)
                existing.market_cap = fundamentals_data.get('market_cap', None)
                existing.dividend_yield = fundamentals_data.get('dividend_yield', None)
                existing.last_updated = current_timestamp
            else:
                # Create new record
                new_record = FundamentalsCache(
                    ticker=ticker,
                    pe_ratio=fundamentals_data.get('pe_ratio', None),
                    profit_margin=fundamentals_data.get('profit_margin', None),
                    revenue_growth=fundamentals_data.get('revenue_growth', None),
                    earnings_growth=fundamentals_data.get('earnings_growth', None),
                    book_value=fundamentals_data.get('book_value', None),
                    market_cap=fundamentals_data.get('market_cap', None),
                    dividend_yield=fundamentals_data.get('dividend_yield', None),
                    last_updated=current_timestamp
                )
                session.add(new_record)
            
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error caching fundamentals: {e}")
        finally:
            session.close()
    else:
        # Fallback to SQLite
        conn = get_db_connection()
        cursor = conn.cursor()
        
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
    current_timestamp = int(time.time())
    
    supabase_url = os.getenv("SUPABASE_URL")
    if supabase_url:
        # Use SQLAlchemy for PostgreSQL
        session = get_db_session()
        try:
            record = session.query(FundamentalsCache).filter(
                FundamentalsCache.ticker == ticker
            ).first()
            
            if record and (current_timestamp - record.last_updated) < CACHE_EXPIRATION:
                # Return as dictionary
                return {
                    'id': record.id,
                    'ticker': record.ticker,
                    'pe_ratio': record.pe_ratio,
                    'profit_margin': record.profit_margin,
                    'revenue_growth': record.revenue_growth,
                    'earnings_growth': record.earnings_growth,
                    'book_value': record.book_value,
                    'market_cap': record.market_cap,
                    'dividend_yield': record.dividend_yield,
                    'last_updated': record.last_updated
                }
        finally:
            session.close()
    else:
        # Fallback to SQLite
        conn = get_db_connection()
        cursor = conn.cursor()
        
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
    supabase_url = os.getenv("SUPABASE_URL")
    if supabase_url:
        # Use SQLAlchemy for PostgreSQL
        session = get_db_session()
        try:
            tickers = session.query(StockDataCache.ticker).distinct().all()
            return [t[0] for t in tickers]
        finally:
            session.close()
    else:
        # Fallback to SQLite
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT ticker FROM stock_data_cache")
        tickers = [row['ticker'] for row in cursor.fetchall()]
        
        conn.close()
        return tickers

def get_all_fundamentals():
    """Get fundamental data for all stocks in cache."""
    supabase_url = os.getenv("SUPABASE_URL")
    if supabase_url:
        # Use SQLAlchemy for PostgreSQL
        session = get_db_session()
        try:
            records = session.query(FundamentalsCache).all()
            return [
                {
                    'id': record.id,
                    'ticker': record.ticker,
                    'pe_ratio': record.pe_ratio,
                    'profit_margin': record.profit_margin,
                    'revenue_growth': record.revenue_growth,
                    'earnings_growth': record.earnings_growth,
                    'book_value': record.book_value,
                    'market_cap': record.market_cap,
                    'dividend_yield': record.dividend_yield,
                    'last_updated': record.last_updated
                }
                for record in records
            ]
        finally:
            session.close()
    else:
        # Fallback to SQLite
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM fundamentals_cache")
        fundamentals = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return fundamentals
