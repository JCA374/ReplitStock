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
        
        # Import/Export section at the top
        st.subheader("📂 Import/Export")
        
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
                        st.error("Could not find ticker column in the CSV file")
                        
                except Exception as e:
                    st.error(f"Error reading CSV file: {str(e)}")
        
        with col2:
            # Export functionality
            st.write("**Export Watchlist**")
            stock_details = manager.get_watchlist_details(watchlist_id)
            
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
        
        st.divider()
        
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
            
            # Single centered button for analysis
            if st.button("📊 Analyze This Watchlist", type="primary", key="analyze_watchlist", use_container_width=True):
                # Store watchlist tickers in session state for batch analysis
                tickers = [s['ticker'] for s in stock_details]
                st.session_state['batch_analysis_tickers'] = tickers
                st.session_state['selected_page'] = 'Batch Analysis'
                st.session_state['batch_analysis_mode'] = 'Selected Stocks'
                st.success(f"Ready to analyze {len(tickers)} stocks. Switch to Batch Analysis tab.")
                st.rerun()
        else:
            st.info("This watchlist is empty. Add stocks using the form above.")