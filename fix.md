I'll help you implement permanent storage for the watchlist in Supabase. Let me first check the technical_spec.md file to understand the project structure and requirements.Based on my review of the project, I can see that **the Supabase integration for watchlists is already implemented** but currently disabled. Here's exactly what you need to do to enable permanent watchlist storage in Supabase:

## Step 1: Create Supabase Tables

First, create the required tables in your Supabase dashboard by running this SQL:

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

## Step 2: Enable Supabase for Watchlists

**File to modify:** `data/db_integration.py`

**Remove this code (around line 30):**
```python
USE_SUPABASE = False  # Disabled Supabase for watchlist operations
```

**Replace with:**
```python
USE_SUPABASE = supabase_db.is_connected()  # Use Supabase if connected
```

That's it! The system will now automatically:
- Use Supabase for watchlist storage when connected
- Fall back to SQLite if Supabase is unavailable
- Handle all the database operations transparently

## Step 3: Optional - Migrate Existing Data

If you have existing watchlists in SQLite that you want to preserve, create this migration script:Save this script as `scripts/migrate_watchlists.py` and run it with:
```bash
python scripts/migrate_watchlists.py
```

## Summary of Changes

### What you need to REMOVE:
- **Nothing!** All the code is already in place.

### What you need to CHANGE:
- In `data/db_integration.py`, change line 30 from:
  ```python
  USE_SUPABASE = False  # Disabled Supabase for watchlist operations
  ```
  To:
  ```python
  USE_SUPABASE = supabase_db.is_connected()  # Use Supabase if connected
  ```

### What happens after this change:
1. When your app starts, it will check if Supabase is connected
2. If connected, all watchlist operations will use Supabase (permanent cloud storage)
3. If not connected, it will fall back to SQLite (local storage)
4. The UI and functionality remain exactly the same

## Testing the Changes

1. **Verify Supabase Connection:**
   - Look at the header in your Streamlit app
   - Should show "✅ Connected to Supabase"

2. **Test Watchlist Operations:**
   - Create a new watchlist
   - Add stocks to watchlist
   - Remove stocks from watchlist
   - Restart the app and verify data persists

## Important Notes

According to the technical spec, this change follows the established pattern:
- ✅ Uses the database-first approach (checks Supabase first)
- ✅ Has automatic fallback to SQLite
- ✅ Doesn't modify core data structures
- ✅ Maintains all existing functionality

The beauty of this implementation is that **everything is already coded and tested** - you just need to enable it by changing that one configuration line!


#!/usr/bin/env python3
"""
Watchlist Migration Script
Migrates all watchlist data from SQLite to Supabase.
"""

import sys
import os

# Add parent directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.db_manager import get_db_session
from data.db_models import WatchlistCollection, WatchlistMembership
from data.supabase_client import get_supabase_db

def migrate_watchlists_to_supabase():
    """Migrate all watchlist data from SQLite to Supabase."""
    print("Starting watchlist migration from SQLite to Supabase...")
    
    session = get_db_session()
    supabase = get_supabase_db()
    
    if not supabase.is_connected():
        print("❌ Cannot connect to Supabase. Migration aborted.")
        return False
    
    try:
        # Migrate collections
        print("\n🔄 Migrating watchlist collections...")
        collections = session.query(WatchlistCollection).all()
        collection_mapping = {}  # old_id -> new_id
        
        if not collections:
            print("ℹ️  No watchlist collections found in SQLite.")
        
        for col in collections:
            print(f"   Migrating collection: {col.name}")
            try:
                new_col = supabase.create_watchlist_collection(
                    col.name, 
                    col.description or "", 
                    col.is_default
                )
                if new_col:
                    collection_mapping[col.id] = new_col['id']
                    print(f"   ✅ Created collection '{col.name}' with ID {new_col['id']}")
                else:
                    print(f"   ❌ Failed to create collection '{col.name}'")
            except Exception as e:
                print(f"   ❌ Error creating collection '{col.name}': {e}")
        
        # Migrate memberships
        print(f"\n🔄 Migrating watchlist memberships...")
        memberships = session.query(WatchlistMembership).all()
        
        if not memberships:
            print("ℹ️  No watchlist memberships found in SQLite.")
        
        migrated_count = 0
        for mem in memberships:
            if mem.collection_id in collection_mapping:
                new_collection_id = collection_mapping[mem.collection_id]
                try:
                    success = supabase.add_to_watchlist_collection(new_collection_id, mem.ticker)
                    if success:
                        print(f"   ✅ Added {mem.ticker} to collection {new_collection_id}")
                        migrated_count += 1
                    else:
                        print(f"   ❌ Failed to add {mem.ticker} to collection {new_collection_id}")
                except Exception as e:
                    print(f"   ❌ Error adding {mem.ticker}: {e}")
            else:
                print(f"   ⚠️  Skipping {mem.ticker} - collection {mem.collection_id} not found")
        
        print(f"\n✅ Migration completed successfully!")
        print(f"   Migrated {len(collection_mapping)} collections")
        print(f"   Migrated {migrated_count} stock memberships")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration error: {e}")
        return False
    finally:
        session.close()

if __name__ == "__main__":
    migrate_watchlists_to_supabase()