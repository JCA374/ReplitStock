# ui/batch_analysis.py - COMPLETE FILE with display_batch_analysis function

# Standard library imports
import logging
import time
from datetime import datetime

# Third-party imports
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Local application imports
from analysis.fundamental import analyze_fundamentals
from analysis.technical import calculate_all_indicators, generate_technical_signals
from config import TIMEFRAMES, PERIOD_OPTIONS
from data.db_integration import (
    get_watchlist, get_all_cached_stocks, get_cached_stock_data,
    get_cached_fundamentals, add_to_watchlist
)
from data.stock_data import StockDataFetcher
from helpers import create_results_table
from utils.ticker_mapping import normalize_ticker
from ui.performance_overview import display_performance_metrics


def add_to_default_watchlist(ticker, name):
    """Quick add to default watchlist"""
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


def check_and_restore_results():
    """Check if we should auto-restore previous results"""
    if ('batch_analysis_results' in st.session_state and 
        st.session_state.batch_analysis_results and
        'batch_analysis_timestamp' in st.session_state):
        
        # Check if results are recent (less than 24 hours old)
        try:
            from datetime import datetime, timedelta
            timestamp_str = st.session_state.batch_analysis_timestamp
            result_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            
            if datetime.now() - result_time < timedelta(hours=24):
                return True
        except:
            pass
    return False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BatchAnalyzer:
    """Enhanced batch analyzer with database-first approach"""

    def __init__(self):
        self.data_fetcher = StockDataFetcher()

    def analyze_stock(self, ticker):
        """
        Analyze a single stock with database-first, then API fallback approach
        Priority: Database -> Alpha Vantage -> Yahoo Finance
        """
        try:
            ticker = normalize_ticker(ticker)
            logger.info(f"Starting analysis for {ticker}")

            # Step 1: Fetch stock data
            stock_data, fundamentals, data_source = self._fetch_stock_data(
                ticker)

            if stock_data is None or stock_data.empty:
                return {
                    "ticker": ticker,
                    "error": "No data available",
                    "error_message": f"Could not retrieve data for {ticker} from any source"
                }

            # Step 2: Get stock info and name
            name, stock_info = self._get_stock_info(ticker)

            # Step 3: Ensure we have fundamentals
            fundamentals = self._get_fundamentals(ticker, fundamentals)

            # Step 4: Calculate technical and fundamental indicators
            indicators, signals = self._calculate_technical_indicators(
                ticker, stock_data)
            fundamental_analysis = self._analyze_fundamentals(
                ticker, fundamentals)

            # Step 5: Get current price safely
            current_price = self._get_current_price(ticker, stock_data)

            # Step 6: Calculate tech score and signals
            tech_score, buy_signal, sell_signal, signal = self._calculate_signals(
                signals, fundamental_analysis)

            # Step 7: Create comprehensive result
            result = {
                "ticker": ticker,
                "name": name,
                "price": current_price,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "tech_score": tech_score,
                "signal": signal,
                "buy_signal": buy_signal,
                "sell_signal": sell_signal,
                "data_source": data_source,

                # Technical indicators (with safe gets)
                "above_ma40": signals.get('above_ma40', False),
                "above_ma4": signals.get('above_ma4', False),
                "rsi": signals.get('rsi_value', None),
                "rsi_above_50": signals.get('rsi_above_50', False),
                "higher_lows": signals.get('higher_lows', False),
                "near_52w_high": signals.get('near_52w_high', False),
                "breakout": signals.get('breakout_up', False),

                # Fundamental indicators (with safe gets)
                "pe_ratio": fundamentals.get('pe_ratio') if fundamentals else None,
                "profit_margin": fundamentals.get('profit_margin') if fundamentals else None,
                "revenue_growth": fundamentals.get('revenue_growth') if fundamentals else None,
                "is_profitable": fundamental_analysis['overall'].get('is_profitable', False),
                "fundamental_check": fundamental_analysis['overall'].get('value_momentum_pass', False),
                "earnings_trend": "Stable"  # Default value
            }

            logger.info(f"Successfully analyzed {ticker}")
            return result

        except Exception as e:
            logger.error(f"Error analyzing {ticker}: {e}")
            return {
                "ticker": ticker,
                "error": str(e),
                "error_message": f"Analysis failed for {ticker}: {str(e)}",
                "name": ticker,
                "price": 0,
                "tech_score": 0,
                "signal": "HÅLL",  # Default to hold on error
                "buy_signal": False,
                "sell_signal": False
            }

    def _fetch_stock_data(self, ticker):
        """Fetch stock data from database first, then APIs"""
        # Step 1: Try to get data from database first
        stock_data = get_cached_stock_data(ticker, '1d', '1y', 'yahoo')
        if stock_data is None or stock_data.empty:
            stock_data = get_cached_stock_data(
                ticker, '1d', '1y', 'alphavantage')

        fundamentals = get_cached_fundamentals(ticker)
        data_source = "database"

        # Step 2: If no cached data, try APIs
        if stock_data is None or stock_data.empty:
            try:
                logger.info(f"No cached data for {ticker}, trying APIs")
                stock_data = self.data_fetcher.get_stock_data(
                    ticker, '1d', '1y', attempt_fallback=True)
                if not stock_data.empty:
                    data_source = "api"
                    logger.info(f"Got data from API for {ticker}")
            except Exception as e:
                logger.warning(f"API failed for {ticker}: {e}")
                stock_data = None

        return stock_data, fundamentals, data_source

    def _get_stock_info(self, ticker):
        """Get stock information"""
        try:
            stock_info = self.data_fetcher.get_stock_info(ticker)
            name = stock_info.get('name', ticker)
            return name, stock_info
        except Exception as e:
            logger.warning(f"Could not get stock info for {ticker}: {e}")
            return ticker, {'name': ticker}

    def _get_fundamentals(self, ticker, existing_fundamentals):
        """Get fundamentals data if not already available"""
        if not existing_fundamentals:
            try:
                return self.data_fetcher.get_fundamentals(ticker)
            except Exception as e:
                logger.debug(f"Skipping fundamentals for {ticker}: {e}")
                return {}
        return existing_fundamentals

    def _calculate_technical_indicators(self, ticker, stock_data):
        """Calculate technical indicators with error handling"""
        try:
            indicators = calculate_all_indicators(stock_data)
            if not indicators:
                logger.warning(
                    f"Could not calculate technical indicators for {ticker}")
                indicators = {}

            signals = generate_technical_signals(indicators)
            if not signals:
                logger.warning(f"Could not generate signals for {ticker}")
                signals = {}

            return indicators, signals
        except Exception as e:
            logger.warning(f"Error calculating indicators for {ticker}: {e}")
            return {}, {'tech_score': 50, 'overall_signal': 'HOLD', 'error': str(e)}

    def _analyze_fundamentals(self, ticker, fundamentals):
        """Analyze fundamentals with error handling"""
        try:
            return analyze_fundamentals(fundamentals or {})
        except Exception as e:
            logger.warning(f"Error analyzing fundamentals for {ticker}: {e}")
            return {'overall': {'value_momentum_pass': False, 'is_profitable': False}}

    def _get_current_price(self, ticker, stock_data):
        """Get current price from stock data safely"""
        try:
            return stock_data['close'].iloc[-1] if not stock_data.empty else 0
        except Exception as e:
            logger.warning(f"Error getting price for {ticker}: {e}")
            return 0

    def _calculate_signals(self, signals, fundamental_analysis):
        """Calculate technical score and buy/sell signals"""
        tech_score = signals.get('tech_score', 0)
        fundamental_pass = fundamental_analysis['overall'].get(
            'value_momentum_pass', False)

        buy_signal = tech_score >= 70 and fundamental_pass
        sell_signal = tech_score < 40 or not signals.get('above_ma40', False)
        signal = "KÖP" if buy_signal else "SÄLJ" if sell_signal else "HÅLL"

        return tech_score, buy_signal, sell_signal, signal

    def batch_analyze(self, tickers, progress_callback=None):
        """Analyze multiple stocks with progress tracking"""
        results = []

        for i, ticker in enumerate(tickers):
            if progress_callback and (i % 10 == 0 or i == len(tickers) - 1):
                progress = (i + 1) / len(tickers)
                progress_callback(
                    progress, f"Analyzing {ticker}... ({i+1}/{len(tickers)})")

            result = self.analyze_stock(ticker)
            results.append(result)

            # Minimal delay for rate limiting
            if i % 20 == 0 and i > 0:
                time.sleep(0.02)

        return results

