# ui/batchscanner_dev.py - MOBILE-FRIENDLY BATCH SCANNER

import logging
import pandas as pd
import streamlit as st
from data.db_integration import get_watchlist
from utils.ticker_mapping import normalize_ticker

logger = logging.getLogger(__name__)


def get_scanner_engine():
    """Get the high-performance scanner engine"""
    from analysis.bulk_scanner import optimized_bulk_scan
    return optimized_bulk_scan


def run_scan(tickers, progress_callback=None):
    """Run optimized scan using bulk scanner"""
    try:
        scanner = get_scanner_engine()
        return scanner(
            target_tickers=tickers,
            fetch_missing=True,
            max_api_workers=3,
            progress_callback=progress_callback
        )
    except Exception as e:
        logger.error(f"Scan error: {e}")
        return []


def get_tickers_for_selection(selection):
    """Get tickers based on selection"""
    if selection == "Watchlist":
        watchlist = get_watchlist()
        return [item['ticker'] for item in watchlist] if watchlist else []
    elif selection == "Small Cap":
        try:
            df = pd.read_csv("data/csv/updated_small.csv")
            return df['ticker'].tolist()[:20]  # Limit for mobile
        except:
            return []
    elif selection == "Mid Cap":
        try:
            df = pd.read_csv("data/csv/updated_mid.csv")
            return df['ticker'].tolist()[:20]  # Limit for mobile
        except:
            return []
    return []


def create_results_dataframe(results):
    """Create clean results dataframe for mobile display"""
    clean_data = []
    
    for result in results:
        if result.get('error'):
            continue
            
        # Standardize signal
        signal = result.get('value_momentum_signal', 'HOLD')
        if signal in ['KÖP', 'KÖPA']:
            signal = 'BUY'
        elif signal in ['SÄLJ', 'SÄLJA']: 
            signal = 'SELL'
        elif signal in ['HÅLL', 'HÅLLA']:
            signal = 'HOLD'
            
        clean_data.append({
            'Ticker': result.get('ticker', 'N/A'),
            'Name': result.get('name', result.get('ticker', 'N/A'))[:25] + "..." if len(result.get('name', '')) > 25 else result.get('name', result.get('ticker', 'N/A')),
            'Signal': signal,
            'Score': int(result.get('tech_score', 0)),
            'MA40': '✓' if result.get('above_ma40') else '✗',
            'RSI': '✓' if result.get('rsi_above_50') else '✗',
            'Profit': '✓' if result.get('is_profitable') else '✗',
            '_raw': result
        })
    
    df = pd.DataFrame(clean_data)
    if not df.empty:
        df = df.sort_values('Score', ascending=False).reset_index(drop=True)
        df.index = df.index + 1
    return df


def render_mobile_results(df):
    """Render results optimized for mobile"""
    if df.empty:
        st.info("No results to display")
        return
    
    st.subheader(f"Results ({len(df)})")
    
    # Mobile-friendly cards instead of table
    for idx, row in df.iterrows():
        with st.container():
            # Create card-like layout
            col1, col2, col3 = st.columns([2, 1, 0.5])
            
            with col1:
                ticker = row['Ticker']
                name = row['Name']
                signal = row['Signal']
                
                # Signal color
                if signal == 'BUY':
                    signal_color = "🟢"
                elif signal == 'SELL':
                    signal_color = "🔴"
                else:
                    signal_color = "🟡"
                
                st.markdown(f"**{ticker}** {signal_color} {signal}")
                st.caption(name)
            
            with col2:
                score = row['Score']
                if score >= 70:
                    st.metric("Score", score, delta="High")
                elif score >= 50:
                    st.metric("Score", score, delta="Med")
                else:
                    st.metric("Score", score, delta="Low")
            
            with col3:
                # Technical indicators as icons
                ma40 = '🟢' if row['MA40'] == '✓' else '🔴'
                rsi = '🟢' if row['RSI'] == '✓' else '🔴'
                profit = '🟢' if row['Profit'] == '✓' else '🔴'
                st.markdown(f"{ma40}{rsi}{profit}")
                
                # Add to watchlist button
                if st.button("➕", key=f"add_{ticker}_{idx}", help="Add to watchlist"):
                    add_to_watchlist(ticker)
        
        st.divider()


