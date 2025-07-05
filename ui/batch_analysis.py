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
    """Reorganized scanner selection interface with logical flow"""
    
    # Step 1: Stock Universe Selection
    st.subheader("📈 Select Stock Universe")
    stock_universe = st.selectbox("Choose stock universe:",
                                  options=[
                                      "All Watchlist Stocks",
                                      "Selected Watchlist", 
                                      "All Small Cap",
                                      "All Mid Cap",
                                      "All Large Cap"
                                  ],
                                  index=1,  # Default to "Selected Watchlist"
                                  key="scanner_universe",
                                  label_visibility="collapsed")

    # Step 2: Watchlist Selection (only show if "Selected Watchlist" is chosen)
    selected_watchlist = None
    if stock_universe == "Selected Watchlist":
        st.subheader("📋 Select Watchlist")
        
        # Get all watchlists
        if 'watchlist_manager' not in st.session_state:
            from services.watchlist_manager import SimpleWatchlistManager
            st.session_state.watchlist_manager = SimpleWatchlistManager()

        manager = st.session_state.watchlist_manager
        watchlists = manager.get_all_watchlists()

        if not watchlists:
            st.warning("No watchlists available")
            return False, stock_universe, False, False, None

        selected_watchlist = st.selectbox("Choose watchlist:",
                                          options=watchlists,
                                          format_func=lambda x: f"{x['name']} {'(Default)' if x.get('is_default', False) else ''}",
                                          key="batch_watchlist_select",
                                          label_visibility="collapsed")
        
        if selected_watchlist:
            stock_count = len(manager.get_watchlist_stocks(selected_watchlist['id']))
            st.info(f"Ready to scan {stock_count} stocks from '{selected_watchlist['name']}'")

    # Step 3: Scan Options
    st.subheader("⚙️ Scan Options")
    col1, col2 = st.columns(2)
    
    with col1:
        show_errors = st.checkbox("Show Errors", value=False, key="show_scanner_errors")
        
    with col2:
        auto_add_buys = st.checkbox("Auto-add BUYs", value=False, key="auto_add_buy_signals")

    # Step 4: Scan Button
    st.subheader("🚀 Execute Scan")
    if st.button("SCAN", type="primary", use_container_width=True):
        return True, stock_universe, show_errors, auto_add_buys, selected_watchlist

    return False, stock_universe, show_errors, auto_add_buys, selected_watchlist


