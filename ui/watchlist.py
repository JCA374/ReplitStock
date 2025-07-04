import streamlit as st
import pandas as pd
import io
from datetime import datetime
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
    
    # Combined Watchlist Actions menu
    with st.expander("⚙️ Watchlist Actions", expanded=False):
        # Create New Watchlist section
        st.subheader("➕ Create New Watchlist")
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            new_name = st.text_input("Watchlist Name", key="new_watchlist_name", placeholder="Enter watchlist name...")
        
        with col2:
            new_desc = st.text_input("Description (optional)", key="new_watchlist_desc", placeholder="Brief description...")
        
        with col3:
            st.write("")  # Add spacing
            if st.button("Create", key="create_watchlist_btn", use_container_width=True):
                if new_name:
                    if manager.create_watchlist(new_name, new_desc):
                        st.success(f"Created '{new_name}'")
                        st.rerun()
                    else:
                        st.error("Watchlist name already exists")
                else:
                    st.warning("Please enter a name")
        
        st.divider()
        
        # Import/Export section
        st.subheader("📂 Import & Export")
        col1, col2 = st.columns(2)
        
        with col1:
            # Import functionality
            st.write("**Import Watchlist**")
            uploaded_file = st.file_uploader(
                "Choose a CSV file",
                type=['csv'],
                key="import_watchlist_file",
                help="Upload a CSV file with ticker symbols. Supported formats: single column with tickers, or multi-column with 'ticker' column."
            )
            
            if uploaded_file is not None:
                try:
                    # Read the uploaded CSV
                    df_import = pd.read_csv(uploaded_file)
                    
                    # Try to find ticker column
                    ticker_column = None
                    possible_columns = ['ticker', 'symbol', 'Ticker', 'Symbol', 'TICKER', 'SYMBOL']
                    
                    for col in possible_columns:
                        if col in df_import.columns:
                            ticker_column = col
                            break
                    
                    # If no ticker column found, assume first column contains tickers
                    if ticker_column is None and len(df_import.columns) > 0:
                        ticker_column = df_import.columns[0]
                    
                    if ticker_column is not None:
                        # Extract tickers
                        tickers = df_import[ticker_column].dropna().astype(str).tolist()
                        
                        # Clean and normalize tickers
                        cleaned_tickers = []
                        for ticker in tickers:
                            cleaned = normalize_ticker(ticker.strip().upper())
                            if cleaned and cleaned not in cleaned_tickers:
                                cleaned_tickers.append(cleaned)
                        
                        st.write(f"Found {len(cleaned_tickers)} unique tickers:")
                        st.write(", ".join(cleaned_tickers[:10]) + ("..." if len(cleaned_tickers) > 10 else ""))
                        
                        if st.button("Import These Tickers", key="confirm_import"):
                            # Get currently selected watchlist for import
                            if 'watchlist_selector' in st.session_state and st.session_state.watchlist_selector:
                                current_watchlist = st.session_state.watchlist_selector
                                watchlist_id = current_watchlist['id']
                                
                                success_count = 0
                                duplicate_count = 0
                                
                                for ticker in cleaned_tickers:
                                    if manager.add_stock_to_watchlist(watchlist_id, ticker):
                                        success_count += 1
                                    else:
                                        duplicate_count += 1
                                
                                if success_count > 0:
                                    st.success(f"✅ Successfully imported {success_count} tickers")
                                if duplicate_count > 0:
                                    st.info(f"ℹ️ Skipped {duplicate_count} duplicates")
                                
                                st.rerun()
                            else:
                                st.warning("Please select a watchlist first")
                    else:
                        st.error("Could not find ticker column in the CSV file")
                        
                except Exception as e:
                    st.error(f"Error reading CSV file: {str(e)}")
        
        with col2:
            # Export functionality
            st.write("**Export Watchlist**")
            if 'watchlist_selector' in st.session_state and st.session_state.watchlist_selector:
                selected_watchlist = st.session_state.watchlist_selector
                stock_details = manager.get_watchlist_details(selected_watchlist['id'])
                
                if stock_details:
                    # Create export DataFrame
                    export_df = pd.DataFrame(stock_details)
                    csv_data = export_df.to_csv(index=False)
                    
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv_data,
                        file_name=f"watchlist_{selected_watchlist['name']}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv",
                        key="export_watchlist_btn",
                        help="Download the current watchlist as a CSV file"
                    )
                    
                    # Show preview
                    st.write(f"Ready to export {len(stock_details)} stocks")
                else:
                    st.write("No stocks to export")
            else:
                st.write("Select a watchlist to export")
    
    st.divider()
    
    # Manage Existing Watchlists section
    st.subheader("📋 Manage Watchlists")
    
    # Main content area
    if not watchlists:
        st.info("No watchlists found. Create your first watchlist above!")
        return
    
    # Watchlist selector - symmetrical layout
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        # Add stock count to display
        def format_watchlist(x):
            if 'watchlist_manager' in st.session_state:
                count = st.session_state.watchlist_manager.get_watchlist_stock_count(x['id'])
                return f"{x['name']} ({count} stocks) {'(Default)' if x['is_default'] else ''}"
            return f"{x['name']} {'(Default)' if x['is_default'] else ''}"
        
        selected_watchlist = st.selectbox(
            "Select Watchlist",
            options=watchlists,
            format_func=format_watchlist,
            key="watchlist_selector"
        )
    
    with col2:
        if st.button("🔄 Refresh", key="refresh_watchlist", use_container_width=True):
            st.rerun()
    
    with col3:
        if selected_watchlist and not selected_watchlist['is_default']:
            if st.button("🗑️ Delete", key="delete_watchlist", use_container_width=True):
                if manager.delete_watchlist(selected_watchlist['id']):
                    st.success("Watchlist deleted")
                    st.rerun()
        else:
            st.write("")  # Empty space for symmetry
    
    if selected_watchlist:
        watchlist_id = selected_watchlist['id']
        
        st.divider()
        
        # Add stock section - matching layout
        st.subheader("➕ Add Stock")
        
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            ticker_input = st.text_input(
                "Enter ticker symbol",
                placeholder="e.g., AAPL, MSFT, VOLV-B.ST",
                key="add_ticker_input"
            )
        
        with col2:
            if st.button("Add to Watchlist", key="add_stock_btn", use_container_width=True):
                if ticker_input:
                    ticker = normalize_ticker(ticker_input.upper())
                    if manager.add_stock_to_watchlist(watchlist_id, ticker):
                        st.success(f"Added {ticker}")
                        st.rerun()
                    else:
                        st.warning(f"{ticker} already in this watchlist")
                else:
                    st.warning("Please enter a ticker")
        
        with col3:
            st.write("")  # Empty space for symmetry
        
        # Display stocks in watchlist
        st.subheader(f"📈 Stocks in '{selected_watchlist['name']}'")
        
        # Get stock details
        stock_details = manager.get_watchlist_details(watchlist_id)
        
        if stock_details:
            # Add remove buttons column
            for idx, stock in enumerate(stock_details):
                col1, col2, col3, col4 = st.columns([0.5, 1.5, 3, 2])
                
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
            
            # Action buttons
            st.divider()
            
            # Single centered button for analysis
            if st.button("📊 Analyze This Watchlist", type="primary", key="analyze_watchlist", use_container_width=True):
                # Store watchlist tickers in session state for batch analysis
                tickers = [s['ticker'] for s in stock_details]
                st.session_state['batch_analysis_tickers'] = tickers
                st.session_state['batch_analysis_source'] = 'watchlist'
                st.session_state['batch_analysis_watchlist_name'] = selected_watchlist['name']
                st.success(f"Ready to analyze {len(tickers)} stocks from '{selected_watchlist['name']}'. Please switch to the Batch Analysis tab to view results.")
                # Don't use st.rerun() here as it can cause issues with navigation
        else:
            st.info("This watchlist is empty. Add stocks using the form above.")