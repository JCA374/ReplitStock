# ui/batch_analysis.py - SIMPLIFIED BATCH ANALYSIS

# Standard library imports
import logging
import time
import pandas as pd
from datetime import datetime

# Third-party imports
import streamlit as st

# Local application imports
from data.db_integration import get_watchlist
from utils.ticker_mapping import normalize_ticker

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_scanner_engine():
    """Get the high-performance scanner engine"""
    from analysis.bulk_scanner import optimized_bulk_scan
    return optimized_bulk_scan


def render_scanner_selection():
    """Simplified scanner selection interface"""
    # st.subheader("🚀 High-Performance Stock Scanner")
    
    # Single row of essential controls
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    
    with col1:
        stock_universe = st.selectbox(
            "📈 Select Stock Universe",
            options=[
                "All Watchlist Stocks",
                "Selected Watchlist", 
                "All Small Cap (updated_small.csv)",
                "All Mid Cap (updated_mid.csv)", 
                "All Large Cap (updated_large.csv)",
                "Manual Entry"
            ],
            key="scanner_universe"
        )
    
    with col2:
        show_errors = st.checkbox("Show Errors", value=False, key="show_scanner_errors")
    
    with col3:
        auto_add_buys = st.checkbox("Auto-add BUYs", value=False, key="auto_add_buy_signals")
    
    with col4:
        if st.button("🚀 SCAN", type="primary", use_container_width=True):
            return True, stock_universe, show_errors, auto_add_buys
    
    return False, stock_universe, show_errors, auto_add_buys


def get_tickers_for_universe(stock_universe):
    """Get tickers based on selected universe"""
    try:
        if stock_universe == "All Watchlist Stocks":
            watchlist = get_watchlist()
            return [item['ticker'] for item in watchlist] if watchlist else []
        
        elif stock_universe == "Selected Watchlist":
            # Get all watchlists
            if 'watchlist_manager' not in st.session_state:
                from services.watchlist_manager import SimpleWatchlistManager
                st.session_state.watchlist_manager = SimpleWatchlistManager()
            
            manager = st.session_state.watchlist_manager
            watchlists = manager.get_all_watchlists()
            
            if not watchlists:
                st.warning("No watchlists available")
                return []
            
            selected_wl = st.selectbox(
                "Select Watchlist:",
                options=watchlists,
                format_func=lambda x: x['name'],
                key="batch_watchlist_select"
            )
            
            if selected_wl:
                return manager.get_watchlist_stocks(selected_wl['id'])
            return []
        
        elif stock_universe == "All Small Cap (updated_small.csv)":
            small_cap_df = pd.read_csv('data/csv/updated_small.csv')
            return [t for t in small_cap_df['YahooTicker'].tolist() if pd.notna(t)]
        
        elif stock_universe == "All Mid Cap (updated_mid.csv)":
            mid_cap_df = pd.read_csv('data/csv/updated_mid.csv')
            tickers = []
            for ticker in mid_cap_df['YahooTicker'].tolist():
                if pd.notna(ticker):
                    # Fix tickers missing .ST suffix
                    if ticker.endswith('ST') and not ticker.endswith('.ST'):
                        ticker = ticker[:-2] + '.ST'
                    tickers.append(ticker)
            return tickers
        
        elif stock_universe == "All Large Cap (updated_large.csv)":
            large_cap_df = pd.read_csv('data/csv/updated_large.csv')
            return [t for t in large_cap_df['YahooTicker'].tolist() if pd.notna(t)]
        
        elif stock_universe == "Manual Entry":
            ticker_input = st.text_input(
                "Enter ticker symbols (comma-separated):",
                key="manual_ticker_input"
            )
            if ticker_input:
                raw_tickers = [t.strip() for t in ticker_input.split(",")]
                return [normalize_ticker(t) for t in raw_tickers if t]
            return []
    
    except Exception as e:
        st.error(f"Error loading tickers: {str(e)}")
        return []


