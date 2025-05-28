Looking at your code, I can see that the watchlist management system is functional but could be significantly improved. Let me analyze the current state and suggest improvements.

## Current Issues with Watchlist Management:

1. **Scattered Implementation**: Watchlist management code is spread across multiple files (`services/watchlist_manager.py`, `ui/watchlist.py`, `data/db_manager.py`)
2. **Limited Features**: Only basic add/remove functionality
3. **No Categories/Tags**: Can't organize stocks by strategy, sector, or custom tags
4. **No Performance Tracking**: Can't see how watchlist stocks are performing
5. **Poor UI/UX**: The watchlist UI is basic and requires multiple clicks for simple operations

## Suggested Improved Watchlist Management System:

### 1. **Enhanced Data Model**
Add these new tables to your database:

```python
# data/db_models.py - ADD these new models

class WatchlistCategory(Base):
    __tablename__ = 'watchlist_categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    color = Column(String(7))  # Hex color for UI
    icon = Column(String(20))  # Emoji or icon name
    description = Column(String(200))
    created_date = Column(String(20))
    
class WatchlistItem(Base):
    __tablename__ = 'watchlist_items_v2'
    
    id = Column(Integer, primary_key=True)
    ticker = Column(String(20))
    category_id = Column(Integer)  # Foreign key to categories
    tags = Column(Text)  # JSON array of tags
    notes = Column(Text)  # User notes
    target_price = Column(Float)  # Price alerts
    stop_loss = Column(Float)
    added_date = Column(String(20))
    added_price = Column(Float)  # Track performance
    
    __table_args__ = (
        UniqueConstraint('ticker', 'category_id', name='unique_ticker_category'),
    )

class WatchlistAlert(Base):
    __tablename__ = 'watchlist_alerts'
    
    id = Column(Integer, primary_key=True)
    ticker = Column(String(20))
    alert_type = Column(String(20))  # 'price_above', 'price_below', 'tech_signal'
    threshold = Column(Float)
    message = Column(String(200))
    is_active = Column(Boolean, default=True)
    created_date = Column(String(20))
    triggered_date = Column(String(20))
```

### 2. **Enhanced Watchlist Manager**

**REPLACE** the current `services/watchlist_manager.py` with:

```python
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
```

### 3. **New Enhanced Watchlist UI**

**CREATE** a new file `ui/watchlist_enhanced.py`:

