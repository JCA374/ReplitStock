import logging
from datetime import datetime
from typing import List, Dict, Optional

from data.db_manager import get_db_session
from data.db_models import WatchlistCollection, WatchlistMembership, Watchlist
from data.stock_data import StockDataFetcher

logger = logging.getLogger(__name__)

class SimpleWatchlistManager:
    """Simple watchlist manager with multiple named watchlists using SQLite"""
    
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
    
    def _ensure_default_watchlist(self):
        """Ensure at least one default watchlist exists"""
        # Try Supabase first
        if self.use_supabase:
            collections = self.supabase_db.get_all_watchlist_collections()
            default_exists = any(c.get('is_default', False) for c in collections)
            
            if not default_exists:
                result = self.supabase_db.create_watchlist_collection(
                    "My Watchlist", 
                    "Default watchlist", 
                    is_default=True
                )
                if result:
                    logger.info("Created default watchlist in Supabase")
                    return
        
        # Fall back to SQLite
        session = get_db_session()
        try:
            default = session.query(WatchlistCollection).filter(
                WatchlistCollection.is_default == True
            ).first()
            
            if not default:
                # Create default watchlist
                default = WatchlistCollection(
                    name="My Watchlist",
                    description="Default watchlist",
                    created_date=datetime.now().strftime("%Y-%m-%d"),
                    is_default=True
                )
                session.add(default)
                session.commit()
                logger.info("Created default watchlist in SQLite")
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating default watchlist: {e}")
        finally:
            session.close()
    
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
            # Check if name already exists
            existing = session.query(WatchlistCollection).filter(
                WatchlistCollection.name == name
            ).first()
            
            if existing:
                return False
            
            new_collection = WatchlistCollection(
                name=name,
                description=description,
                created_date=datetime.now().strftime("%Y-%m-%d"),
                is_default=False
            )
            session.add(new_collection)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating watchlist: {e}")
            return False
        finally:
            session.close()
    
    def delete_watchlist(self, watchlist_id: int) -> bool:
        """Delete a watchlist collection"""
        session = get_db_session()
        try:
            collection = session.query(WatchlistCollection).filter(
                WatchlistCollection.id == watchlist_id
            ).first()
            
            if not collection or collection.is_default:
                return False
            
            # Delete all memberships first
            session.query(WatchlistMembership).filter(
                WatchlistMembership.collection_id == watchlist_id
            ).delete()
            
            # Delete the collection
            session.delete(collection)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting watchlist: {e}")
            return False
        finally:
            session.close()
    
    def add_stock_to_watchlist(self, watchlist_id: int, ticker: str) -> bool:
        """Add a stock to a specific watchlist"""
        # Try Supabase first
        if self.use_supabase:
            result = self.supabase_db.add_to_watchlist_collection(watchlist_id, ticker)
            if result:
                return True
        
        # Fall back to SQLite
        session = get_db_session()
        try:
            # Check if already exists
            existing = session.query(WatchlistMembership).filter(
                WatchlistMembership.collection_id == watchlist_id,
                WatchlistMembership.ticker == ticker
            ).first()
            
            if existing:
                return False
            
            # Add to watchlist
            membership = WatchlistMembership(
                collection_id=watchlist_id,
                ticker=ticker,
                added_date=datetime.now().strftime("%Y-%m-%d")
            )
            session.add(membership)
            
            # Also add to legacy watchlist table for compatibility
            from data.db_integration import add_to_watchlist
            try:
                info = self.data_fetcher.get_stock_info(ticker)
                add_to_watchlist(
                    ticker,
                    info.get('name', ticker),
                    info.get('exchange', ''),
                    info.get('sector', '')
                )
            except:
                pass
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding stock to watchlist: {e}")
            return False
        finally:
            session.close()
    
    def remove_stock_from_watchlist(self, watchlist_id: int, ticker: str) -> bool:
        """Remove a stock from a specific watchlist"""
        # Try Supabase first
        if self.use_supabase:
            result = self.supabase_db.remove_from_watchlist_collection(watchlist_id, ticker)
            if result:
                return True
        
        # Fall back to SQLite
        session = get_db_session()
        try:
            membership = session.query(WatchlistMembership).filter(
                WatchlistMembership.collection_id == watchlist_id,
                WatchlistMembership.ticker == ticker
            ).first()
            
            if membership:
                session.delete(membership)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"Error removing stock from watchlist: {e}")
            return False
        finally:
            session.close()
    
    def get_watchlist_stocks(self, watchlist_id: int) -> List[str]:
        """Get all stock tickers in a specific watchlist"""
        # Try Supabase first
        if self.use_supabase:
            stocks = self.supabase_db.get_watchlist_collection_stocks(watchlist_id)
            if stocks is not None:
                return stocks
        
        # Fall back to SQLite
        session = get_db_session()
        try:
            memberships = session.query(WatchlistMembership).filter(
                WatchlistMembership.collection_id == watchlist_id
            ).all()
            return [m.ticker for m in memberships]
        finally:
            session.close()
    
    def get_watchlist_stock_count(self, watchlist_id: int) -> int:
        """Get count of stocks in a watchlist (fast method)"""
        # Try Supabase first
        if self.use_supabase:
            stocks = self.supabase_db.get_watchlist_collection_stocks(watchlist_id)
            if stocks is not None:
                return len(stocks)
        
        # Fall back to SQLite
        session = get_db_session()
        try:
            count = session.query(WatchlistMembership).filter(
                WatchlistMembership.collection_id == watchlist_id
            ).count()
            return count
        finally:
            session.close()
    
    def get_watchlist_details(self, watchlist_id: int) -> List[Dict]:
        """Get detailed information for all stocks in a watchlist (optimized for speed)"""
        tickers = self.get_watchlist_stocks(watchlist_id)
        # Sort tickers alphabetically
        tickers.sort()
        details = []
        
        for ticker in tickers:
            try:
                # Only get basic stock info, skip price data for speed
                info = self.data_fetcher.get_stock_info(ticker)
                
                details.append({
                    'ticker': ticker,
                    'name': info.get('name', ticker),
                    'sector': info.get('sector', ''),
                    'exchange': info.get('exchange', ''),
                })
            except Exception as e:
                logger.warning(f"Error getting details for {ticker}: {e}")
                details.append({
                    'ticker': ticker,
                    'name': ticker,
                    'sector': 'Unknown',
                    'exchange': 'Unknown',
                })
        
        return details