def get_tickers_for_universe(stock_universe, selected_watchlist=None):
    """Get tickers based on selected universe"""
    try:
        if stock_universe == "All Watchlist Stocks":
            watchlist = get_watchlist()
            return [item['ticker'] for item in watchlist] if watchlist else []

        elif stock_universe == "Selected Watchlist":
            if selected_watchlist:
                if 'watchlist_manager' not in st.session_state:
                    from services.watchlist_manager import SimpleWatchlistManager
                    st.session_state.watchlist_manager = SimpleWatchlistManager()

                manager = st.session_state.watchlist_manager
                return manager.get_watchlist_stocks(selected_watchlist['id'])
            return []

        elif stock_universe == "All Small Cap":
            from utils.ticker_cleaner import load_and_clean_csv_tickers
            tickers = load_and_clean_csv_tickers('data/csv/updated_small.csv')
            st.info(f"Loaded {len(tickers)} small cap stocks from CSV")
            return tickers

        elif stock_universe == "All Mid Cap":
            from utils.ticker_cleaner import load_and_clean_csv_tickers
            tickers = load_and_clean_csv_tickers('data/csv/updated_mid.csv')
            st.info(f"Loaded {len(tickers)} mid cap stocks from CSV")
            return tickers

        elif stock_universe == "All Large Cap":
            from utils.ticker_cleaner import load_and_clean_csv_tickers
            tickers = load_and_clean_csv_tickers('data/csv/updated_large.csv')
            st.info(f"Loaded {len(tickers)} large cap stocks from CSV")
            return tickers

        elif stock_universe == "Manual Entry":
            ticker_input = st.text_input(
                "Enter ticker symbols (comma-separated):",
                key="manual_ticker_input")
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
        if result.get('error') and not st.session_state.get(
                'show_scanner_errors', False):
            continue

        # Standardize signal format
        signal = result.get('value_momentum_signal',
                            result.get('signal', 'HOLD'))
        if signal in ['KÖP', 'KÖPA']:
            signal = 'BUY'
        elif signal in ['SÄLJ', 'SÄLJA']:
            signal = 'SELL'
        elif signal in ['HÅLL', 'HÅLLA']:
            signal = 'HOLD'

        # Create clean row
        clean_data.append({
            'Rank':
            0,  # Will be set after sorting
            'Ticker':
            result.get('ticker', 'N/A'),
            'Name':
            result.get('name', result.get('ticker', 'N/A')),
            'Signal':
            signal,
            'Score':
            int(result.get('tech_score', 0)),
            'MA40':
            '✓' if result.get('above_ma40') else '✗',
            'RSI>50':
            '✓' if result.get('rsi_above_50') else '✗',
            'Profitable':
            '✓' if result.get('is_profitable') else '✗',
            'Source':
            result.get('data_source', 'api'),
            '_raw':
            result  # Keep raw data for actions
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
        filtered_df['_signal_priority'] = filtered_df['Signal'].map(
            signal_priority).fillna(4)
        filtered_df = filtered_df.sort_values(['_signal_priority', 'Score'],
                                              ascending=[True, False])
        filtered_df = filtered_df.drop('_signal_priority', axis=1)
    elif sort_by == "Ticker":
        filtered_df = filtered_df.sort_values('Ticker')
    elif sort_by == "P/E":
        # Sort by P/E, putting N/A at the end
        filtered_df['_pe_sort'] = filtered_df['P/E'].apply(
            lambda x: 999 if x == 'N/A' else float(x))
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
            target_wl = next(
                (w for w in watchlists if w['id'] == selected_watchlist_id),
                None)
        else:
            # Try to get the currently selected bulk add watchlist
            if 'bulk_add_watchlist_select' in st.session_state:
                bulk_selected = st.session_state.bulk_add_watchlist_select
                target_wl = bulk_selected if bulk_selected else next(
                    (w for w in watchlists if w['is_default']), None)
            else:
                target_wl = next((w for w in watchlists if w['is_default']),
                                 None)

        if target_wl:
            success = manager.add_stock_to_watchlist(target_wl['id'], ticker, name)
            if success:
                st.success(f"✅ Added {ticker} to '{target_wl['name']}'!")
            else:
                st.info(f"ℹ️ {ticker} already in '{target_wl['name']}'")
        else:
            st.error("No watchlist found")
    except Exception as e:
        st.error(f"Error adding {ticker}: {str(e)}")


def remove_single_from_watchlist(ticker, watchlist_id=None):
    """Remove single stock from specified or all watchlists"""
    try:
        if 'watchlist_manager' not in st.session_state:
            from services.watchlist_manager import SimpleWatchlistManager
            st.session_state.watchlist_manager = SimpleWatchlistManager()

        manager = st.session_state.watchlist_manager
        watchlists = manager.get_all_watchlists()
        
        removed_from = []
        
        if watchlist_id:
            # Remove from specific watchlist
            target_wl = next((w for w in watchlists if w['id'] == watchlist_id), None)
            if target_wl:
                success = manager.remove_stock_from_watchlist(target_wl['id'], ticker)
                if success:
                    removed_from.append(target_wl['name'])
        else:
            # Remove from all watchlists that contain this ticker
            for watchlist in watchlists:
                stocks = manager.get_watchlist_stocks(watchlist['id'])
                for stock in stocks:
                    stock_ticker = stock.get('ticker', '') if isinstance(stock, dict) else str(stock)
                    if stock_ticker == ticker:
                        success = manager.remove_stock_from_watchlist(watchlist['id'], ticker)
                        if success:
                            removed_from.append(watchlist['name'])
                        break
        
        if removed_from:
            if len(removed_from) == 1:
                st.success(f"✅ Removed {ticker} from '{removed_from[0]}'!")
            else:
                st.success(f"✅ Removed {ticker} from {len(removed_from)} watchlists: {', '.join(removed_from)}")
            st.rerun()  # Refresh the interface
        else:
            st.info(f"ℹ️ {ticker} not found in any watchlist")
            
    except Exception as e:
        st.error(f"Error removing {ticker}: {str(e)}")


def check_stock_in_watchlists(ticker):
    """Check which watchlists contain this ticker"""
    try:
        if 'watchlist_manager' not in st.session_state:
            return []
            
        manager = st.session_state.watchlist_manager
        watchlists = manager.get_all_watchlists()
        containing_watchlists = []
        
        for watchlist in watchlists:
            stocks = manager.get_watchlist_stocks(watchlist['id'])
            for stock in stocks:
                stock_ticker = stock.get('ticker', '') if isinstance(stock, dict) else str(stock)
                if stock_ticker == ticker:
                    containing_watchlists.append(watchlist)
                    break
                
        return containing_watchlists
    except Exception as e:
        logger.error(f"Error checking watchlists for {ticker}: {e}")
        return []


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
            target_wl = next(
                (w for w in watchlists if w['id'] == selected_watchlist_id),
                None)
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
                success = manager.add_stock_to_watchlist(
                    target_wl['id'], ticker)
                if success:
                    added_count += 1
                else:
                    failed_count += 1

        if added_count > 0:
            st.success(
                f"✅ Added {added_count} BUY signals to '{target_wl['name']}'!")
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
            return manager.add_stock_to_watchlist(default_wl['id'], ticker, name)
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

    # Compact header with essential actions
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        st.markdown(f"**📊 Results ({len(filtered_df)} stocks)**")
        
    buy_signals = filtered_df[filtered_df['Signal'] == 'BUY']
    
    if not buy_signals.empty:
        # Get watchlists for selection
        if 'watchlist_manager' not in st.session_state:
            from services.watchlist_manager import SimpleWatchlistManager
            st.session_state.watchlist_manager = SimpleWatchlistManager()
        
        manager = st.session_state.watchlist_manager
        watchlists = manager.get_all_watchlists()
        
        if watchlists:
            with col2:
                if st.button(f"➕ Add {len(buy_signals)} BUYs", 
                           type="primary", use_container_width=True):
                    # Use default watchlist for quick add
                    default_watchlist = next((w for w in watchlists if w.get('is_default')), watchlists[0])
                    bulk_add_to_watchlist(buy_signals, default_watchlist['id'])
    
    with col3:
        csv_data = filtered_df.to_csv(index=False)
        st.download_button("📥 CSV", csv_data, "results.csv", "text/csv", use_container_width=True)
    
    with col4:
        if st.button("🔄 Refresh", use_container_width=True):
            trigger_new_scan()

    # Mobile-responsive table headers with minimal spacing - added single analysis column
    col_single, col_add, col_del, col_gpt, col_ticker, col_signal, col_score, col_indicators = st.columns([0.7, 0.7, 0.7, 0.7, 1.3, 1, 1, 1.2])

    with col_single:
        st.markdown("**Single**")
    with col_add:
        st.markdown("**Add**")
    with col_del:
        st.markdown("**Del**")
    with col_gpt:
        st.markdown("**GPT**")
    with col_ticker:
        st.markdown("**Stock**")
    with col_signal:
        st.markdown("**Signal**")
    with col_score:
        st.markdown("**Score**")
    with col_indicators:
        st.markdown("**Tech**", help="""Technical Health Matrix - Three Key Indicators:

🟢 MA40: Price Above 40-Day Moving Average
   • Primary trend confirmation signal
   • Green = Bullish trend, Red = Bearish trend

🟡 RSI>50: Relative Strength Index Above 50
   • Momentum and buying pressure indicator  
   • Green = Strong momentum, Red = Weak momentum

🔴 Profitable: Company Fundamental Health
   • Based on earnings and profit margins
   • Green = Profitable company, Red = Unprofitable

Reading: 🟢🟢🟢 = Strong Buy | 🔴🔴🔴 = Strong Sell | Mixed = Caution
Combined reading provides instant technical health assessment.""")

    st.markdown('<div style="margin: 0.25rem 0; border-bottom: 1px solid #333;"></div>', unsafe_allow_html=True)

    # Mobile-optimized CSS with full width
    st.markdown("""
    <style>
    /* Force full width on mobile */
    .main .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }
    
    /* Make columns use full width */
    div[data-testid="stHorizontalBlock"] {
        width: 100% !important;
        gap: 0.25rem !important;
    }
    
    div[data-testid="stHorizontalBlock"] > div {
        padding-top: 0.1rem !important;
        padding-bottom: 0.1rem !important;
        padding-left: 0.1rem !important;
        padding-right: 0.1rem !important;
        flex: 1 !important;
    }
    
    /* Reduce header spacing */
    .batch-header {
        margin-bottom: 0.25rem !important;
        padding-bottom: 0.1rem !important;
    }
    
    .batch-table-row {
        padding: 4px 0px !important;
        margin: 2px 0px !important;
        min-height: 32px !important;
        border-bottom: 1px solid #e6e6e6;
        width: 100% !important;
    }
    
    .stButton > button {
        height: 32px !important;
        padding: 4px 8px !important;
        min-height: 32px !important;
        font-size: 14px !important;
        touch-action: manipulation !important;
        width: 100% !important;
    }
    
    .batch-text {
        font-size: 14px !important;
        line-height: 1.4 !important;
        margin: 0 !important;
        word-wrap: break-word !important;
    }
    
    .batch-link {
        font-size: 14px !important;
        text-decoration: none !important;
        display: inline-block !important;
        padding: 4px !important;
        min-height: 32px !important;
        touch-action: manipulation !important;
        word-wrap: break-word !important;
    }
    
    .batch-indicator {
        font-size: 16px !important;
        line-height: 1.0 !important;
        text-align: center !important;
        letter-spacing: -1px !important;
    }
    
    /* Mobile responsive adjustments */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }
        
        .batch-text {
            font-size: 12px !important;
        }
        
        .batch-link {
            font-size: 12px !important;
            padding: 2px !important;
        }
        
        .stButton > button {
            font-size: 12px !important;
            padding: 4px 6px !important;
        }
        
        .batch-indicator {
            font-size: 12px !important;
            line-height: 0.8 !important;
            letter-spacing: -2px !important;
        }
        
        div[data-testid="stHorizontalBlock"] {
            gap: 0.1rem !important;
        }
        
        div[data-testid="stHorizontalBlock"] > div {
            padding-left: 0.05rem !important;
            padding-right: 0.05rem !important;
        }
    }
    </style>
    """,
                unsafe_allow_html=True)

    # Ultra-compact table with individual buttons
    for idx, row in filtered_df.iterrows():
        # Mobile-responsive row layout with single analysis column
        col_single, col_add, col_del, col_gpt, col_ticker, col_signal, col_score, col_indicators = st.columns([0.7, 0.7, 0.7, 0.7, 1.3, 1, 1, 1.2])

        # Extract ticker information
        ticker = row.get('Ticker', 'N/A')
        name = row.get('Name', ticker)
        
        # Check if stock is in any watchlist
        containing_watchlists = check_stock_in_watchlists(ticker)
        
        # Single analysis button
        with col_single:
            if ticker != 'N/A':
                if st.button("📊", key=f"single_{ticker}_{idx}", help=f"Single analysis for {ticker}"):
                    # Set the ticker for single analysis and trigger automatic navigation
                    st.session_state.analyze_ticker = ticker
                    st.session_state.auto_analyze = True
                    st.session_state.selected_tab = "Single Stock"
                    st.success(f"📊 Analyzing {ticker}...")
                    st.rerun()
            else:
                st.markdown('<div class="batch-text">—</div>', unsafe_allow_html=True)
        
        # Add button with watchlist selection
        with col_add:
            # Create a unique key for the selectbox
            selectbox_key = f"watchlist_select_{ticker}_{idx}"
            
            # Get available watchlists
            if 'watchlist_manager' not in st.session_state:
                from services.watchlist_manager import SimpleWatchlistManager
                st.session_state.watchlist_manager = SimpleWatchlistManager()
            
            manager = st.session_state.watchlist_manager
            watchlists = manager.get_all_watchlists()
            
            if watchlists:
                # Create a popover for watchlist selection
                with st.popover("➕", help=f"Add {ticker} to watchlist"):
                    st.markdown(f"**Add {ticker}**")
                    
                    # Watchlist selection
                    watchlist_options = {f"{wl['name']}": wl['id'] for wl in watchlists}
                    selected_watchlist_name = st.selectbox(
                        "Choose watchlist:",
                        options=list(watchlist_options.keys()),
                        key=selectbox_key,
                        label_visibility="collapsed"
                    )
                    
                    # Add button inside popover
                    if st.button("Add to Watchlist", key=f"add_confirm_{ticker}_{idx}", use_container_width=True):
                        selected_watchlist_id = watchlist_options[selected_watchlist_name]
                        add_single_to_watchlist(ticker, name, selected_watchlist_id)
                        st.rerun()
            else:
                # Fallback if no watchlists available
                if st.button("➕", key=f"add_fallback_{ticker}_{idx}", help=f"Add {ticker}"):
                    add_single_to_watchlist(ticker, name)

        # Delete button - only show if stock is in watchlists
        with col_del:
            if containing_watchlists:
                if st.button("🗑️", key=f"del_{ticker}_{idx}", help=f"Remove {ticker} from watchlists"):
                    remove_single_from_watchlist(ticker)
            else:
                st.markdown('<div class="batch-text">—</div>', unsafe_allow_html=True)

        # GPT link - compact for mobile
        with col_gpt:
            if ticker != 'N/A':
                link, clean_ticker = generate_chatgpt_link(ticker)
                st.markdown(
                    f'<a href="{link}" target="_blank" class="batch-link">🤖</a>',
                    unsafe_allow_html=True)
            else:
                st.markdown('<div class="batch-text">—</div>', unsafe_allow_html=True)

        # Stock info (ticker + company name combined for mobile)
        with col_ticker:
            if ticker != 'N/A':
                clean_ticker = ticker.replace('[', '').replace(']', '').split('(')[0].strip()
                yahoo_url = f"https://finance.yahoo.com/quote/{clean_ticker}"
                # Compact display: ticker on top, company name smaller below
                if name != 'N/A' and name != ticker:
                    display_name = name[:20] + "..." if len(name) > 20 else name
                    st.markdown(
                        f'<a href="{yahoo_url}" target="_blank" class="batch-link"><strong>{clean_ticker}</strong><br><small>{display_name}</small></a>',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        f'<a href="{yahoo_url}" target="_blank" class="batch-link"><strong>{clean_ticker}</strong></a>',
                        unsafe_allow_html=True)
            else:
                st.markdown('<div class="batch-text"><strong>N/A</strong></div>', unsafe_allow_html=True)

        # Signal - consistent font with color
        with col_signal:
            signal = row.get('Signal', 'HOLD')
            if signal == 'BUY':
                st.markdown(
                    '<div class="batch-text">🟢 <strong>BUY</strong></div>',
                    unsafe_allow_html=True)
            elif signal == 'SELL':
                st.markdown(
                    '<div class="batch-text">🔴 <strong>SELL</strong></div>',
                    unsafe_allow_html=True)
            else:
                st.markdown(
                    '<div class="batch-text">🟡 <strong>HOLD</strong></div>',
                    unsafe_allow_html=True)

        # Score - consistent font with color
        with col_score:
            score = int(row.get('Score', 0))
            if score >= 70:
                st.markdown(
                    f'<div class="batch-text"><strong>{score}</strong> 🟢</div>',
                    unsafe_allow_html=True)
            elif score >= 50:
                st.markdown(
                    f'<div class="batch-text"><strong>{score}</strong> 🟡</div>',
                    unsafe_allow_html=True)
            else:
                st.markdown(
                    f'<div class="batch-text"><strong>{score}</strong> 🔴</div>',
                    unsafe_allow_html=True)

        # Technical indicators - consistent font with tooltips
        with col_indicators:
            ma40 = '🟢' if row.get('MA40') == '✓' else '🔴'
            rsi = '🟢' if row.get('RSI>50') == '✓' else '🔴'
            profit = '🟢' if row.get('Profitable') == '✓' else '🔴'
            
            # Create tooltip text explaining each indicator
            ma40_status = "Above MA40" if row.get('MA40') == '✓' else "Below MA40"
            rsi_status = "RSI > 50" if row.get('RSI>50') == '✓' else "RSI ≤ 50"
            profit_status = "Profitable" if row.get('Profitable') == '✓' else "Not Profitable"
            
            tooltip_text = f"{ma40_status} | {rsi_status} | {profit_status}"
            
            st.markdown(
                f'<div class="batch-indicator" title="{tooltip_text}">{ma40}{rsi}{profit}</div>',
                unsafe_allow_html=True)

    # Mobile-friendly tips
    if not buy_signals.empty:
        st.info(
            "💡 **Tips**: Tap ticker symbols for Yahoo Finance • Select watchlist above and use 'Add All BUYs' or individual ➕ buttons"
        )
    else:
        st.info(
            "💡 **Tips**: Tap ticker symbols for Yahoo Finance • No BUY signals found - try adjusting filters"
        )


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

    # Mobile-optimized filters in expander
    with st.expander("🔧 Filters & Settings", expanded=False):
        # Mobile-friendly 2x2 layout
        col1, col2 = st.columns(2)
        
        with col1:
            signal_filter = st.multiselect("Show Signals", 
                                         ["BUY", "HOLD", "SELL"],
                                         default=["BUY", "HOLD", "SELL"],
                                         help="Filter by trading signals")
            
            min_score = st.number_input("Min Score", 
                                      min_value=0, max_value=100, value=0,
                                      help="Minimum technical score")
        
        with col2:
            max_results = st.number_input("Show Results", 
                                        min_value=5, max_value=200, value=50,
                                        help="Maximum results to display")
            
            sort_by = st.selectbox("Sort By", 
                                 ["Score", "Signal", "Ticker"],
                                 help="Sort results by field")

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
        results = scanner(target_tickers=tickers,
                          fetch_missing=True,
                          max_api_workers=8,
                          progress_callback=progress_callback)
        end_time = time.time()

        # Store scan stats
        success_count = len([r for r in results if not r.get('error')])
        st.session_state.last_scan_stats = {
            'total': len(results),
            'duration': end_time - start_time,
            'success_rate':
            (success_count / len(results)) * 100 if results else 0,
            'sources': 'Database + APIs'
        }

        return results

    except Exception as e:
        logger.error(f"Scanner error: {e}")
        return []


def generate_chatgpt_link(ticker):
    """Generate ChatGPT link with ticker-specific question"""
    import urllib.parse

    # Clean the ticker
    clean_ticker = ticker.replace('[', '').replace(']',
                                                   '').split('(')[0].strip()

    # Create the question
    question = f"""
Tell me about the company behind the Yahoo Finance ticker {clean_ticker}. 
Give me a short summary about the company and its future potentials and risks. 
If the company is dealing in conflict materials, Arctic oil or gas exploration, or weapons, let me know.
"""

    # Generate the link
    link = "https://chatgpt.com/?q=" + urllib.parse.quote(question)
    return link, clean_ticker


def display_batch_analysis():
    """Main batch analysis interface - SIMPLIFIED"""
    st.header("🚀 Stock Scanner")

    # Show scanner status
    show_scanner_status()

    # Reorganized scanner selection
    should_scan, stock_universe, show_errors, auto_add_buys, selected_watchlist = render_scanner_selection()

    # Get tickers for selected universe
    tickers = get_tickers_for_universe(stock_universe, selected_watchlist)

    if not tickers:
        st.warning(f"No tickers found for {stock_universe}")
    elif tickers and not should_scan:
        st.info(f"Ready to scan {len(tickers)} stocks from {stock_universe}")

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
            buy_results = [
                r for r in results if r.get('value_momentum_signal') == 'BUY'
            ]
            if buy_results:
                buy_df = create_clean_results_dataframe(buy_results)
                buy_signals = buy_df[buy_df['Signal'] == 'BUY']
                if not buy_signals.empty:
                    # Use default watchlist for auto-add
                    bulk_add_to_watchlist(buy_signals)

        # Single merged notification
        st.success(f"Scanned {len(tickers)} stocks from {stock_universe} - Found {len(results)} results")

    # Display results if available
    if 'batch_analysis_results' in st.session_state:
        results = st.session_state.batch_analysis_results
        if results:
            render_unified_results_table(results)
        else:
            st.info("No results from last scan")