def add_to_watchlist(ticker):
    """Add stock to default watchlist"""
    try:
        if 'watchlist_manager' not in st.session_state:
            from services.watchlist_manager import SimpleWatchlistManager
            st.session_state.watchlist_manager = SimpleWatchlistManager()
        
        manager = st.session_state.watchlist_manager
        watchlists = manager.get_all_watchlists()
        default_wl = next((w for w in watchlists if w['is_default']), None)
        
        if default_wl:
            success = manager.add_stock_to_watchlist(default_wl['id'], ticker)
            if success:
                st.success(f"Added {ticker} to watchlist!")
            else:
                st.info(f"{ticker} already in watchlist")
        else:
            st.error("No default watchlist found")
    except Exception as e:
        st.error(f"Failed to add {ticker}: {str(e)}")


def display_batchscanner_dev():
    """Mobile-friendly batch scanner interface"""
    
    # Mobile-optimized header
    st.title("📱 Stock Scanner")
    
    # Simple selection in mobile-friendly layout
    st.subheader("1. Select Stock Universe")
    universe = st.radio(
        "Choose stocks to scan:",
        ["Watchlist", "Small Cap", "Mid Cap"],
        horizontal=True,
        help="Select which group of stocks to analyze"
    )
    
    # Get tickers
    tickers = get_tickers_for_selection(universe)
    
    if not tickers:
        st.warning(f"No stocks found in {universe}")
        return
    
    st.info(f"Ready to scan {len(tickers)} stocks from {universe}")
    
    # Mobile-friendly scan button
    st.subheader("2. Start Scan")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        scan_button = st.button(
            f"🚀 Scan {len(tickers)} Stocks", 
            type="primary", 
            use_container_width=True
        )
    
    with col2:
        auto_add = st.checkbox("Auto-add BUYs", help="Automatically add BUY signals to watchlist")
    
    # Run scan
    if scan_button:
        with st.spinner(f"Scanning {len(tickers)} stocks..."):
            # Progress bar for mobile
            progress_bar = st.progress(0)
            
            def update_progress(progress, text):
                progress_bar.progress(progress)
            
            results = run_scan(tickers, update_progress)
        
        # Clear progress
        progress_bar.empty()
        
        if results:
            # Store results
            st.session_state.mobile_scan_results = results
            
            # Auto-add BUY signals
            if auto_add:
                buy_results = [r for r in results if r.get('value_momentum_signal') == 'BUY']
                for result in buy_results:
                    add_to_watchlist(result.get('ticker'))
            
            # Success message
            st.success(f"Scan complete! Found {len(results)} results")
    
    # Display results
    st.subheader("3. Results")
    
    if 'mobile_scan_results' in st.session_state:
        results = st.session_state.mobile_scan_results
        df = create_results_dataframe(results)
        
        if not df.empty:
            # Mobile-friendly filters
            with st.expander("🔍 Filter Results"):
                col1, col2 = st.columns(2)
                
                with col1:
                    min_score = st.slider("Min Score", 0, 100, 0)
                
                with col2:
                    signal_filter = st.multiselect(
                        "Signals",
                        ["BUY", "HOLD", "SELL"],
                        default=["BUY", "HOLD", "SELL"]
                    )
            
            # Apply filters
            filtered_df = df[
                (df['Score'] >= min_score) & 
                (df['Signal'].isin(signal_filter))
            ]
            
            # Show results
            render_mobile_results(filtered_df)
            
            # Download option
            if not filtered_df.empty:
                csv = filtered_df.drop('_raw', axis=1).to_csv(index=False)
                st.download_button(
                    "📥 Download Results",
                    csv,
                    "scan_results.csv",
                    "text/csv",
                    use_container_width=True
                )
        else:
            st.info("No results from scan")
    else:
        st.info("👆 Start a scan to see results here")
    
    # Mobile tips
    with st.expander("💡 Tips"):
        st.markdown("""
        - **Scores**: 70+ = High quality, 50+ = Medium, <50 = Low
        - **Indicators**: Green = Good, Red = Caution
        - **Signals**: 🟢 BUY, 🟡 HOLD, 🔴 SELL
        - **MA40**: Stock above 40-day moving average
        - **RSI**: Momentum indicator above 50
        - **Profit**: Company is profitable
        """)