def format_pe_ratio(pe_ratio):
    """Format P/E ratio for display"""
    if pe_ratio is None or pd.isna(pe_ratio):
        return "N/A"
    try:
        pe_float = float(pe_ratio)
        if pe_float < 0:
            return "N/A"
        return f"{pe_float:.1f}"
    except (ValueError, TypeError):
        return "N/A"


def create_clean_results_dataframe(results):
    """Create a clean, consistent DataFrame from scanner results"""
    clean_data = []
    
    for result in results:
        # Skip errors unless specifically requested
        if result.get('error') and not st.session_state.get('show_scanner_errors', False):
            continue
            
        # Standardize signal format
        signal = result.get('value_momentum_signal', result.get('signal', 'HOLD'))
        if signal in ['KÖP', 'KÖPA']:
            signal = 'BUY'
        elif signal in ['SÄLJ', 'SÄLJA']: 
            signal = 'SELL'
        elif signal in ['HÅLL', 'HÅLLA']:
            signal = 'HOLD'
            
        # Create clean row
        clean_data.append({
            'Rank': 0,  # Will be set after sorting
            'Ticker': result.get('ticker', 'N/A'),
            'Name': result.get('name', result.get('ticker', 'N/A')),
            'Signal': signal,
            'Score': int(result.get('tech_score', 0)),
            'Price': f"{result.get('last_price', result.get('price', 0)):.2f}",
            'P/E': format_pe_ratio(result.get('pe_ratio')),
            'MA40': '✓' if result.get('above_ma40') else '✗',
            'RSI>50': '✓' if result.get('rsi_above_50') else '✗', 
            'Profitable': '✓' if result.get('is_profitable') else '✗',
            'Source': result.get('data_source', 'api'),
            '_raw': result  # Keep raw data for actions
        })
    
    return pd.DataFrame(clean_data)


def apply_filters_and_sort(df, signal_filter, min_score, sort_by):
    """Apply filters and sorting to results DataFrame"""
    if df.empty:
        return df
    
    filtered_df = df.copy()
    
    # Apply signal filter
    if signal_filter:
        filtered_df = filtered_df[filtered_df['Signal'].isin(signal_filter)]
    
    # Apply minimum score filter
    filtered_df = filtered_df[filtered_df['Score'] >= min_score]
    
    # Apply sorting
    if sort_by == "Score":
        filtered_df = filtered_df.sort_values('Score', ascending=False)
    elif sort_by == "Signal":
        signal_priority = {"BUY": 1, "HOLD": 2, "SELL": 3}
        filtered_df['_signal_priority'] = filtered_df['Signal'].map(signal_priority).fillna(4)
        filtered_df = filtered_df.sort_values(['_signal_priority', 'Score'], ascending=[True, False])
        filtered_df = filtered_df.drop('_signal_priority', axis=1)
    elif sort_by == "Ticker":
        filtered_df = filtered_df.sort_values('Ticker')
    elif sort_by == "P/E":
        # Sort by P/E, putting N/A at the end
        filtered_df['_pe_sort'] = filtered_df['P/E'].apply(lambda x: 999 if x == 'N/A' else float(x))
        filtered_df = filtered_df.sort_values('_pe_sort')
        filtered_df = filtered_df.drop('_pe_sort', axis=1)
    
    # Update rank after sorting
    filtered_df['Rank'] = range(1, len(filtered_df) + 1)
    
    return filtered_df


