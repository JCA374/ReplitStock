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
        print(f"   Collections migrated: {len(collection_mapping)}")
        print(f"   Stocks migrated: {migrated_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        return False
    finally:
        session.close()

def verify_migration():
    """Verify that the migration was successful by comparing counts."""
    print("\n🔍 Verifying migration...")
    
    session = get_db_session()
    supabase = get_supabase_db()
    
    try:
        # Count SQLite data
        sqlite_collections = session.query(WatchlistCollection).count()
        sqlite_memberships = session.query(WatchlistMembership).count()
        
        # Count Supabase data
        supabase_collections = len(supabase.get_all_watchlist_collections())
        
        # Count total memberships in Supabase
        supabase_memberships = 0
        for collection in supabase.get_all_watchlist_collections():
            stocks = supabase.get_watchlist_collection_stocks(collection['id'])
            supabase_memberships += len(stocks)
        
        print(f"SQLite Collections: {sqlite_collections}")
        print(f"Supabase Collections: {supabase_collections}")
        print(f"SQLite Memberships: {sqlite_memberships}")
        print(f"Supabase Memberships: {supabase_memberships}")
        
        if sqlite_collections == supabase_collections and sqlite_memberships == supabase_memberships:
            print("✅ Migration verification successful - all data migrated!")
            return True
        else:
            print("⚠️  Migration verification shows differences - some data may not have migrated")
            return False
            
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        return False
    finally:
        session.close()

def main():
    """Main migration function."""
    print("=" * 60)
    print("  WATCHLIST MIGRATION SCRIPT")
    print("  SQLite → Supabase")
    print("=" * 60)
    
    # Check connections
    print("🔍 Checking database connections...")
    
    session = get_db_session()
    try:
        sqlite_collections = session.query(WatchlistCollection).count()
        print(f"✅ SQLite connected - {sqlite_collections} collections found")
    except Exception as e:
        print(f"❌ SQLite connection failed: {e}")
        return
    finally:
        session.close()
    
    supabase = get_supabase_db()
    if supabase.is_connected():
        print("✅ Supabase connected")
    else:
        print("❌ Supabase connection failed")
        return
    
    # Ask for confirmation
    print(f"\n⚠️  This will migrate all watchlist data from SQLite to Supabase.")
    print("   Existing Supabase data may be overwritten if names conflict.")
    
    response = input("\nProceed with migration? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("Migration cancelled.")
        return
    
    # Perform migration
    success = migrate_watchlists_to_supabase()
    
    if success:
        # Verify results
        verify_migration()
        
        print(f"\n🎉 Migration complete!")
        print("   You can now enable Supabase in your application settings.")
        print("   Your SQLite data remains unchanged as a backup.")
    else:
        print(f"\n❌ Migration failed. Please check the errors above.")

if __name__ == "__main__":
    main()