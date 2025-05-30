# services/watchlist_manager.py - COMPLETE REPLACEMENT

import streamlit as st
import pandas as pd
import logging
from datetime import datetime, timedelta
import json
from typing import List, Dict, Optional, Tuple

from data.db_manager import get_db_session
from data.db_models import WatchlistCategory, WatchlistItem, WatchlistAlert
from data.stock_data import StockDataFetcher
from data.db_integration import add_to_watchlist, remove_from_watchlist, get_watchlist

class EnhancedWatchlistManager:
    """
    Enhanced watchlist manager with categories, tags, alerts, and performance tracking
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.data_fetcher = StockDataFetcher()
        self._ensure_default_categories()
        
    def _ensure_default_categories(self):
        """Ensure default categories exist"""
        session = get_db_session()
        try:
            default_categories = [
                {"name": "Portfolio", "color": "#28a745", "icon": "💼", 
                 "description": "Stocks I currently own"},
                {"name": "Watchlist", "color": "#007bff", "icon": "👁️", 
                 "description": "Stocks I'm monitoring"},
                {"name": "Buy Candidates", "color": "#ffc107", "icon": "🎯", 
                 "description": "Potential buy opportunities"},
                {"name": "Earnings Watch", "color": "#6f42c1", "icon": "📊", 
                 "description": "Upcoming earnings"},
                {"name": "High Risk", "color": "#dc3545", "icon": "⚠️", 
                 "description": "Volatile or risky positions"}
            ]
            
            for cat in default_categories:
                existing = session.query(WatchlistCategory).filter(
                    WatchlistCategory.name == cat["name"]
                ).first()
                
                if not existing:
                    new_cat = WatchlistCategory(
                        name=cat["name"],
                        color=cat["color"],
                        icon=cat["icon"],
                        description=cat["description"],
                        created_date=datetime.now().strftime("%Y-%m-%d")
                    )
                    session.add(new_cat)
            
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error creating default categories: {e}")
        finally:
            session.close()
    
    def get_categories(self) -> List[Dict]:
        """Get all watchlist categories"""
        session = get_db_session()
        try:
            categories = session.query(WatchlistCategory).all()
            return [
                {
                    "id": cat.id,
                    "name": cat.name,
                    "color": cat.color,
                    "icon": cat.icon,
                    "description": cat.description
                }
                for cat in categories
            ]
        finally:
            session.close()
    
    def add_category(self, name: str, color: str = "#6c757d", 
                    icon: str = "📌", description: str = "") -> bool:
        """Add a new category"""
        session = get_db_session()
        try:
            new_cat = WatchlistCategory(
                name=name,
                color=color,
                icon=icon,
                description=description,
                created_date=datetime.now().strftime("%Y-%m-%d")
            )
            session.add(new_cat)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error adding category: {e}")
            return False
        finally:
            session.close()
    
    def add_stock_enhanced(self, ticker: str, category_id: int, 
                          tags: List[str] = None, notes: str = "",
                          target_price: float = None, 
                          stop_loss: float = None) -> bool:
        """Add stock with enhanced metadata"""
        session = get_db_session()
        try:
            # Get current price
            stock_data = self.data_fetcher.get_stock_data(ticker, '1d', '5d')
            current_price = stock_data['close'].iloc[-1] if not stock_data.empty else 0
            
            # Check if already exists in category
            existing = session.query(WatchlistItem).filter(
                WatchlistItem.ticker == ticker,
                WatchlistItem.category_id == category_id
            ).first()
            
            if existing:
                return False
            
            # Create new item
            new_item = WatchlistItem(
                ticker=ticker,
                category_id=category_id,
                tags=json.dumps(tags or []),
                notes=notes,
                target_price=target_price,
                stop_loss=stop_loss,
                added_date=datetime.now().strftime("%Y-%m-%d"),
                added_price=current_price
            )
            session.add(new_item)
            session.commit()
            
            # Also add to legacy watchlist for compatibility
            stock_info = self.data_fetcher.get_stock_info(ticker)
            add_to_watchlist(ticker, stock_info.get('name', ticker), 
                           stock_info.get('exchange', ''), 
                           stock_info.get('sector', ''))
            
            return True
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error adding stock: {e}")
            return False
        finally:
            session.close()
    
    def get_watchlist_by_category(self, category_id: int = None) -> pd.DataFrame:
        """Get watchlist items with current prices and performance"""
        session = get_db_session()
        try:
            query = session.query(WatchlistItem)
            if category_id:
                query = query.filter(WatchlistItem.category_id == category_id)
            
            items = query.all()
            
            if not items:
                return pd.DataFrame()
            
            # Build dataframe with current data
            data = []
            for item in items:
                try:
                    # Get current price
                    stock_data = self.data_fetcher.get_stock_data(
                        item.ticker, '1d', '5d'
                    )
                    
                    if not stock_data.empty:
                        current_price = stock_data['close'].iloc[-1]
                        prev_close = stock_data['close'].iloc[-2] if len(stock_data) > 1 else current_price
                        daily_change = ((current_price - prev_close) / prev_close) * 100
                        
                        # Calculate performance since added
                        if item.added_price and item.added_price > 0:
                            total_return = ((current_price - item.added_price) / item.added_price) * 100
                        else:
                            total_return = 0
                        
                        # Get stock info
                        info = self.data_fetcher.get_stock_info(item.ticker)
                        
                        # Check alerts
                        alert_triggered = False
                        if item.target_price and current_price >= item.target_price:
                            alert_triggered = "Target reached!"
                        elif item.stop_loss and current_price <= item.stop_loss:
                            alert_triggered = "Stop loss triggered!"
                        
                        data.append({
                            'id': item.id,
                            'ticker': item.ticker,
                            'name': info.get('name', item.ticker),
                            'sector': info.get('sector', ''),
                            'current_price': current_price,
                            'daily_change': daily_change,
                            'added_date': item.added_date,
                            'added_price': item.added_price,
                            'total_return': total_return,
                            'target_price': item.target_price,
                            'stop_loss': item.stop_loss,
                            'tags': json.loads(item.tags) if item.tags else [],
                            'notes': item.notes,
                            'alert': alert_triggered,
                            'category_id': item.category_id
                        })
                    
                except Exception as e:
                    self.logger.warning(f"Error processing {item.ticker}: {e}")
                    continue
            
            return pd.DataFrame(data)
            
        finally:
            session.close()
    
    def set_alert(self, ticker: str, alert_type: str, 
                  threshold: float, message: str = "") -> bool:
        """Set a price or technical alert"""
        session = get_db_session()
        try:
            new_alert = WatchlistAlert(
                ticker=ticker,
                alert_type=alert_type,
                threshold=threshold,
                message=message,
                created_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            session.add(new_alert)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error setting alert: {e}")
            return False
        finally:
            session.close()
    
    def check_alerts(self) -> List[Dict]:
        """Check all active alerts and return triggered ones"""
        session = get_db_session()
        triggered_alerts = []
        
        try:
            active_alerts = session.query(WatchlistAlert).filter(
                WatchlistAlert.is_active == True
            ).all()
            
            for alert in active_alerts:
                try:
                    # Get current data
                    stock_data = self.data_fetcher.get_stock_data(
                        alert.ticker, '1d', '1d'
                    )
                    
                    if not stock_data.empty:
                        current_price = stock_data['close'].iloc[-1]
                        triggered = False
                        
                        if alert.alert_type == 'price_above' and current_price >= alert.threshold:
                            triggered = True
                        elif alert.alert_type == 'price_below' and current_price <= alert.threshold:
                            triggered = True
                        
                        if triggered:
                            triggered_alerts.append({
                                'ticker': alert.ticker,
                                'type': alert.alert_type,
                                'threshold': alert.threshold,
                                'current_price': current_price,
                                'message': alert.message
                            })
                            
                            # Mark as triggered
                            alert.is_active = False
                            alert.triggered_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            
                except Exception as e:
                    self.logger.warning(f"Error checking alert for {alert.ticker}: {e}")
            
            session.commit()
            
        finally:
            session.close()
        
        return triggered_alerts
    
    def get_performance_summary(self, category_id: int = None) -> Dict:
        """Get performance summary of watchlist"""
        df = self.get_watchlist_by_category(category_id)
        
        if df.empty:
            return {}
        
        # Calculate metrics
        total_stocks = len(df)
        avg_return = df['total_return'].mean()
        winners = len(df[df['total_return'] > 0])
        losers = len(df[df['total_return'] < 0])
        
        # Best and worst performers
        best = df.nlargest(3, 'total_return')[['ticker', 'name', 'total_return']]
        worst = df.nsmallest(3, 'total_return')[['ticker', 'name', 'total_return']]
        
        return {
            'total_stocks': total_stocks,
            'average_return': avg_return,
            'winners': winners,
            'losers': losers,
            'best_performers': best.to_dict('records'),
            'worst_performers': worst.to_dict('records')
        }

# Legacy WatchlistManager for backward compatibility
class WatchlistManager:
    """
    Legacy manager for watchlist operations.
    Maintains backward compatibility with existing code.
    """
    
    def __init__(self):
        """
        Initialize the watchlist manager with SQLite storage.
        """
        self.logger = logging.getLogger(__name__)
        
        # Default watchlists
        self.default_watchlists = [
            {"name": "My Watchlist", "stocks": []},
            {"name": "Potential Buys", "stocks": []},
            {"name": "Portfolio", "stocks": []}
        ]
        
        # Initialize watchlists if not in session
        if 'watchlists' not in st.session_state:
            # Try to load from database
            db_watchlist = get_watchlist()
            
            if db_watchlist:
                # Create a single watchlist from database
                all_stocks = [item['ticker'] for item in db_watchlist]
                self.default_watchlists[0]["stocks"] = all_stocks
                
            st.session_state.watchlists = self.default_watchlists
            
        # Ensure all default watchlists exist
        self._ensure_default_watchlists()
        
        # Initialize active watchlist index if not set
        if 'active_watchlist_index' not in st.session_state:
            st.session_state.active_watchlist_index = 0
    
    def get_all_watchlists(self):
        """Get all watchlists."""
        return st.session_state.watchlists
    
    def add_watchlist(self, name):
        """Add a new watchlist."""
        # Check if watchlist name already exists
        existing_names = [w["name"] for w in st.session_state.watchlists]
        if name in existing_names:
            return False
            
        # Add new watchlist
        st.session_state.watchlists.append({"name": name, "stocks": []})
        return True
    
    def _ensure_default_watchlists(self):
        """Ensure all default watchlists exist in the session state."""
        default_names = set(wl["name"] for wl in self.default_watchlists)
        existing_names = set(wl["name"] for wl in st.session_state.watchlists)
        
        # Add missing watchlists
        for name in default_names - existing_names:
            for wl in self.default_watchlists:
                if wl["name"] == name:
                    st.session_state.watchlists.append({"name": name, "stocks": []})
    
    def delete_watchlist(self, index):
        """Delete a watchlist."""
        if index < 0 or index >= len(st.session_state.watchlists):
            return False
            
        # Don't delete the default watchlist
        if index == 0:
            return False
            
        # Delete watchlist
        st.session_state.watchlists.pop(index)
        return True
    
    def add_stock_to_watchlist(self, watchlist_index, ticker, add_to_db=True):
        """Add a stock to a specific watchlist."""
        if watchlist_index < 0 or watchlist_index >= len(st.session_state.watchlists):
            return False
            
        # Get watchlist
        watchlist = st.session_state.watchlists[watchlist_index]
        
        # Check if stock already exists
        if ticker in watchlist["stocks"]:
            return False
            
        # Add to watchlist
        watchlist["stocks"].append(ticker)
        
        # Add to database if requested
        if add_to_db and watchlist_index == 0:  # Only sync the main watchlist
            try:
                from data.stock_data import StockDataFetcher
                
                # Get stock info for database
                fetcher = StockDataFetcher()
                info = fetcher.get_stock_info(ticker)
                
                # Add to database
                add_to_watchlist(
                    ticker, 
                    info.get('shortName', ticker),
                    info.get('exchange', ''),
                    info.get('sector', '')
                )
            except Exception as e:
                self.logger.error(f"Error adding stock to database: {e}")
        
        return True
    
    def remove_stock_from_watchlist(self, watchlist_index, ticker, remove_from_db=True):
        """Remove a stock from a specific watchlist."""
        if watchlist_index < 0 or watchlist_index >= len(st.session_state.watchlists):
            return False
            
        # Get watchlist
        watchlist = st.session_state.watchlists[watchlist_index]
        
        # Check if stock exists
        if ticker not in watchlist["stocks"]:
            return False
            
        # Remove from watchlist
        watchlist["stocks"].remove(ticker)
        
        # Remove from database if requested
        if remove_from_db and watchlist_index == 0:  # Only sync the main watchlist
            try:
                remove_from_watchlist(ticker)
            except Exception as e:
                self.logger.error(f"Error removing stock from database: {e}")
        
        return True
        
    def get_active_watchlist_index(self):
        """Get the index of the currently active watchlist."""
        return st.session_state.active_watchlist_index
        
    def get_active_watchlist(self):
        """Get the currently active watchlist."""
        return st.session_state.watchlists[self.get_active_watchlist_index()]
        
    def set_active_watchlist(self, index):
        """Set the active watchlist by index."""
        if 0 <= index < len(st.session_state.watchlists):
            st.session_state.active_watchlist_index = index
            return True
        return False

    def rename_watchlist(self, index, new_name):
        """Rename a watchlist."""
        if index < 0 or index >= len(st.session_state.watchlists):
            return False

        # Check if the new name is empty or already exists
        if not new_name or new_name in [wl["name"] for wl in st.session_state.watchlists]:
            return False

        # Rename watchlist
        st.session_state.watchlists[index]["name"] = new_name
        return True