def add_single_to_watchlist(ticker, name, selected_watchlist_id=None):
    """Add single stock to specified or default watchlist"""
    try:
        if 'watchlist_manager' not in st.session_state:
            from services.watchlist_manager import SimpleWatchlistManager
            st.session_state.watchlist_manager = SimpleWatchlistManager()
        
        manager = st.session_state.watchlist_manager
        watchlists = manager.get_all_watchlists()
        
        # Use selected watchlist or find default
        if selected_watchlist_id:
            target_wl = next((w for w in watchlists if w['id'] == selected_watchlist_id), None)
        else:
            # Try to get the currently selected bulk add watchlist
            if 'bulk_add_watchlist_select' in st.session_state:
                bulk_selected = st.session_state.bulk_add_watchlist_select
                target_wl = bulk_selected if bulk_selected else next((w for w in watchlists if w['is_default']), None)
            else:
                target_wl = next((w for w in watchlists if w['is_default']), None)
        
        if target_wl:
            success = manager.add_stock_to_watchlist(target_wl['id'], ticker)
            if success:
                st.success(f"✅ Added {ticker} to '{target_wl['name']}'!")
            else:
                st.info(f"ℹ️ {ticker} already in '{target_wl['name']}'")
        else:
            st.error("No watchlist found")
    except Exception as e:
        st.error(f"Error adding {ticker}: {str(e)}")


def bulk_add_to_watchlist(buy_signals_df, selected_watchlist_id=None):
    """Add all BUY signals to a specified watchlist"""
    try:
        if 'watchlist_manager' not in st.session_state:
            from services.watchlist_manager import SimpleWatchlistManager
            st.session_state.watchlist_manager = SimpleWatchlistManager()
        
        manager = st.session_state.watchlist_manager
        watchlists = manager.get_all_watchlists()
        
        # Use selected watchlist or find default
        if selected_watchlist_id:
            target_wl = next((w for w in watchlists if w['id'] == selected_watchlist_id), None)
        else:
            target_wl = next((w for w in watchlists if w['is_default']), None)
        
        if not target_wl:
            st.error("No watchlist found")
            return
        
        added_count = 0
        failed_count = 0
        
        for _, row in buy_signals_df.iterrows():
            ticker = row['Ticker']
            if ticker and ticker != 'N/A':
                success = manager.add_stock_to_watchlist(target_wl['id'], ticker)
                if success:
                    added_count += 1
                else:
                    failed_count += 1
        
        if added_count > 0:
            st.success(f"✅ Added {added_count} BUY signals to '{target_wl['name']}'!")
        if failed_count > 0:
            st.info(f"ℹ️ {failed_count} stocks already in watchlist")
            
    except Exception as e:
        st.error(f"Error in bulk add: {str(e)}")


def trigger_new_scan():
    """Trigger a new scan by clearing results"""
    if 'batch_analysis_results' in st.session_state:
        del st.session_state.batch_analysis_results
    if 'last_scan_stats' in st.session_state:
        del st.session_state.last_scan_stats
    st.rerun()


def add_stock_to_watchlist_with_feedback(ticker, name):
    """Add stock to default watchlist with proper feedback"""
    try:
        if not ticker:
            return False

        if 'watchlist_manager' not in st.session_state:
            from services.watchlist_manager import SimpleWatchlistManager
            st.session_state.watchlist_manager = SimpleWatchlistManager()
        
        manager = st.session_state.watchlist_manager
        watchlists = manager.get_all_watchlists()
        
        # Find default watchlist
        default_wl = next((w for w in watchlists if w['is_default']), None)
        
        if default_wl:
            return manager.add_stock_to_watchlist(default_wl['id'], ticker)
        return False

    except Exception as e:
        st.error(f"❌ Failed to add {ticker}: {str(e)}")
        return False


def add_selected_to_watchlist(selected_stocks):
    """Add selected stocks to default watchlist"""
    added_count = 0
    for _, stock in selected_stocks.iterrows():
        ticker = stock.get('Ticker', '')
        name = stock.get('Name', ticker)
        
        # Clean ticker if it has markdown link formatting
        if '[' in str(ticker) and ']' in str(ticker):
            ticker = str(ticker).split('[')[1].split(']')[0]
        
        if ticker and add_stock_to_watchlist_with_feedback(ticker, name):
            added_count += 1
    
    if added_count > 0:
        st.success(f"✅ Added {added_count} stocks to watchlist!")


