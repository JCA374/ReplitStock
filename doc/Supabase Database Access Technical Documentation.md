# Supabase Database Access Technical Documentation

## Overview

This document explains how to access the Supabase PostgreSQL database from the Stock Analysis application. The implementation uses a Session Pooler connection method for IPv4 compatibility and provides a seamless fallback to SQLite when cloud database access is unavailable.

## Connection Architecture

### Connection Flow

1. The application attempts to connect to Supabase PostgreSQL database
2. If successful, all data operations use the cloud database
3. If connection fails, the application automatically falls back to a local SQLite database
4. The connection type is exposed via `get_connection_type()` for UI status indicators

### Key Components

- **`db_connection.py`**: Central module managing database connections
- **`DatabaseConnection`** class: Handles connection initialization and management
- **Session Pooler**: IPv4-compatible connection method for Supabase
- **Credential Management**: Securely loads from `secrets.toml` or environment variables

## How to Access the Database

### Basic Usage

```python
from data.db_connection import get_db_session, get_db_engine, get_connection_type

# Check connection type (postgresql or sqlite)
connection_type = get_connection_type()
print(f"Using {connection_type} database")

# Get a session for ORM operations
session = get_db_session()
try:
    # Example: Query all items from watchlist table
    watchlist_items = session.query(Watchlist).all()
    
    # Process results
    for item in watchlist_items:
        print(f"Ticker: {item.ticker}, Name: {item.name}")
finally:
    session.close()

# Use the engine directly for raw SQL
engine = get_db_engine()
with engine.connect() as conn:
    # Example: Run a raw SQL query
    result = conn.execute(text("SELECT * FROM watchlist LIMIT 10"))
    for row in result:
        print(row)
```

### Using SQLAlchemy ORM

```python
from data.db_connection import get_db_session
from data.db_models import Watchlist

# Add a new item to watchlist
def add_to_watchlist(ticker, name, exchange, sector):
    session = get_db_session()
    try:
        # Check if ticker already exists
        existing = session.query(Watchlist).filter(Watchlist.ticker == ticker).first()
        if existing:
            return False
        
        # Create new watchlist entry with current date
        from datetime import datetime
        new_item = Watchlist(
            ticker=ticker,
            name=name,
            exchange=exchange,
            sector=sector,
            added_date=datetime.now().strftime("%Y-%m-%d")
        )
        session.add(new_item)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error adding to watchlist: {e}")
        return False
    finally:
        session.close()
```

### Executing Raw SQL

```python
from data.db_connection import get_db_connection
from sqlalchemy import text
import pandas as pd

# Execute a custom query and return results as DataFrame
def run_custom_query(sql_query, params=None):
    db = get_db_connection()
    return db.execute_query(sql_query, params)

# Example usage
def get_stocks_by_sector(sector):
    query = "SELECT ticker, name, exchange FROM watchlist WHERE sector = :sector"
    params = {"sector": sector}
    return run_custom_query(query, params)

# Call the function
tech_stocks = get_stocks_by_sector("Technology")
print(tech_stocks)  # DataFrame with results
```

## Database Tables

### Main Tables

1. **watchlist**
   - Primary table for storing user's watchlist items
   - Fields: id, ticker, name, exchange, sector, added_date

2. **stock_data_cache**
   - Caches historical stock price data to reduce API calls
   - Fields: id, ticker, timeframe, period, data (JSON), timestamp, source

3. **fundamentals_cache**
   - Stores fundamental financial data for companies
   - Fields: id, ticker, pe_ratio, profit_margin, revenue_growth, earnings_growth, book_value, market_cap, dividend_yield, last_updated

## Configuration

### secrets.toml

The application requires the following configuration in `.streamlit/secrets.toml`:

```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-supabase-anon-key"
DATABASE_PASSWORD = "your-database-password"
ALPHA_VANTAGE_API_KEY = "your-alpha-vantage-key"
```

### Connection String Format

The application uses a Session Pooler connection for IPv4 compatibility:

```
postgresql://postgres.{project_ref}:{password}@aws-0-eu-north-1.pooler.supabase.com:5432/postgres
```

## Troubleshooting

### Common Issues

1. **Connection Failures**
   - Check if `secrets.toml` is in the correct location
   - Verify credentials are correct
   - Ensure network allows outbound connections to port 5432

2. **IPv6/IPv4 Compatibility**
   - The application uses Session Pooler to ensure IPv4 compatibility
   - If connection issues persist, check network configuration

3. **SQLite Fallback**
   - If you see "Using sqlite database" in logs, Supabase connection failed
   - Data will be stored locally, not in the cloud

### Testing Connection

Run the test script to verify database access:

```bash
python db_connection.py
```

Successful output will show:
```
✅ Connected to postgresql database!
Current database timestamp: 2025-05-18 14:50:19.201415+00:00
```

## Performance Considerations

- Use the Session Pooler for persistent connections
- Keep transactions short to avoid blocking
- Cache frequently accessed data when appropriate
- The application automatically handles connection pooling

## Security Notes

- Never commit `secrets.toml` to version control
- The application sanitizes SQL inputs to prevent injection
- Use the `supabase` module for row-level security if needed
- Consider enabling SSL mode for additional security