# ui/batch_analysis.py - FORCE BULK SCANNER USAGE

def start_optimized_batch_analysis(tickers, progress_callback=None):
    """
    FIXED: Force bulk scanner usage - never use traditional analyzer
    """
    if not tickers:
        return []

    logger.info(f"🚀 FORCING BULK SCANNER for {len(tickers)} stocks")

    try:
        # Import the bulk scanner
        from analysis.bulk_scanner import optimized_bulk_scan
        
        # FORCE bulk scanner usage with maximum speed settings
        logger.info("⚡ Using optimized bulk scanner with maximum speed settings")
        
        results = optimized_bulk_scan(
            target_tickers=tickers,
            fetch_missing=True,
            max_api_workers=8,  # Increased workers
            progress_callback=progress_callback
        )

        if results:
            logger.info(f"✅ BULK SCANNER SUCCESS: {len(results)} results")
            return format_results_for_ui(results)
        else:
            logger.error("❌ BULK SCANNER FAILED - no results returned")
            # Still return empty list instead of falling back to slow method
            return []

    except ImportError as e:
        logger.error(f"❌ BULK SCANNER IMPORT FAILED: {e}")
        logger.error("Check if analysis/bulk_scanner.py exists and has optimized_bulk_scan function")
        return []
    except Exception as e:
        logger.error(f"❌ BULK SCANNER ERROR: {e}")
        return []


