Based on your codebase analysis, I'll create a comprehensive fix.md file for Claude to implement a clean watchlist feature. Here's the content:

```markdown
# Watchlist Feature Fix Instructions

## 🎯 Goal
Consolidate the watchlist feature into a single, clean implementation using SQLite storage with support for multiple named watchlists.

## 🗑️ Files to Remove
Delete these files completely as they create confusion:
- `ui/watchlist_enhanced.py`
- Remove the "Enhanced Watchlist" tab from `app.py`

## 📝 Database Schema Updates

### 1. Update `data/db_models.py`
Add a new model for watchlist collections after the existing `Watchlist` model:

```python
class WatchlistCollection(Base):
    __tablename__ = 'watchlist_collections'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True)
    description = Column(String(200))
    created_date = Column(String(20))
    is_default = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<WatchlistCollection(name='{self.name}')>"

class WatchlistMembership(Base):
    __tablename__ = 'watchlist_memberships'
    
    id = Column(Integer, primary_key=True)
    collection_id = Column(Integer)
    ticker = Column(String(20))
    added_date = Column(String(20))
    
    __table_args__ = (
        UniqueConstraint('collection_id', 'ticker', name='unique_collection_ticker'),
    )
    
    def __repr__(self):
        return f"<WatchlistMembership(collection_id={self.collection_id}, ticker='{self.ticker}')>"
```

## 📦 Simplified Watchlist Manager

### 2. Replace `services/watchlist_manager.py`
Replace the entire file with this simplified version:

```python
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
                logger.info("Created default watchlist")
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating default watchlist: {e}")
        finally:
            session.close()
    
    def get_all_watchlists(self) -> List[Dict]:
        """Get all watchlist collections"""
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
        """Create a new watchlist collection"""
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
    
    def get_watchlist_details(self, watchlist_id: int) -> List[Dict]:
        """Get detailed information for all stocks in a watchlist"""
        tickers = self.get_watchlist_stocks(watchlist_id)
        details = []
        
        for ticker in tickers:
            try:
                info = self.data_fetcher.get_stock_info(ticker)
                stock_data = self.data_fetcher.get_stock_data(ticker, '1d', '5d')
                
                if not stock_data.empty:
                    current_price = stock_data['close'].iloc[-1]
                    prev_price = stock_data['close'].iloc[-2] if len(stock_data) > 1 else current_price
                    change_pct = ((current_price - prev_price) / prev_price * 100) if prev_price > 0 else 0
                    
                    details.append({
                        'ticker': ticker,
                        'name': info.get('name', ticker),
                        'sector': info.get('sector', ''),
                        'exchange': info.get('exchange', ''),
                        'current_price': current_price,
                        'change_pct': change_pct
                    })
            except Exception as e:
                logger.warning(f"Error getting details for {ticker}: {e}")
                details.append({
                    'ticker': ticker,
                    'name': ticker,
                    'sector': 'Unknown',
                    'exchange': 'Unknown',
                    'current_price': 0,
                    'change_pct': 0
                })
        
        return details
```

## 🎨 Updated UI

### 3. Replace `ui/watchlist.py`
Replace the entire file with this clean implementation:

```python
import streamlit as st
import pandas as pd
from services.watchlist_manager import SimpleWatchlistManager
from utils.ticker_mapping import normalize_ticker

def display_watchlist():
    """Display the unified watchlist interface"""
    st.header("📊 Watchlists")
    
    # Initialize watchlist manager
    if 'watchlist_manager' not in st.session_state:
        st.session_state.watchlist_manager = SimpleWatchlistManager()
    
    manager = st.session_state.watchlist_manager
    
    # Get all watchlists
    watchlists = manager.get_all_watchlists()
    
    # Sidebar for watchlist management
    with st.sidebar:
        st.subheader("Watchlist Management")
        
        # Create new watchlist
        with st.expander("➕ Create New Watchlist"):
            new_name = st.text_input("Watchlist Name", key="new_watchlist_name")
            new_desc = st.text_area("Description (optional)", key="new_watchlist_desc")
            
            if st.button("Create", key="create_watchlist_btn"):
                if new_name:
                    if manager.create_watchlist(new_name, new_desc):
                        st.success(f"Created '{new_name}'")
                        st.rerun()
                    else:
                        st.error("Watchlist name already exists")
                else:
                    st.warning("Please enter a name")
    
    # Main content area
    if not watchlists:
        st.error("No watchlists found. This should not happen!")
        return
    
    # Watchlist selector
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        selected_watchlist = st.selectbox(
            "Select Watchlist",
            options=watchlists,
            format_func=lambda x: f"{x['name']} {'(Default)' if x['is_default'] else ''}",
            key="watchlist_selector"
        )
    
    with col2:
        if st.button("🔄 Refresh", key="refresh_watchlist"):
            st.rerun()
    
    with col3:
        if selected_watchlist and not selected_watchlist['is_default']:
            if st.button("🗑️ Delete", key="delete_watchlist"):
                if manager.delete_watchlist(selected_watchlist['id']):
                    st.success("Watchlist deleted")
                    st.rerun()
    
    if selected_watchlist:
        watchlist_id = selected_watchlist['id']
        
        # Add stock section
        st.subheader("➕ Add Stock")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            ticker_input = st.text_input(
                "Enter ticker symbol",
                placeholder="e.g., AAPL, MSFT, VOLV-B.ST",
                key="add_ticker_input"
            )
        
        with col2:
            if st.button("Add to Watchlist", key="add_stock_btn"):
                if ticker_input:
                    ticker = normalize_ticker(ticker_input.upper())
                    if manager.add_stock_to_watchlist(watchlist_id, ticker):
                        st.success(f"Added {ticker}")
                        st.rerun()
                    else:
                        st.warning(f"{ticker} already in this watchlist")
                else:
                    st.warning("Please enter a ticker")
        
        # Display stocks in watchlist
        st.subheader(f"📈 Stocks in '{selected_watchlist['name']}'")
        
        # Get stock details
        stock_details = manager.get_watchlist_details(watchlist_id)
        
        if stock_details:
            # Create DataFrame for display
            df = pd.DataFrame(stock_details)
            
            # Add remove buttons column
            for idx, stock in enumerate(stock_details):
                col1, col2, col3, col4, col5, col6 = st.columns([0.5, 1.5, 2, 1.5, 1, 1])
                
                with col1:
                    if st.button("❌", key=f"remove_{stock['ticker']}_{idx}"):
                        if manager.remove_stock_from_watchlist(watchlist_id, stock['ticker']):
                            st.success(f"Removed {stock['ticker']}")
                            st.rerun()
                
                with col2:
                    st.write(f"**{stock['ticker']}**")
                
                with col3:
                    st.write(stock['name'])
                
                with col4:
                    st.write(stock['sector'])
                
                with col5:
                    st.metric("Price", f"${stock['current_price']:.2f}")
                
                with col6:
                    color = "green" if stock['change_pct'] >= 0 else "red"
                    st.markdown(
                        f"<span style='color: {color}'>{stock['change_pct']:+.2f}%</span>",
                        unsafe_allow_html=True
                    )
            
            # Action buttons
            st.divider()
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📊 Analyze This Watchlist", type="primary", key="analyze_watchlist"):
                    # Store watchlist tickers in session state for batch analysis
                    tickers = [s['ticker'] for s in stock_details]
                    st.session_state['batch_analysis_tickers'] = tickers
                    st.session_state['selected_page'] = 'Batch Analysis'
                    st.success(f"Ready to analyze {len(tickers)} stocks. Go to Batch Analysis tab.")
            
            with col2:
                # Export functionality
                if st.button("📥 Export to CSV", key="export_watchlist"):
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"watchlist_{selected_watchlist['name']}_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
        else:
            st.info("This watchlist is empty. Add stocks using the form above.")