def render_compact_results_table(filtered_df):
    """Render beautiful, compact results table with individual add buttons"""
    if filtered_df.empty:
        st.info("📊 No results to display")
        return
    
    # Header with stats
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"📊 Scan Results ({len(filtered_df)} stocks)")
    with col2:
        buy_count = len(filtered_df[filtered_df['Signal'] == 'BUY'])
        if buy_count > 0:
            st.metric("🟢 BUY Signals", buy_count)
    
    # Bulk actions row with watchlist selector
    buy_signals = filtered_df[filtered_df['Signal'] == 'BUY']
    
    if not buy_signals.empty:
        # Get watchlists for selection
        if 'watchlist_manager' not in st.session_state:
            from services.watchlist_manager import SimpleWatchlistManager
            st.session_state.watchlist_manager = SimpleWatchlistManager()
        
        manager = st.session_state.watchlist_manager
        watchlists = manager.get_all_watchlists()
        
        if watchlists:
            # Watchlist selection and bulk add
            col1, col2, col3, col4, col5 = st.columns([2, 1.2, 0.8, 0.8, 0.8])
            
            with col1:
                selected_watchlist = st.selectbox(
                    "Select watchlist for bulk add:",
                    options=watchlists,
                    format_func=lambda x: f"📋 {x['name']} {'(default)' if x.get('is_default') else ''}",
                    key="bulk_add_watchlist_select"
                )
            
            with col2:
                if st.button(f"➕ Add All {len(buy_signals)} BUYs", type="primary", use_container_width=True):
                    bulk_add_to_watchlist(buy_signals, selected_watchlist['id'] if selected_watchlist else None)
            
            with col3:
                # Quick create new watchlist
                if st.button("📋 New", use_container_width=True, help="Create new watchlist"):
                    new_name = f"Scan Results {datetime.now().strftime('%m/%d')}"
                    success = manager.create_watchlist(new_name, f"Created from scan on {datetime.now().strftime('%Y-%m-%d')}")
                    if success:
                        st.success(f"✅ Created '{new_name}'")
                        st.rerun()
                    else:
                        st.error("Failed to create watchlist")
            
            with col4:
                csv_data = filtered_df.to_csv(index=False)
                st.download_button("📥 CSV", csv_data, "scan_results.csv", "text/csv", use_container_width=True)
            
            with col5:
                if st.button("🔄 Refresh", use_container_width=True):
                    trigger_new_scan()
        else:
            # Fallback if no watchlists available
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button(f"➕ Add All {len(buy_signals)} BUY Signals", type="primary", use_container_width=True):
                    bulk_add_to_watchlist(buy_signals)
            
            with col2:
                csv_data = filtered_df.to_csv(index=False)
                st.download_button("📥 Download CSV", csv_data, "scan_results.csv", "text/csv", use_container_width=True)
            
            with col3:
                if st.button("🔄 Refresh Scan", use_container_width=True):
                    trigger_new_scan()
    else:
        # No buy signals, just show other actions
        col1, col2 = st.columns(2)
        
        with col1:
            csv_data = filtered_df.to_csv(index=False)
            st.download_button("📥 Download CSV", csv_data, "scan_results.csv", "text/csv", use_container_width=True)
        
        with col2:
            if st.button("🔄 Refresh Scan", use_container_width=True):
                trigger_new_scan()
    
    st.divider()
    
    # Table headers
    col_add, col_rank, col_ticker, col_company, col_signal, col_score, col_price, col_pe, col_indicators = st.columns([
        0.8, 0.6, 1.2, 2.5, 1, 1.2, 1, 0.8, 1.5
    ])
    
    with col_add:
        st.markdown("**Add**")
    with col_rank:
        st.markdown("**#**")
    with col_ticker:
        st.markdown("**Ticker**")
    with col_company:
        st.markdown("**Company**")
    with col_signal:
        st.markdown("**Signal**")
    with col_score:
        st.markdown("**Score**")
    with col_price:
        st.markdown("**Price**")
    with col_pe:
        st.markdown("**P/E**")
    with col_indicators:
        st.markdown("**Indicators**")
    
    st.markdown("---")
    
    # Custom CSS for ultra-compact rows
    st.markdown("""
    <style>
    .compact-row {
        padding: 2px 0px !important;
        margin: 0px !important;
        min-height: 25px !important;
    }
    div[data-testid="stHorizontalBlock"] > div {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
    }
    .stButton > button {
        height: 25px !important;
        padding: 0px 6px !important;
        min-height: 25px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Ultra-compact table with individual buttons
    for idx, row in filtered_df.iterrows():
        # Create a single compact row using HTML-like approach
        col_add, col_rank, col_ticker, col_company, col_signal, col_score, col_price, col_pe, col_indicators = st.columns([
            0.8, 0.6, 1.2, 2.5, 1, 1.2, 1, 0.8, 1.5
        ])
        
        # Add button - ultra compact
        with col_add:
            ticker = row.get('Ticker', 'N/A')
            name = row.get('Name', ticker)
            if st.button("➕", key=f"add_{ticker}_{idx}", help=f"Add {ticker}"):
                add_single_to_watchlist(ticker, name)
        
        # Rank - small text
        with col_rank:
            st.markdown(f"<small>#{row.get('Rank', idx+1)}</small>", unsafe_allow_html=True)
        
        # Ticker with Yahoo Finance link - compact
        with col_ticker:
            if ticker != 'N/A':
                clean_ticker = ticker.replace('[', '').replace(']', '').split('(')[0].strip()
                yahoo_url = f"https://finance.yahoo.com/quote/{clean_ticker}"
                st.markdown(f"**[{clean_ticker}]({yahoo_url})**")
            else:
                st.markdown("**N/A**")
        
        # Company name - truncated
        with col_company:
            if name != 'N/A' and name != ticker:
                display_name = name[:30] + "..." if len(name) > 30 else name
                google_search = f"https://www.google.com/search?q={name.replace(' ', '+')}"
                st.markdown(f"[{display_name}]({google_search})")
            else:
                st.markdown(name if name != ticker else "—")
        
        # Signal - compact colored badge
        with col_signal:
            signal = row.get('Signal', 'HOLD')
            if signal == 'BUY':
                st.markdown("🟢 **BUY**")
            elif signal == 'SELL':
                st.markdown("🔴 **SELL**")
            else:
                st.markdown("🟡 **HOLD**")
        
        # Score - compact with mini progress
        with col_score:
            score = int(row.get('Score', 0))
            # Inline score with mini progress bar
            if score >= 70:
                st.markdown(f"**{score}** 🟢")
            elif score >= 50:
                st.markdown(f"**{score}** 🟡")
            else:
                st.markdown(f"**{score}** 🔴")
        
        # Price - compact
        with col_price:
            price = row.get('Price', 'N/A')
            if price != 'N/A':
                st.markdown(f"**${price}**")
            else:
                st.markdown("N/A")
        
        # P/E Ratio - compact
        with col_pe:
            pe = row.get('P/E', 'N/A')
            st.markdown(f"{pe}")
        
        # Technical indicators - ultra compact
        with col_indicators:
            ma40 = '🟢' if row.get('MA40') == '✓' else '🔴'
            rsi = '🟢' if row.get('RSI>50') == '✓' else '🔴'
            profit = '🟢' if row.get('Profitable') == '✓' else '🔴'
            st.markdown(f"<small>{ma40}{rsi}{profit}</small>", unsafe_allow_html=True)
    
    # Footer with selection info
    st.caption(f"💡 Tip: Click ticker symbols to view on Yahoo Finance • Company names link to Google search")
    
    # Enhanced info about watchlist functionality
    if not buy_signals.empty:
        st.info("💡 **Watchlist Add Options**: Select your target watchlist above, then use 'Add All BUYs' or individual ➕ buttons")
    else:
        st.info("💡 **No BUY signals found** - Try adjusting filters or running a new scan")


def render_unified_results_table(results):
    """Single unified results table with all features"""
    if not results:
        st.info("No results to display")
        return
    
    # Convert to clean DataFrame
    df = create_clean_results_dataframe(results)
    
    if df.empty:
        st.info("No valid results to display")
        return
    
    # Simple filters in one row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        signal_filter = st.multiselect("Signals", ["BUY", "HOLD", "SELL"], default=["BUY", "HOLD", "SELL"])
    
    with col2:
        min_score = st.slider("Min Score", 0, 100, 0)
    
    with col3:
        max_results = st.slider("Show Top", 10, 200, 50)
    
    with col4:
        sort_by = st.selectbox("Sort By", ["Score", "Signal", "Ticker", "P/E"])
    
    # Apply filters and sorting
    filtered_df = apply_filters_and_sort(df, signal_filter, min_score, sort_by)
    top_results = filtered_df.head(max_results)
    
    # Render the compact table
    render_compact_results_table(top_results)


def show_scanner_status():
    """Show which scanner is being used and performance stats"""
    # st.info("🚀 **Using Optimized Bulk Scanner** - Database-first with parallel processing")
    
    # Show quick stats if available
    if 'last_scan_stats' in st.session_state:
        stats = st.session_state.last_scan_stats
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Stocks Processed", stats.get('total', 0))
        with col2:
            st.metric("Processing Time", f"{stats.get('duration', 0):.1f}s")
        with col3:
            st.metric("Success Rate", f"{stats.get('success_rate', 0):.1f}%")
        with col4:
            st.metric("Data Sources", stats.get('sources', 'Multiple'))


def run_optimized_scan(tickers, progress_callback=None):
    """Run the optimized bulk scanner"""
    try:
        scanner = get_scanner_engine()
        
        start_time = time.time()
        results = scanner(
            target_tickers=tickers,
            fetch_missing=True,
            max_api_workers=8,
            progress_callback=progress_callback
        )
        end_time = time.time()
        
        # Store scan stats
        success_count = len([r for r in results if not r.get('error')])
        st.session_state.last_scan_stats = {
            'total': len(results),
            'duration': end_time - start_time,
            'success_rate': (success_count / len(results)) * 100 if results else 0,
            'sources': 'Database + APIs'
        }
        
        return results
        
    except Exception as e:
        logger.error(f"Scanner error: {e}")
        return []


def display_batch_analysis():
    """Main batch analysis interface - SIMPLIFIED"""
    st.header("🚀 Stock Scanner")
    
    # Show scanner status
    show_scanner_status()
    
    # Simplified scanner selection
    should_scan, stock_universe, show_errors, auto_add_buys = render_scanner_selection()
    
    # Get tickers for selected universe
    tickers = get_tickers_for_universe(stock_universe)
    
    if not tickers and stock_universe != "Manual Entry":
        st.warning(f"No tickers found for {stock_universe}")
    elif tickers:
        st.success(f"Ready to scan {len(tickers)} stocks from {stock_universe}")
    
    # Run scan if requested
    if should_scan and tickers:
        # Create progress indicators
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def update_progress(progress, text):
            progress_bar.progress(progress)
            status_text.text(text)
        
        # Run optimized analysis
        with st.spinner(f"Scanning {len(tickers)} stocks..."):
            results = run_optimized_scan(tickers, update_progress)
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
        # Store results
        st.session_state.batch_analysis_results = results
        
        # Auto-add BUY signals if requested
        if auto_add_buys and results:
            buy_results = [r for r in results if r.get('value_momentum_signal') == 'BUY']
            if buy_results:
                buy_df = create_clean_results_dataframe(buy_results)
                buy_signals = buy_df[buy_df['Signal'] == 'BUY']
                if not buy_signals.empty:
                    # Use default watchlist for auto-add
                    bulk_add_to_watchlist(buy_signals)
        
        st.success(f"✅ Scan complete! Found {len(results)} results")
    
    # Display results if available
    if 'batch_analysis_results' in st.session_state:
        results = st.session_state.batch_analysis_results
        if results:
            render_unified_results_table(results)
        else:
            st.info("No results from last scan")