# DISABLE the traditional analyzer to force bulk scanner usage
def start_traditional_batch_analysis(tickers, progress_callback=None):
    """
    DISABLED: Traditional analyzer is too slow - force user to fix bulk scanner
    """
    logger.error("❌ TRADITIONAL ANALYZER DISABLED - FIX BULK SCANNER INSTEAD")
    logger.error("The traditional analyzer is 10x slower. Fix the bulk scanner configuration.")
    
    return [{
        "ticker": "ERROR",
        "error": "Traditional analyzer disabled for performance",
        "error_message": "Bulk scanner failed - check analysis/bulk_scanner.py configuration"
    }]


def format_results_for_ui(optimized_results):
    """Convert optimized bulk scan results to UI format - ENHANCED for partial data"""
    formatted_results = []

    for analysis in optimized_results:
        # ENHANCEMENT: Check for error attribute OR error field
        has_error = (hasattr(analysis, "error") and analysis.error) or (isinstance(analysis, dict) and "error" in analysis and analysis["error"])
        
        if has_error:
            formatted_results.append({
                "ticker": analysis.get("ticker", "Unknown"),
                "error": analysis.get("error", "Unknown error"),
                "error_message": analysis.get("error_message", "Unknown error"),
                "name": analysis.get("name", analysis.get("ticker", "Unknown")),
                "signal": "ERROR",
                "tech_score": 0,
                "data_source": "error"
            })
            continue

        # ENHANCEMENT: Handle data_status field 
        data_status = analysis.get("data_status", "complete")
        
        result = {
            "ticker": analysis["ticker"],
            "name": analysis.get("name", analysis["ticker"]),
            "price": analysis.get("last_price", 0),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "tech_score": analysis.get("tech_score", 0),
            "signal": analysis.get("value_momentum_signal", "HOLD"),
            "buy_signal": analysis.get("value_momentum_signal") == "BUY",
            "sell_signal": analysis.get("value_momentum_signal") == "SELL",
            "data_source": analysis.get("data_source", "api"),
            "data_status": data_status,  # Include data status
            "above_ma40": analysis.get("above_ma40", False),
            "above_ma4": analysis.get("above_ma4", False),
            "rsi_above_50": analysis.get("rsi_above_50", False),
            "near_52w_high": analysis.get("near_52w_high", False),
            "pe_ratio": analysis.get("pe_ratio"),
            "profit_margin": analysis.get("profit_margin"),
            "revenue_growth": analysis.get("revenue_growth"),
            "is_profitable": analysis.get("is_profitable", False),
            "fundamental_check": analysis.get("fundamental_pass", False)
        }
        
        # ENHANCEMENT: Add warning for partial data
        if data_status == "partial":
            result["warning"] = "Partial data available"
        elif data_status == "missing":
            result["warning"] = "Price data missing"
            result["error"] = "No price data available"
            
        formatted_results.append(result)

    return formatted_results


