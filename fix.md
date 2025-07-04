# Watchlist Data Minimization Fix - Implementation Guide

## Overview
This fix updates the watchlist functionality to only store the ticker symbol and company name when adding stocks. No price data, performance metrics, or other values will be collected or stored. The watchlist will be a simple list that loads without any API calls.

## Current State Analysis
Currently, the watchlist system:
- Stores ticker, name, sector, current_price, and change_pct in `get_watchlist_details()`
- Makes API calls to fetch current prices when viewing watchlists
- Exports these additional fields when exporting to CSV

## Required Changes

### 1. Update `services/watchlist_manager.py`

#### Change 1: Modify `add_stock_to_watchlist()` method

**FIND this section (around line 140-165):**
```python
def add_stock_to_watchlist(self, watchlist_id: int, ticker: str) -> bool:
    """Add a stock to a watchlist"""
    try:
        # Check if stock already exists in this watchlist
        existing = self.db.query(WatchlistStock).filter_by(
            watchlist_id=watchlist_id,
            ticker=ticker
        ).first()

        if existing:
            return False

        # Add stock to watchlist
        watchlist_stock = WatchlistStock(
            watchlist_id=watchlist_id,
            ticker=ticker
        )

        self.db.add(watchlist_stock)
        self.db.commit()
        return True
```

**REPLACE with:**
```python
def add_stock_to_watchlist(self, watchlist_id: int, ticker: str, name: str = None) -> bool:
    """Add a stock to a watchlist with optional name"""
    try:
        # Check if stock already exists in this watchlist
        existing = self.db.query(WatchlistStock).filter_by(
            watchlist_id=watchlist_id,
            ticker=ticker
        ).first()

        if existing:
            return False

        # If name not provided, use ticker as name
        if not name:
            name = ticker

        # Add stock to watchlist with name
        watchlist_stock = WatchlistStock(
            watchlist_id=watchlist_id,
            ticker=ticker,
            name=name  # Store the company name
        )

        self.db.add(watchlist_stock)
        self.db.commit()
        return True
```

#### Change 2: Simplify `get_watchlist_details()` method

**FIND this section (around line 200-240):**
```python
def get_watchlist_details(self, watchlist_id: int) -> List[dict]:
    """Get detailed information for all stocks in a watchlist"""
    stocks = self.get_watchlist_stocks(watchlist_id)
    details = []

    for ticker in stocks:
        try:
            # Get basic company info
            info = yf.Ticker(ticker).info

            # Get current price and calculate change
            current_price = info.get('currentPrice', 0)
            if not current_price:
                current_price = info.get('regularMarketPrice', 0)

            previous_close = info.get('previousClose', 0)
            if current_price and previous_close:
                change_pct = ((current_price - previous_close) / previous_close) * 100
            else:
                change_pct = 0

            details.append({
                'ticker': ticker,
                'name': info.get('longName', ticker),
                'sector': info.get('sector', 'Unknown'),
                'current_price': current_price,
                'change_pct': change_pct
            })
```

**REPLACE with:**
```python
def get_watchlist_details(self, watchlist_id: int) -> List[dict]:
    """Get ticker and name for all stocks in a watchlist (no API calls)"""
    try:
        # Query the database directly for stored ticker and name
        stocks = self.db.query(WatchlistStock).filter_by(
            watchlist_id=watchlist_id
        ).all()

        details = []
        for stock in stocks:
            details.append({
                'ticker': stock.ticker,
                'name': getattr(stock, 'name', stock.ticker)  # Use stored name or ticker as fallback
            })

        return details
    except Exception as e:
        logger.error(f"Error getting watchlist details: {e}")
        return []
```

### 2. Update Database Model in `data/db_models.py`

**ADD a name column to the WatchlistStock model:**

**FIND this section:**
```python
class WatchlistStock(Base):
    __tablename__ = 'watchlist_stocks'

    id = Column(Integer, primary_key=True)
    watchlist_id = Column(Integer, ForeignKey('watchlists.id'))
    ticker = Column(String, nullable=False)
    added_date = Column(DateTime, default=datetime.utcnow)
```

**REPLACE with:**
```python
class WatchlistStock(Base):
    __tablename__ = 'watchlist_stocks'

    id = Column(Integer, primary_key=True)
    watchlist_id = Column(Integer, ForeignKey('watchlists.id'))
    ticker = Column(String, nullable=False)
    name = Column(String, nullable=True)  # Add company name field
    added_date = Column(DateTime, default=datetime.utcnow)
```

### 3. Update UI Components