```

## 🔧 App.py Updates

### 4. Update `app.py`
In the main() function, find the navigation section and:

**REMOVE:**
```python
page = st.sidebar.radio(
    "Select a page:",
    ["Single Stock Analysis", "Batch Analysis", "Watchlist", "Enhanced Watchlist"]
)
```

**REPLACE WITH:**
```python
page = st.sidebar.radio(
    "Select a page:",
    ["Single Stock Analysis", "Batch Analysis", "Watchlist"]
)
```

**REMOVE** the Enhanced Watchlist page handling:
```python
elif page == "Enhanced Watchlist":
    display_enhanced_watchlist()
```

**UPDATE** the imports section:
Remove:
```python
from ui.watchlist_enhanced import display_enhanced_watchlist
```

## 🔄 Integration with Batch Analysis

### 5. Update `ui/batch_analysis.py`
In the `display_batch_analysis()` function, add this option to the analysis mode selection:

```python
# In the analysis_mode radio button options, add:
analysis_mode = st.sidebar.radio(
    "Analysis Mode:",
    ["All Watchlist Stocks", "Selected Watchlist", "All Small Cap",
        "All Mid Cap", "All Large Cap", "Selected Stocks"],
    key="batch_analysis_mode"
)

# Add this case to handle "Selected Watchlist":
elif analysis_mode == "Selected Watchlist":
    # Get all watchlists
    if 'watchlist_manager' not in st.session_state:
        from services.watchlist_manager import SimpleWatchlistManager
        st.session_state.watchlist_manager = SimpleWatchlistManager()
    
    manager = st.session_state.watchlist_manager
    watchlists = manager.get_all_watchlists()
    
    if watchlists:
        selected_wl = st.sidebar.selectbox(
            "Select Watchlist",
            options=watchlists,
            format_func=lambda x: x['name'],
            key="batch_watchlist_select"
        )
        
        if selected_wl:
            tickers = manager.get_watchlist_stocks(selected_wl['id'])
            selected_tickers = tickers
            st.success(f"Ready to analyze {len(tickers)} stocks from '{selected_wl['name']}'")
    else:
        st.warning("No watchlists available")
        selected_tickers = []
```

## 🧹 Cleanup Session State

### 6. Update `app.py` initialization
In the session state initialization section, **REPLACE**:

```python
if 'watchlist_manager' not in st.session_state:
    st.session_state.db_storage = create_db_storage()
    st.session_state.watchlist_manager = WatchlistManager()
```

**WITH:**
```python
if 'watchlist_manager' not in st.session_state:
    from services.watchlist_manager import SimpleWatchlistManager
    st.session_state.watchlist_manager = SimpleWatchlistManager()
```

## ✅ Summary
This fix will give you:
- A single, clean "Watchlist" tab
- Support for multiple named watchlists stored in SQLite
- Easy add/remove functionality
- Integration with batch analysis
- Clean, maintainable code

The implementation removes all the complex "enhanced" features and focuses on core functionality that works reliably with SQLite storage.
```

This fix.md file provides Claude with clear, step-by-step instructions to implement a clean watchlist feature that meets all your requirements. The implementation:

1. Uses SQLite exclusively
2. Supports multiple named watchlists
3. Has a single "Watchlist" tab
4. Allows easy add/remove operations
5. Integrates with batch analysis for scanning
6. Removes all the confusing enhanced features

The code is clean, straightforward, and maintainable.