def render_results_with_watchlist_icons(filtered_df):
    """Render results table with clickable watchlist icons"""
    st.subheader("📊 Analysis Results with Quick Add")

    for idx, row in filtered_df.iterrows():
        with st.container():
            col_icon, col_ticker, col_name, col_price, col_signal, col_tech, col_pe = st.columns([
                0.5, 1, 2.5, 1, 1, 1, 1])

            with col_icon:
                ticker = row.get('Ticker', '')
                name = row.get('Namn', ticker)
                if st.button("➕", key=f"batch_watchlist_{ticker}_{idx}",
                             help=f"Add {ticker} to watchlist"):
                    if ticker:
                        add_stock_to_watchlist_with_feedback(ticker, name)
                        st.rerun()
                    else:
                        st.error("❌ No ticker found for this stock")

            with col_ticker:
                st.write(f"**{row.get('Ticker', 'N/A')}**")

            with col_name:
                st.write(row.get('Namn', 'N/A'))

            with col_price:
                price_str = row.get('Pris', 'N/A')
                st.write(price_str)

            with col_signal:
                signal = row.get('Signal', 'HÅLL')
                data_status = row.get('data_status', 'complete')
                
                if row.get('error') or data_status == 'error':
                    st.error(f"⚠️ ERROR")
                elif data_status == 'missing':
                    st.warning(f"⚠️ NO DATA")
                elif data_status == 'partial':
                    st.warning(f"⚠️ {signal}")
                elif signal == 'KÖP':
                    st.success(f"🟢 {signal}")
                elif signal == 'SÄLJ':
                    st.error(f"🔴 {signal}")
                else:
                    st.info(f"🟡 {signal}")

            with col_tech:
                tech_score = row.get('Tech Score', 0)
                if isinstance(tech_score, (int, float)):
                    st.metric("Tech", f"{tech_score}")
                else:
                    st.write(tech_score)

            with col_pe:
                pe = row.get('P/E', 'N/A')
                st.write(f"P/E: {pe}")

        st.divider()


def add_stock_to_watchlist_with_feedback(ticker, name):
    """Add stock to default watchlist with proper feedback"""
    try:
        if not ticker:
            st.error("❌ Invalid ticker provided", icon="❌")
            return False

        success = add_to_default_watchlist(ticker, name)

        if success:
            st.success(f"✅ Added {ticker} to watchlist!", icon="✅")
            return True
        else:
            st.info(f"ℹ️ {ticker} is already in your watchlist!", icon="ℹ️")
            return False

    except Exception as e:
        st.error(f"❌ Failed to add {ticker}: {str(e)}", icon="❌")
        return False