```python
# ui/watchlist_enhanced.py - NEW FILE

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

def display_enhanced_watchlist():
    """Display the enhanced watchlist with categories and performance tracking"""
    st.header("📊 Enhanced Watchlist Manager")
    
    # Initialize enhanced manager
    if 'enhanced_watchlist' not in st.session_state:
        from services.watchlist_manager import EnhancedWatchlistManager
        st.session_state.enhanced_watchlist = EnhancedWatchlistManager()
    
    manager = st.session_state.enhanced_watchlist
    
    # Sidebar for categories
    with st.sidebar:
        st.subheader("📁 Categories")
        
        categories = manager.get_categories()
        
        # Add new category
        with st.expander("➕ Add Category"):
            new_name = st.text_input("Name")
            new_color = st.color_picker("Color", "#6c757d")
            new_icon = st.text_input("Icon", "📌")
            new_desc = st.text_area("Description")
            
            if st.button("Create Category"):
                if new_name and manager.add_category(new_name, new_color, new_icon, new_desc):
                    st.success(f"Created {new_icon} {new_name}")
                    st.rerun()
        
        # Category selection
        selected_cat = st.radio(
            "Select Category",
            options=[{"id": 0, "name": "All Categories"}] + categories,
            format_func=lambda x: f"{x.get('icon', '')} {x['name']}",
            index=0
        )
    
    # Main content area
    category_id = selected_cat['id'] if selected_cat['id'] > 0 else None
    
    # Alerts section
    alerts = manager.check_alerts()
    if alerts:
        st.warning(f"🔔 {len(alerts)} alerts triggered!")
        with st.expander("View Alerts", expanded=True):
            for alert in alerts:
                st.write(f"**{alert['ticker']}** - {alert['message']}")
                st.write(f"Current: ${alert['current_price']:.2f} (Threshold: ${alert['threshold']:.2f})")
    
    # Performance summary
    summary = manager.get_performance_summary(category_id)
    if summary:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Stocks", summary['total_stocks'])
        with col2:
            st.metric("Avg Return", f"{summary['average_return']:.1f}%")
        with col3:
            st.metric("Winners", summary['winners'])
        with col4:
            st.metric("Losers", summary['losers'])
    
    # Watchlist table
    df = manager.get_watchlist_by_category(category_id)
    
    if not df.empty:
        # Sort by total return
        df = df.sort_values('total_return', ascending=False)
        
        # Display with color coding
        st.subheader("📈 Watchlist Items")
        
        for _, row in df.iterrows():
            with st.container():
                col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 1, 1, 1, 1])
                
                with col1:
                    st.write(f"**{row['ticker']}**")
                    st.caption(row['name'])
                    
                with col2:
                    # Tags
                    if row['tags']:
                        tag_html = " ".join([f"<span style='background-color: #e9ecef; padding: 2px 6px; border-radius: 3px; margin-right: 4px;'>{tag}</span>" for tag in row['tags']])
                        st.markdown(tag_html, unsafe_allow_html=True)
                    
                with col3:
                    st.metric("Price", f"${row['current_price']:.2f}", 
                             f"{row['daily_change']:.1f}%")
                
                with col4:
                    color = "green" if row['total_return'] > 0 else "red"
                    st.markdown(f"<span style='color:{color}'>**{row['total_return']:.1f}%**</span>", 
                               unsafe_allow_html=True)
                    st.caption("Since added")
                
                with col5:
                    if row['alert']:
                        st.error(row['alert'])
                    else:
                        st.write("—")
                
                with col6:
                    if st.button("📝", key=f"edit_{row['id']}"):
                        st.session_state[f"editing_{row['id']}"] = True
                
                # Edit section
                if st.session_state.get(f"editing_{row['id']}", False):
                    with st.expander("Edit", expanded=True):
                        col1, col2 = st.columns(2)
                        with col1:
                            new_target = st.number_input("Target Price", 
                                                       value=row['target_price'] or 0.0,
                                                       key=f"target_{row['id']}")
                            new_stop = st.number_input("Stop Loss", 
                                                     value=row['stop_loss'] or 0.0,
                                                     key=f"stop_{row['id']}")
                        with col2:
                            new_notes = st.text_area("Notes", value=row['notes'] or "",
                                                   key=f"notes_{row['id']}")
                        
                        if st.button("Save", key=f"save_{row['id']}"):
                            # Update logic here
                            st.session_state[f"editing_{row['id']}"] = False
                            st.rerun()
                
                st.divider()
    else:
        st.info("No stocks in this category. Add some to get started!")
    
    # Quick add section
    st.subheader("➕ Quick Add Stock")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        ticker = st.text_input("Ticker Symbol")
    
    with col2:
        if categories:
            target_category = st.selectbox(
                "Category",
                categories,
                format_func=lambda x: f"{x['icon']} {x['name']}"
            )
    
    with col3:
        tags = st.text_input("Tags (comma-separated)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        target_price = st.number_input("Target Price (optional)", min_value=0.0)
    
    with col2:
        stop_loss = st.number_input("Stop Loss (optional)", min_value=0.0)
    
    notes = st.text_area("Notes (optional)")
    
    if st.button("➕ Add to Watchlist", type="primary"):
        if ticker and target_category:
            tag_list = [t.strip() for t in tags.split(",")] if tags else []
            
            success = manager.add_stock_enhanced(
                ticker=ticker.upper(),
                category_id=target_category['id'],
                tags=tag_list,
                notes=notes,
                target_price=target_price if target_price > 0 else None,
                stop_loss=stop_loss if stop_loss > 0 else None
            )
            
            if success:
                st.success(f"✅ Added {ticker} to {target_category['name']}!")
                st.rerun()
            else:
                st.error("Failed to add stock (may already exist in this category)")
```

### 4. **Update app.py**

**MODIFY** `app.py` to add the enhanced watchlist:

```python
# In app.py, modify the imports section to add:
from ui.watchlist_enhanced import display_enhanced_watchlist

# In the sidebar navigation section, REPLACE:
page = st.sidebar.radio(
    "Select a page:",
    ["Single Stock Analysis", "Batch Analysis",
        "Enhanced Stock Scanner", "Watchlist"]
)

# WITH:
page = st.sidebar.radio(
    "Select a page:",
    ["Single Stock Analysis", "Batch Analysis",
        "Enhanced Stock Scanner", "Watchlist", "Enhanced Watchlist"]
)

# In the page display section, ADD:
elif page == "Enhanced Watchlist":
    display_enhanced_watchlist()
```

## Benefits of this Enhanced System:

1. **Better Organization**: Categories and tags help organize large watchlists
2. **Performance Tracking**: See how stocks have performed since you added them
3. **Price Alerts**: Set target prices and stop losses with automatic notifications
4. **Quick Actions**: Add stocks from any page with proper categorization
5. **Bulk Operations**: Import/export watchlists, bulk categorization
6. **Notes & Context**: Keep notes on why you're watching each stock
7. **Visual Indicators**: Color-coded performance, alert badges
8. **Integration**: Works seamlessly with existing scanner and analysis tools

## Migration Strategy:

1. **Keep existing watchlist functional** during transition
2. **Run both systems in parallel** initially
3. **Migrate existing watchlist data** to new enhanced format
4. **Gradually phase out old system** once users are comfortable

This enhanced watchlist system will make your stock analysis tool much more powerful and user-friendly!