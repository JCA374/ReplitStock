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