def display_batch_analysis():
    """Main batch analysis interface with clickable watchlist icons"""
    st.header("Batch Analysis")
    st.write(
        "Analyze multiple stocks at once using database cache first, then API fallback.")
    
    # Auto-restore recent results
    has_recent_results = check_and_restore_results()
    
    # Show existing results info if available
    if has_recent_results:
        results_count = len(st.session_state.batch_analysis_results)
        timestamp = st.session_state.get('batch_analysis_timestamp', 'Unknown time')
        analyzed_tickers = st.session_state.get('batch_analysis_tickers', [])
        
        st.info(f"📊 **Previous Results Available**: {results_count} stocks analyzed at {timestamp}")
        
        # Show quick summary of what was analyzed
        if analyzed_tickers:
            with st.expander(f"📋 Previously Analyzed Stocks ({len(analyzed_tickers)} stocks)", expanded=False):
                # Display in columns for better formatting
                cols = st.columns(5)
                for i, ticker in enumerate(analyzed_tickers[:20]):  # Show first 20
                    with cols[i % 5]:
                        st.write(f"• {ticker}")
                if len(analyzed_tickers) > 20:
                    st.write(f"... and {len(analyzed_tickers) - 20} more")
        
        # Clear results button
        if st.button("🗑️ Clear Previous Results", help="Clear previous analysis results"):
            for key in ['batch_analysis_results', 'batch_analysis_timestamp', 'batch_analysis_tickers']:
                if key in st.session_state:
                    del st.session_state[key]
            st.success("Previous results cleared!")
            st.rerun()

    # Initialize analyzer
    if 'batch_analyzer' not in st.session_state:
        st.session_state.batch_analyzer = BatchAnalyzer()

    analyzer = st.session_state.batch_analyzer

    # Get watchlist for quick selection
    watchlist = get_watchlist()
    watchlist_tickers = [item['ticker']
                         for item in watchlist] if watchlist else []

    # Settings in main content area
    st.header("Batch Analysis")
    st.write("Analyze multiple stocks at once using database cache first, then API fallback.")
    
    with st.expander("⚙️ Analysis Settings", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            analysis_mode = st.radio(
                "Analysis Mode:",
                ["All Watchlist Stocks", "Selected Watchlist", "All Small Cap",
                 "All Mid Cap", "All Large Cap", "Selected Stocks"],
                key="batch_analysis_mode"
            )
        
        with col2:
            st.info("📊 Data Priority: Cache → Alpha Vantage → Yahoo Finance")

    selected_tickers = []

    if analysis_mode == "All Watchlist Stocks":
        if not watchlist:
            st.warning(
                "Your watchlist is empty. Please add stocks to your watchlist or use another mode.")
        else:
            selected_tickers = watchlist_tickers
            st.success(
                f"Ready to analyze all {len(selected_tickers)} stocks in your watchlist")

    elif analysis_mode == "Selected Watchlist":
        # Get all watchlists
        if 'watchlist_manager' not in st.session_state:
            from services.watchlist_manager import SimpleWatchlistManager
            st.session_state.watchlist_manager = SimpleWatchlistManager()
        
        manager = st.session_state.watchlist_manager
        watchlists = manager.get_all_watchlists()
        
        if watchlists:
            selected_wl = st.selectbox(
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

    elif analysis_mode == "All Small Cap":
        try:
            small_cap_df = pd.read_csv('data/csv/updated_small.csv')
            small_cap_tickers = small_cap_df['YahooTicker'].tolist()
            selected_tickers = [t for t in small_cap_tickers if pd.notna(t)]
            st.success(
                f"Ready to analyze all {len(selected_tickers)} stocks from Small Cap list")
        except Exception as e:
            st.error(f"Failed to load Small Cap CSV file: {str(e)}")

    elif analysis_mode == "All Mid Cap":
        try:
            mid_cap_df = pd.read_csv('data/csv/updated_mid.csv')
            mid_cap_tickers = mid_cap_df['YahooTicker'].tolist()

            # Fix common ticker format issues in midcap CSV
            fixed_tickers = []
            for ticker in mid_cap_tickers:
                if pd.notna(ticker):
                    # Fix tickers missing .ST suffix
                    if ticker.endswith('ST') and not ticker.endswith('.ST'):
                        ticker = ticker[:-2] + '.ST'
                    fixed_tickers.append(ticker)

            selected_tickers = fixed_tickers
            st.success(
                f"Ready to analyze all {len(selected_tickers)} stocks from Mid Cap list")
        except Exception as e:
            st.error(f"Failed to load Mid Cap CSV file: {str(e)}")

    elif analysis_mode == "All Large Cap":
        try:
            large_cap_df = pd.read_csv('data/csv/updated_large.csv')
            large_cap_tickers = large_cap_df['YahooTicker'].tolist()
            selected_tickers = [t for t in large_cap_tickers if pd.notna(t)]
            st.success(
                f"Ready to analyze all {len(selected_tickers)} stocks from Large Cap list")
        except Exception as e:
            st.error(f"Failed to load Large Cap CSV file: {str(e)}")

    else:  # Selected Stocks mode
        input_method = st.radio(
            "Select stocks from:",
            ["Watchlist", "Small Cap CSV", "Mid Cap CSV",
                "Large Cap CSV", "Manual Entry"],
            key="batch_input_method"
        )

        if input_method == "Watchlist":
            if not watchlist:
                st.warning("Your watchlist is empty.")
            else:
                selected_tickers = st.multiselect(
                    "Select stocks from your watchlist:",
                    options=watchlist_tickers,
                    key="batch_watchlist_select"
                )

        elif input_method == "Small Cap CSV":
            try:
                small_cap_df = pd.read_csv('data/csv/updated_small.csv')
                small_cap_tickers = small_cap_df['YahooTicker'].tolist()
                selected_tickers = st.multiselect(
                    "Select stocks from Small Cap list:",
                    options=[t for t in small_cap_tickers if pd.notna(t)],
                    key="batch_small_cap_select"
                )
            except Exception as e:
                st.error(f"Failed to load Small Cap CSV file: {str(e)}")

        elif input_method == "Mid Cap CSV":
            try:
                mid_cap_df = pd.read_csv('data/csv/updated_mid.csv')
                mid_cap_tickers = mid_cap_df['YahooTicker'].tolist()

                # Fix ticker format issues for selection
                fixed_options = []
                for ticker in mid_cap_tickers:
                    if pd.notna(ticker):
                        if ticker.endswith('ST') and not ticker.endswith('.ST'):
                            ticker = ticker[:-2] + '.ST'
                        fixed_options.append(ticker)

                selected_tickers = st.multiselect(
                    "Select stocks from Mid Cap list:",
                    options=fixed_options,
                    key="batch_mid_cap_select"
                )
            except Exception as e:
                st.error(f"Failed to load Mid Cap CSV file: {str(e)}")

        elif input_method == "Large Cap CSV":
            try:
                large_cap_df = pd.read_csv('data/csv/updated_large.csv')
                large_cap_tickers = large_cap_df['YahooTicker'].tolist()
                selected_tickers = st.multiselect(
                    "Select stocks from Large Cap list:",
                    options=[t for t in large_cap_tickers if pd.notna(t)],
                    key="batch_large_cap_select"
                )
            except Exception as e:
                st.error(f"Failed to load Large Cap CSV file: {str(e)}")

        else:  # Manual Entry
            ticker_input = st.text_input(
                "Enter ticker symbols (comma-separated):",
                key="batch_manual_tickers"
            )
            if ticker_input:
                raw_tickers = [t.strip() for t in ticker_input.split(",")]
                selected_tickers = [normalize_ticker(
                    t) for t in raw_tickers if t]

    # Show data source priority info
    st.info("📊 **Data Source Priority**: Database Cache → Alpha Vantage API → Yahoo Finance API")

    # Analysis execution
    run_button = st.button("🚀 Run Batch Analysis",
                           type="primary", disabled=len(selected_tickers) == 0)

    if run_button and selected_tickers:
        # Create progress indicators
        progress_bar = st.progress(0)
        status_text = st.empty()

        def update_progress(progress, text):
            progress_bar.progress(progress)
            status_text.text(text)

        # Run optimized analysis
        with st.spinner(f"Running optimized analysis on {len(selected_tickers)} stocks..."):
            results = start_optimized_batch_analysis(
                selected_tickers, update_progress)

        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()

        # Store results in session state with persistence
        st.session_state.batch_analysis_results = results
        st.session_state.batch_analysis_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.batch_analysis_tickers = selected_tickers.copy()  # Remember what was analyzed

        # Show performance summary
        success_count = len([r for r in results if "error" not in r])
        error_count = len([r for r in results if "error" in r])

        st.success(f"✅ Optimized analysis complete!")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Processed", len(results))
        with col2:
            st.metric("Successful", success_count)
        with col3:
            st.metric("Failed", error_count)

    # Display results if available
    if 'batch_analysis_results' in st.session_state:
        results = st.session_state.batch_analysis_results
        
        # Show analysis summary
        if results:
            timestamp = st.session_state.get('batch_analysis_timestamp', 'Unknown time')
            st.subheader(f"📈 Analysis Results (Generated: {timestamp})")
            success_results = [r for r in results if "error" not in r]
            error_results = [r for r in results if "error" in r]

            if success_results:
                try:
                    results_df = create_results_table(success_results)

                    if not results_df.empty:
                        st.subheader(
                            f"📈 Analysis Results ({len(success_results)} successful)")

                        # Add filtering options
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            signal_filter = st.multiselect(
                                "Filter by Signal:",
                                ["KÖP", "HÅLL", "SÄLJ"],
                                default=["KÖP", "HÅLL", "SÄLJ"],
                                key="batch_signal_filter"
                            )

                        with col2:
                            min_tech_score = st.slider(
                                "Minimum Tech Score:",
                                0, 100, 0,
                                key="batch_tech_score_filter"
                            )

                        with col3:
                            available_sources = results_df["Data Source"].unique(
                            ).tolist() if "Data Source" in results_df.columns else []
                            data_source_filter = st.multiselect(
                                "Data Source:",
                                available_sources,
                                default=available_sources,
                                key="batch_source_filter"
                            )

                        # Apply filters
                        filtered_df = results_df.copy()

                        if signal_filter and "Signal" in filtered_df.columns:
                            filtered_df = filtered_df[filtered_df["Signal"].isin(
                                signal_filter)]

                        if "Tech Score" in filtered_df.columns:
                            filtered_df = filtered_df[filtered_df["Tech Score"]
                                                      >= min_tech_score]

                        if data_source_filter and "Data Source" in filtered_df.columns:
                            filtered_df = filtered_df[filtered_df["Data Source"].isin(
                                data_source_filter)]

                        # Sort by Signal priority then Tech Score
                        if "Signal" in filtered_df.columns and "Tech Score" in filtered_df.columns:
                            signal_priority = {"KÖP": 1, "HÅLL": 2, "SÄLJ": 3}
                            filtered_df["_signal_priority"] = filtered_df["Signal"].map(
                                signal_priority).fillna(4)
                            filtered_df = filtered_df.sort_values(
                                ["_signal_priority", "Tech Score"], ascending=[True, False])
                            filtered_df = filtered_df.drop(
                                "_signal_priority", axis=1)
                        elif "Tech Score" in filtered_df.columns:
                            filtered_df = filtered_df.sort_values(
                                "Tech Score", ascending=False)

                        # Results controls - moved above the table
                        st.subheader("📊 Results Actions")
                        
                        # Action controls in columns
                        action_col1, action_col2, action_col3 = st.columns([1, 1, 1])
                        
                        with action_col1:
                            # Traditional dataframe view toggle
                            show_traditional = st.checkbox("📊 Show Traditional Table", value=False, key="show_traditional_table")
                        
                        with action_col2:
                            # Download button
                            csv_data = filtered_df.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="📥 Download Results as CSV",
                                data=csv_data,
                                file_name=f"batch_analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                        
                        with action_col3:
                            # Bulk add controls
                            # Use the simple watchlist manager
                            if 'watchlist_manager' not in st.session_state:
                                from services.watchlist_manager import SimpleWatchlistManager
                                st.session_state.watchlist_manager = SimpleWatchlistManager()

                            manager = st.session_state.watchlist_manager
                            watchlists = manager.get_all_watchlists()
                            
                            if watchlists:
                                # Watchlist selection for bulk add
                                target_watchlist = st.selectbox(
                                    "📁 Select Watchlist:",
                                    options=watchlists,
                                    format_func=lambda x: f"{x['name']} {'(Default)' if x['is_default'] else ''}",
                                    key="bulk_add_watchlist",
                                    label_visibility="collapsed"
                                )
                                
                                # Get stocks with BUY signals
                                top_buy_signals = pd.DataFrame()
                                if "Signal" in filtered_df.columns:
                                    top_buy_signals = filtered_df[
                                        (filtered_df["Signal"] == "KÖP") | 
                                        (filtered_df["Signal"] == "BUY")
                                    ].head(10)
                                
                                if not top_buy_signals.empty and target_watchlist:
                                    if st.button("➕ Add All BUY Signals", type="primary", key="bulk_add_button", use_container_width=True):
                                        added_count = 0
                                        failed_count = 0
                                        
                                        for _, stock in top_buy_signals.iterrows():
                                            ticker = stock.get('Ticker', '')
                                            if ticker:
                                                success = manager.add_stock_to_watchlist(target_watchlist['id'], ticker)
                                                if success:
                                                    added_count += 1
                                                else:
                                                    failed_count += 1
                                        
                                        # Summary
                                        if added_count > 0:
                                            st.success(f"✅ Added {added_count} stocks to '{target_watchlist['name']}'!")
                                        if failed_count > 0:
                                            st.info(f"ℹ️ {failed_count} stocks already in watchlist")
                                else:
                                    st.info("No BUY signals to add")
                            else:
                                st.warning("No watchlists available")
                        
                        st.divider()

                        # Render results with clickable watchlist icons
                        render_results_with_watchlist_icons(filtered_df)
                        
                        # Show traditional table view if requested
                        if show_traditional:
                            st.subheader("📊 Traditional Table View")
                            st.dataframe(filtered_df, use_container_width=True, hide_index=True)

                except Exception as e:
                    st.error(f"Error displaying results: {e}")

            # Show error results if any
            if error_results:
                with st.expander(f"⚠️ Failed Analyses ({len(error_results)})", expanded=False):
                    error_df = pd.DataFrame(error_results)
                    st.dataframe(error_df, use_container_width=True)
