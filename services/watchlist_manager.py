import logging
from datetime import datetime
from typing import List, Dict, Optional

from data.db_manager import get_db_session
from data.db_models import WatchlistCollection, WatchlistMembership, Watchlist
from data.stock_data import StockDataFetcher

logger = logging.getLogger(__name__)

class SimpleWatchlistManager:
    """Simple watchlist manager using SQLite exclusively"""
    
    def __init__(self):
        self.data_fetcher = StockDataFetcher()
        logger.info("Using SQLite exclusively for watchlist storage")
        self._ensure_default_watchlist()
    
    def _ensure_default_watchlist(self):
        """Ensure at least one default watchlist exists"""
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
                
                # Add some default Swedish stocks to the watchlist
                self._populate_default_stocks(default.id)
                
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating default watchlist: {e}")
        finally:
            session.close()
    
    def _populate_default_stocks(self, watchlist_id: int):
        """Add some default Swedish stocks to the default watchlist"""
        default_stocks = [
            "VOLV-B.ST", "ERIC-B.ST", "ABB.ST", "ASSA-B.ST", "ALFA.ST",
            "HM-B.ST", "SAND.ST", "SKF-B.ST", "ATCO-A.ST", "SWED-A.ST"
        ]
        
        for ticker in default_stocks:
            try:
                self.add_stock_to_watchlist(watchlist_id, ticker)
            except Exception as e:
                logger.error(f"Error adding default stock {ticker}: {e}")
                continue
    
    def get_all_watchlists(self) -> List[Dict]:
        """Get all watchlist collections from SQLite database."""
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
        """Create a new watchlist collection in SQLite database."""
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
    
    def add_stock_to_watchlist(self, watchlist_id: int, ticker: str, name: str = None) -> bool:
        """Add a stock to a specific watchlist with optional name"""
        session = get_db_session()
        try:
            # Check if already exists
            existing = session.query(WatchlistMembership).filter(
                WatchlistMembership.collection_id == watchlist_id,
                WatchlistMembership.ticker == ticker
            ).first()
            
            if existing:
                return False
            
            # If name not provided, use ticker as name
            if not name:
                name = ticker
            
            # Add to watchlist with name
            membership = WatchlistMembership(
                collection_id=watchlist_id,
                ticker=ticker,
                name=name,  # Store the company name
                added_date=datetime.now().strftime("%Y-%m-%d")
            )
            session.add(membership)
            
            # Also add to legacy watchlist table for compatibility
            from data.db_integration import add_to_watchlist
            try:
                add_to_watchlist(
                    ticker,
                    name,  # Use the provided name
                    '',    # No exchange data needed
                    ''     # No sector data needed
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
        session = get_db_session()
        try:
            memberships = session.query(WatchlistMembership).filter(
                WatchlistMembership.collection_id == watchlist_id
            ).all()
            return [m.ticker for m in memberships]
        finally:
            session.close()
    
    def get_watchlist_stock_count(self, watchlist_id: int) -> int:
        """Get the number of stocks in a specific watchlist"""
        session = get_db_session()
        try:
            count = session.query(WatchlistMembership).filter(
                WatchlistMembership.collection_id == watchlist_id
            ).count()
            return count
        finally:
            session.close()
    
    def get_watchlist_details(self, watchlist_id: int) -> List[Dict]:
        """Get ticker and name for all stocks in a watchlist (no API calls)"""
        session = get_db_session()
        try:
            # Query the database directly for stored ticker and name
            stocks = session.query(WatchlistMembership).filter(
                WatchlistMembership.collection_id == watchlist_id
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
        finally:
            session.close()
    
    def import_watchlist_from_csv(self, watchlist_id: int, csv_content: str) -> tuple[int, int]:
        """
        Import stocks from CSV content into a watchlist
        
        Returns:
            tuple: (successful_imports, total_tickers)
        """
        import csv
        import io
        
        successful = 0
        total = 0
        
        try:
            # Parse CSV content
            csv_file = io.StringIO(csv_content)
            reader = csv.reader(csv_file)
            
            tickers = []
            for row in reader:
                if row:  # Skip empty rows
                    # Take the first non-empty column value
                    ticker = None
                    for cell in row:
                        if cell and cell.strip():
                            ticker = cell.strip().upper()
                            break
                    
                    if ticker:
                        # Normalize Swedish tickers
                        from utils.ticker_mapping import normalize_ticker
                        ticker = normalize_ticker(ticker)
                        tickers.append(ticker)
            
            # Add tickers to watchlist
            for ticker in tickers:
                total += 1
                # Try to get company name during import (optional enhancement)
                name = ticker  # Default to ticker if name lookup fails
                try:
                    # Optional: Quick lookup for name without full data fetch
                    info = self.data_fetcher.get_stock_info(ticker)
                    if info and info.get('name'):
                        name = str(info.get('name'))  # Ensure it's a string
                except:
                    pass
                
                if self.add_stock_to_watchlist(watchlist_id, ticker, name):
                    successful += 1
                    
        except Exception as e:
            logger.error(f"Error importing CSV: {e}")
        
        return successful, total