#### Update `ui/batch_analysis.py` - Fix add_stock_to_watchlist calls

**FIND all occurrences of:**
```python
manager.add_stock_to_watchlist(watchlist_id, ticker)
```

**REPLACE with:**
```python
manager.add_stock_to_watchlist(watchlist_id, ticker, name)
```

**Specifically update these functions:**
- `add_single_to_watchlist()` 
- `add_stock_to_watchlist_with_feedback()`
- `add_selected_to_watchlist()`

#### Update `ui/enhanced_scanner.py` - Fix add function

**FIND:**
```python
def add_stock_to_watchlist(ticker, name):
    """Add stock to default watchlist"""
    # ... existing code ...
    if default_wl:
        success = manager.add_stock_to_watchlist(default_wl['id'], ticker)
```

**REPLACE with:**
```python
def add_stock_to_watchlist(ticker, name):
    """Add stock to default watchlist"""
    # ... existing code ...
    if default_wl:
        success = manager.add_stock_to_watchlist(default_wl['id'], ticker, name)
```

### 4. Update Watchlist Display in `ui/watchlist.py`

**FIND the section that displays watchlist stocks (around line 150-200):**
```python
# Display stock details
if stock_details:
    # Create DataFrame for display
    df = pd.DataFrame(stock_details)

    # Format the display
    display_df = df[['ticker', 'name', 'sector', 'current_price', 'change_pct']].copy()
    display_df.columns = ['Ticker', 'Name', 'Sector', 'Price', 'Change %']
```

**REPLACE with:**
```python
# Display stock details
if stock_details:
    # Create DataFrame for display (only ticker and name)
    df = pd.DataFrame(stock_details)

    # Simple display with just ticker and name
    display_df = df[['ticker', 'name']].copy()
    display_df.columns = ['Ticker', 'Company Name']
```

### 5. Update Export Functionality

The export will automatically only include ticker and name since that's all that's stored now. No changes needed to the export code.

### 6. Update Import Functionality

**The import already works correctly** - it only imports tickers. However, we should update it to try to fetch company names during import.

**FIND in `services/watchlist_manager.py` - `import_watchlist_from_csv()` method:**
```python
if self.add_stock_to_watchlist(watchlist_id, ticker):
    successful += 1
```

**REPLACE with:**
```python
# Try to get company name during import (optional enhancement)
name = ticker  # Default to ticker if name lookup fails
try:
    # Optional: Quick lookup for name without full data fetch
    from data.stock_data import get_company_name
    fetched_name = get_company_name(ticker)
    if fetched_name:
        name = fetched_name
except:
    pass

if self.add_stock_to_watchlist(watchlist_id, ticker, name):
    successful += 1
```

## Database Migration

After making these code changes, you'll need to handle the database schema update:

1. **For new installations**: The database will be created with the new schema automatically.

2. **For existing installations**: Add this migration script to handle existing databases:

Create a new file `migrations/add_name_to_watchlist.py`:

```python
"""Add name column to watchlist_stocks table"""
from sqlalchemy import text
from data.db_connection import get_db_connection

def migrate():
    """Add name column to existing watchlist_stocks table"""
    db = get_db_connection()
    try:
        # Check if column already exists
        result = db.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='watchlist_stocks' AND column_name='name'"
        )).fetchone()

        if not result:
            # Add the column
            db.execute(text(
                "ALTER TABLE watchlist_stocks ADD COLUMN name VARCHAR"
            ))
            db.commit()
            print("Successfully added name column to watchlist_stocks")
        else:
            print("Name column already exists")

    except Exception as e:
        print(f"Migration error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
```

## Testing the Changes

1. **Test adding stocks to watchlist**:
   - Add a stock from batch analysis
   - Verify only ticker and name are stored
   - Check that no API calls are made when viewing watchlist

2. **Test import/export**:
   - Export a watchlist to CSV
   - Verify only ticker and name columns are present
   - Import the CSV to a new watchlist
   - Verify import works correctly

3. **Test performance**:
   - Load a watchlist with 50+ stocks
   - Verify it loads instantly without API calls
   - Check that the display shows only ticker and name

## Benefits of This Change

1. **Performance**: Watchlists load instantly without any API calls
2. **Reliability**: No dependency on external APIs for viewing watchlists
3. **Simplicity**: Cleaner data model focused on essential information
4. **Privacy**: Less data stored means less to manage/protect
5. **Export/Import**: Simpler CSV files that are easier to manage

## Rollback Plan

If you need to rollback:
1. Restore the original code from your version control
2. The database will still work (extra 'name' column will be ignored)
3. Existing watchlists remain functional