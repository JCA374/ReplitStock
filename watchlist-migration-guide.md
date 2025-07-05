# Watchlist to Supabase Migration Guide

## Current State Analysis

Currently, the watchlist functionality uses **SQLite** as the primary storage with the following structure:
- `WatchlistCollection` table: Stores different watchlist categories (e.g., "My Watchlist", "Tech Stocks")
- `WatchlistMembership` table: Stores which stocks belong to which watchlist
- `SimpleWatchlistManager` service: Manages all watchlist operations

The Supabase integration is **already built** but currently **disabled** for watchlist operations (`USE_SUPABASE = False` in `data/db_integration.py`).

## Migration Steps

### Step 1: Create Supabase Tables

First, create the required tables in your Supabase database:

```sql
-- Create watchlist_collections table
CREATE TABLE IF NOT EXISTS public.watchlist_collections (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description VARCHAR(200),
    created_date VARCHAR(20),
    is_default BOOLEAN DEFAULT FALSE
);

-- Create watchlist_memberships table
CREATE TABLE IF NOT EXISTS public.watchlist_memberships (
    id SERIAL PRIMARY KEY,
    collection_id INTEGER NOT NULL,
    ticker VARCHAR(20) NOT NULL,
    added_date VARCHAR(20),
    UNIQUE(collection_id, ticker)
);

-- Create indexes for better performance
CREATE INDEX idx_membership_collection ON watchlist_memberships(collection_id);
CREATE INDEX idx_membership_ticker ON watchlist_memberships(ticker);
```

### Step 2: Update Supabase Client

**File to modify:** `data/supabase_client.py`

Add these methods to the `SupabaseDB` class:

```python
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
```

### Step 3: Update SimpleWatchlistManager

**File to modify:** `services/watchlist_manager.py`

Update the `SimpleWatchlistManager` class to use Supabase when available:

```python
def __init__(self):
    self.data_fetcher = StockDataFetcher()
    
    # Try to get Supabase connection
    from data.supabase_client import get_supabase_db
    self.supabase_db = get_supabase_db()
    self.use_supabase = self.supabase_db.is_connected()
    
    if self.use_supabase:
        logger.info("Using Supabase for watchlist storage")
    else:
        logger.info("Using SQLite for watchlist storage")
    
    self._ensure_default_watchlist()

def get_all_watchlists(self) -> List[Dict]:
    """Get all watchlist collections from the appropriate database."""
    # Try Supabase first
    if self.use_supabase:
        collections = self.supabase_db.get_all_watchlist_collections()
        if collections:
            return collections
    
    # Fall back to SQLite
    session = get_db_session()
    try:
        collections = session.query(WatchlistCollection).all()
        return [
            {
                'id': c.id,
                'name': c.name,
                'description': c.description,
                'created_date': c.created_date,
                'is_default': c.is_default
            }
            for c in collections
        ]
    finally:
        session.close()

def create_watchlist(self, name: str, description: str = "") -> bool:
    """Create a new watchlist collection in the appropriate database."""
    # Try Supabase first
    if self.use_supabase:
        result = self.supabase_db.create_watchlist_collection(name, description)
        if result:
            return True
    
    # Fall back to SQLite
    session = get_db_session()
    try:
        # ... existing SQLite code ...
```

### Step 4: Enable Supabase for Watchlists

**File to modify:** `data/db_integration.py`

Change the configuration to enable Supabase:

```python
# Line 30 - Change from:
USE_SUPABASE = False  # Disabled Supabase for watchlist operations

# To:
USE_SUPABASE = supabase_db.is_connected()  # Use Supabase if connected
```

### Step 5: Data Migration Script (Optional)

If you have existing watchlist data in SQLite that you want to migrate to Supabase:

**Create a new file:** `scripts/migrate_watchlists.py`

```python
import sys
sys.path.append('.')

from data.db_manager import get_db_session
from data.db_models import WatchlistCollection, WatchlistMembership
from data.supabase_client import get_supabase_db

def migrate_watchlists_to_supabase():
    """Migrate all watchlist data from SQLite to Supabase."""
    session = get_db_session()
    supabase = get_supabase_db()
    
    if not supabase.is_connected():
        print("Cannot connect to Supabase. Migration aborted.")
        return
    
    try:
        # Migrate collections
        collections = session.query(WatchlistCollection).all()
        collection_mapping = {}  # old_id -> new_id
        
        for col in collections:
            print(f"Migrating collection: {col.name}")
            new_col = supabase.create_watchlist_collection(
                col.name, 
                col.description or "", 
                col.is_default
            )
            if new_col:
                collection_mapping[col.id] = new_col['id']
        
        # Migrate memberships
        memberships = session.query(WatchlistMembership).all()
        for mem in memberships:
            if mem.collection_id in collection_mapping:
                new_collection_id = collection_mapping[mem.collection_id]
                supabase.add_to_watchlist_collection(new_collection_id, mem.ticker)
                print(f"Added {mem.ticker} to collection {new_collection_id}")
        
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Migration error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    migrate_watchlists_to_supabase()
```

## Testing the Migration

1. **Verify Supabase Connection:**
   ```python
   python -c "from data.supabase_client import get_supabase_db; print(get_supabase_db().is_connected())"
   ```

2. **Check Database Status in UI:**
   - Look at the header in your Streamlit app
   - Should show "✅ Connected to Supabase"

3. **Test Watchlist Operations:**
   - Create a new watchlist
   - Add stocks to watchlist
   - Remove stocks from watchlist
   - Switch between watchlists

## Rollback Plan

If you need to revert to SQLite-only operation:

1. **In `data/db_integration.py`:**
   ```python
   USE_SUPABASE = False  # Force SQLite usage
   ```

2. **In `services/watchlist_manager.py`:**
   ```python
   def __init__(self):
       self.data_fetcher = StockDataFetcher()
       self.use_supabase = False  # Force SQLite
       self._ensure_default_watchlist()
   ```

## Benefits of Supabase Storage

1. **Cloud Sync:** Watchlists accessible from any device
2. **Multi-user Support:** Different users can have separate watchlists
3. **Backup:** Automatic cloud backups
4. **Scalability:** Better performance for large watchlists
5. **Real-time Updates:** Potential for real-time collaboration

## Important Notes

- The system will **automatically fall back to SQLite** if Supabase is unavailable
- All existing watchlist functionality remains unchanged from the user's perspective
- Data is NOT automatically synced between SQLite and Supabase
- Consider running the migration script during low-usage periods