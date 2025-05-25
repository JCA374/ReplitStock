# Enhanced Stock Scanner - Comprehensive Ranking and Watchlist Management

# Standard library imports
import logging
import time
from datetime import datetime, timedelta

# Third-party imports
import numpy as np
import pandas as pd
import streamlit as st

# Local application imports
from analysis.fundamental import analyze_fundamentals
from analysis.scanner import StockScanner
from analysis.technical import calculate_all_indicators, generate_technical_signals
from data.db_integration import get_watchlist, get_all_cached_stocks, add_to_watchlist
from helpers import get_index_constituents

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('enhanced_scanner')

class EnhancedStockScorer:
    """
    Comprehensive stock scoring system that combines multiple factors
    """
    
    def __init__(self, strategy=None):
        self.strategy = strategy
        
    def calculate_comprehensive_score(self, analysis_result):
        """
        Calculate a comprehensive score from 0-100 based on multiple factors
        """
        if "error" in analysis_result:
            return 0
            
        score = 0
        
        # Technical Score (40% weight)
        tech_score = analysis_result.get('tech_score', 0)
        score += (tech_score / 100) * 40
        
        # Fundamental Score (30% weight)
        fund_score = self._calculate_fundamental_score(analysis_result)
        score += (fund_score / 100) * 30
        
        # Momentum Score (20% weight)
        momentum_score = self._calculate_momentum_score(analysis_result)
        score += (momentum_score / 100) * 20
        
        # Quality Score (10% weight)
        quality_score = self._calculate_quality_score(analysis_result)
        score += (quality_score / 100) * 10
        
        return min(100, max(0, score))
    
    def _calculate_fundamental_score(self, analysis):
        """Calculate fundamental score based on financial metrics"""
        score = 0
        
        # Profitability (40 points)
        if analysis.get('is_profitable', False):
            score += 20
            
        pe_ratio = analysis.get('pe_ratio')
        if pe_ratio and 5 <= pe_ratio <= 25:  # Reasonable P/E
            score += 20
        elif pe_ratio and pe_ratio < 5:
            score += 10  # Very cheap but risky
            
        # Growth (30 points)
        revenue_growth = analysis.get('revenue_growth', 0)
        if revenue_growth and revenue_growth > 0.1:  # 10%+ growth
            score += 15
        elif revenue_growth and revenue_growth > 0.05:  # 5%+ growth
            score += 10
            
        profit_margin = analysis.get('profit_margin', 0)
        if profit_margin and profit_margin > 0.15:  # 15%+ margin
            score += 15
        elif profit_margin and profit_margin > 0.05:  # 5%+ margin
            score += 10
            
        # Earnings trend (30 points)
        earnings_trend = analysis.get('earnings_trend', '')
        if 'ökande' in earnings_trend.lower():  # Increasing
            score += 30
        elif 'nyligen ökande' in earnings_trend.lower():  # Recently increasing
            score += 20
            
        return min(100, score)
    
    def _calculate_momentum_score(self, analysis):
        """Calculate momentum score based on price action"""
        score = 0
        
        # Price vs moving averages (50 points)
        if analysis.get('above_ma40', False):
            score += 25
        if analysis.get('above_ma4', False):
            score += 25
            
        # RSI momentum (25 points)
        if analysis.get('rsi_above_50', False):
            score += 25
            
        # Price patterns (25 points)
        if analysis.get('higher_lows', False):
            score += 10
        if analysis.get('near_52w_high', False):
            score += 10
        if analysis.get('breakout', False):
            score += 5
            
        return min(100, score)
    
    def _calculate_quality_score(self, analysis):
        """Calculate quality score based on business quality indicators"""
        score = 50  # Base score
        
        # Data source quality
        data_source = analysis.get('data_source', 'unknown')
        if data_source in ['yahoo', 'alphavantage']:
            score += 20
            
        # Fundamental data availability
        if analysis.get('pe_ratio') is not None:
            score += 15
        if analysis.get('revenue_growth') is not None:
            score += 15
            
        return min(100, score)

# NOTE: This class is being replaced by StockScanner from analysis.scanner module
# Keeping it here temporarily for reference during migration
class EnhancedStockScanner:
    """
    Enhanced stock scanner with comprehensive ranking and easy watchlist management
    """
    
    def __init__(self):
        self.strategy = st.session_state.get('strategy')
        self.watchlist_manager = st.session_state.get('watchlist_manager')
        self.scorer = EnhancedStockScorer(self.strategy)
        
    def scan_and_rank_stocks(self, tickers, progress_callback=None):
        """
        Scan stocks and rank them comprehensively
        """
        results = []
        failed_analyses = []
        
        for i, ticker in enumerate(tickers):
            if progress_callback:
                progress = i / len(tickers)
                progress_callback(progress, f"Analyzing {ticker}... ({i+1}/{len(tickers)})")
            
            # Get analysis from strategy
            if self.strategy:
                analysis = self.strategy.analyze_stock(ticker)
            else:
                # Fallback to basic analysis if no strategy available
                analysis = {"ticker": ticker, "error": "No strategy available"}
            
            if "error" in analysis:
                failed_analyses.append({
                    "ticker": ticker,
                    "error": analysis["error"],
                    "error_message": analysis.get("error_message", "Unknown error")
                })
                continue
            
            # Calculate comprehensive score
            comprehensive_score = self.scorer.calculate_comprehensive_score(analysis)
            
            # Create enhanced result
            result = {
                "Rank": 0,  # Will be set after sorting
                "Ticker": analysis["ticker"],
                "Name": analysis.get("name", ticker),
                "Price": analysis.get("price", 0),
                "Score": round(comprehensive_score, 1),
                "Tech Score": analysis.get("tech_score", 0),
                "Signal": analysis.get("signal", "HÅLL"),
                "Above MA40": "✓" if analysis.get("above_ma40", False) else "✗",
                "Above MA4": "✓" if analysis.get("above_ma4", False) else "✗",
                "RSI > 50": "✓" if analysis.get("rsi_above_50", False) else "✗",
                "Near 52w High": "✓" if analysis.get("near_52w_high", False) else "✗",
                "Profitable": "✓" if analysis.get("is_profitable", False) else "✗",
                "P/E": round(analysis.get("pe_ratio", 0), 1) if analysis.get("pe_ratio") else "N/A",
                "Data Source": analysis.get("data_source", "unknown").title(),
                "_analysis": analysis  # Keep full analysis for detailed view
            }
            
            results.append(result)
        
        # Sort by comprehensive score and assign ranks
        results.sort(key=lambda x: x["Score"], reverse=True)
        for i, result in enumerate(results):
            result["Rank"] = i + 1
        
        # Store failed analyses
        st.session_state.failed_analyses = failed_analyses
        
        return results

def load_tickers_from_csv(universe_file, limit_stocks=False):
    """
    Load tickers from CSV file or use predefined lists
    """
    try:
        if universe_file == "OMXS30":
            tickers = get_index_constituents("OMXS30")
        elif universe_file == "S&P 500 Top 30":
            tickers = get_index_constituents("S&P 500 Top 30")
        elif universe_file == "Dow Jones":
            tickers = get_index_constituents("Dow Jones")
        elif universe_file == "Watchlist":
            watchlist = get_watchlist()
            tickers = [stock['ticker'] for stock in watchlist]
        elif universe_file == "All Database Stocks":
            tickers = get_all_cached_stocks()
        else:
            # Try to load from CSV file
            try:
                df = pd.read_csv(universe_file)
                if 'ticker' in df.columns:
                    tickers = df['ticker'].tolist()
                elif 'Ticker' in df.columns:
                    tickers = df['Ticker'].tolist()
                else:
                    # Take first column as tickers
                    tickers = df.iloc[:, 0].tolist()
            except FileNotFoundError:
                st.error(f"File {universe_file} not found")
                return []
        
        if limit_stocks:
            tickers = tickers[:20]
            
        return tickers
    except Exception as e:
        st.error(f"Error loading tickers: {str(e)}")
        return []

def render_enhanced_scanner_ui():
    """
    Render the enhanced scanner UI
    """
    st.header("📊 Enhanced Stock Scanner")
    st.markdown("*Comprehensive stock ranking with easy watchlist management*")
    
    # Initialize scanner - using StockScanner instead of EnhancedStockScanner
    if 'enhanced_scanner' not in st.session_state:
        st.session_state.enhanced_scanner = StockScanner()
    
    scanner = st.session_state.enhanced_scanner
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        render_scanner_controls(scanner)
    
    with col2:
        render_scanner_results(scanner)

def render_scanner_controls(scanner):
    """
    Render scanner control panel
    """
    st.subheader("🎯 Scanner Settings")
    
    # Stock universe selection
    universe_options = [
        "OMXS30",
        "S&P 500 Top 30",
        "Dow Jones",
        "Watchlist",
        "All Database Stocks"
    ]
    
    selected_universe = st.selectbox(
        "Stock Universe",
        universe_options,
        index=0,  # Default to OMXS30
        help="Choose which set of stocks to scan"
    )
    
    # Scan options
    st.subheader("⚙️ Options")
    
    limit_stocks = st.checkbox("Limit to first 20 stocks (for testing)", value=False)
    
    batch_size = st.slider("Batch Size", 10, 50, 25, 
                          help="Number of stocks to process at once")
    
    # Scan button
    if st.button("🚀 Start Enhanced Scan", type="primary", use_container_width=True):
        start_enhanced_scan(scanner, selected_universe, limit_stocks, batch_size)
    
    # Watchlist quick add section
    if 'scan_results' in st.session_state and st.session_state.scan_results:
        st.subheader("📝 Quick Add to Watchlist")
        render_watchlist_quick_add()


def start_enhanced_scan(scanner, universe_file, limit_stocks, batch_size):
    """
    Start the enhanced scanning process using optimized bulk scanning
    """
    # Load tickers from selected universe
    tickers = load_tickers_from_csv(universe_file, limit_stocks)

    if not tickers:
        st.error("No tickers found to scan")
        return

    # Show info about the scan
    st.info(f"🚀 Starting optimized bulk scan of {len(tickers)} stocks")
    st.info("📊 **Process**: Database bulk load → Batch API calls → Parallel analysis")

    # Show progress
    progress_bar = st.progress(0)
    status_text = st.empty()

    def update_progress(progress, message):
        progress_bar.progress(progress)
        status_text.text(message)

    # Run optimized bulk scan
    with st.spinner("Running optimized bulk scan..."):
        # Import the optimized scanner
        from analysis.bulk_scanner import optimized_bulk_scan

        # Use the optimized bulk scanning approach
        scan_results = optimized_bulk_scan(
            target_tickers=tickers,
            fetch_missing=True,  # Fetch missing data via APIs
            max_api_workers=3,   # Conservative API worker count
            progress_callback=update_progress
        )

        # Process results into the format expected by the UI
        results = []
        failed_analyses = []

        # Process each analysis result
        for analysis in scan_results:
            if "error" in analysis and analysis["error"]:
                failed_analyses.append({
                    "ticker": analysis.get("ticker", "Unknown"),
                    "error": analysis["error"],
                    "error_message": analysis.get("error_message", "Unknown error")
                })
                continue

            # Calculate comprehensive score using EnhancedStockScorer
            scorer = EnhancedStockScorer(st.session_state.get('strategy'))
            comprehensive_score = scorer.calculate_comprehensive_score(
                analysis)

            # Create enhanced result
            result = {
                "Rank": 0,  # Will be set after sorting
                "Ticker": analysis["ticker"],
                "Name": analysis.get("name", analysis["ticker"]),
                # Note: different field name from bulk scanner
                "Price": analysis.get("last_price", 0),
                "Score": round(comprehensive_score, 1),
                "Tech Score": analysis.get("tech_score", 0),
                # Note: different field name
                "Signal": analysis.get("value_momentum_signal", "HOLD"),
                "Above MA40": "✓" if analysis.get("above_ma40", False) else "✗",
                "Above MA4": "✓" if analysis.get("above_ma4", False) else "✗",
                "RSI > 50": "✓" if analysis.get("rsi_above_50", False) else "✗",
                "Near 52w High": "✓" if analysis.get("near_52w_high", False) else "✗",
                "Profitable": "✓" if analysis.get("is_profitable", False) else "✗",
                "P/E": round(analysis.get("pe_ratio", 0), 1) if analysis.get("pe_ratio") else "N/A",
                "Data Source": analysis.get("data_source", "unknown").title(),
                "_analysis": analysis  # Keep full analysis for detailed view
            }

            results.append(result)

        # Sort by comprehensive score and assign ranks
        results.sort(key=lambda x: x["Score"], reverse=True)
        for i, result in enumerate(results):
            result["Rank"] = i + 1

        # Store failed analyses
        st.session_state.failed_analyses = failed_analyses

    # Store results
    st.session_state.scan_results = results

    # Clear progress
    progress_bar.empty()
    status_text.empty()

    # Show performance summary
    st.success(f"✅ Optimized scan complete!")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Analyzed", len(results))
    with col2:
        st.metric("Successful", len(results))
    with col3:
        st.metric("Failed", len(failed_analyses))


def render_scanner_results(scanner):
    """
    Render scanner results with ranking
    """
    if 'scan_results' not in st.session_state or not st.session_state.scan_results:
        st.info("👈 Use the controls to start a scan")
        return
    
    results = st.session_state.scan_results
    df = pd.DataFrame(results)
    
    st.subheader(f"📈 Scan Results ({len(results)} stocks)")
    
    # Filtering options
    with st.expander("🔍 Filter Results", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            min_score = st.slider("Minimum Score", 0, 100, 0)
            
        with col2:
            signals = st.multiselect(
                "Signals",
                ["KÖP", "HÅLL", "SÄLJ"],
                default=["KÖP", "HÅLL", "SÄLJ"]
            )
            
        with col3:
            top_n = st.slider("Show Top N", 10, len(results), min(50, len(results)))
    
    # Apply filters
    filtered_df = df[
        (df["Score"] >= min_score) &
        (df["Signal"].isin(signals))
    ].head(top_n)
    
    if filtered_df.empty:
        st.warning("No stocks match the current filters")
        return
    
    # Display results table
    display_columns = [
        "Rank", "Ticker", "Name", "Score", "Signal", "Price",
        "Above MA40", "Above MA4", "RSI > 50", "Profitable", "P/E"
    ]
    
    st.dataframe(
        filtered_df[display_columns],
        column_config={
            "Rank": st.column_config.NumberColumn("Rank", width="small"),
            "Score": st.column_config.ProgressColumn(
                "Score", 
                min_value=0, 
                max_value=100,
                format="%.1f"
            ),
            "Signal": st.column_config.TextColumn("Signal", width="small"),
            "Price": st.column_config.NumberColumn("Price", format="%.2f"),
        },
        use_container_width=True,
        hide_index=True
    )
    
    # Top performers highlight
    st.subheader("🏆 Top 5 Performers")
    top_5 = filtered_df.head(5)
    
    for _, stock in top_5.iterrows():
        with st.container():
            col1, col2, col3, col4 = st.columns([1, 2, 1, 1])
            
            with col1:
                st.metric("Rank", f"#{stock['Rank']}")
            
            with col2:
                st.write(f"**{stock['Ticker']}** - {stock['Name']}")
                st.write(f"Signal: {stock['Signal']}")
                
            with col3:
                st.metric("Score", f"{stock['Score']:.1f}")
                
            with col4:
                if st.button(f"Add to Watchlist", key=f"add_{stock['Ticker']}"):
                    add_stock_to_watchlist(stock['Ticker'], stock['Name'])
    
    # Show failed analyses if any
    if hasattr(st.session_state, 'failed_analyses') and st.session_state.failed_analyses:
        with st.expander(f"⚠️ Failed Analyses ({len(st.session_state.failed_analyses)})", expanded=False):
            failed_df = pd.DataFrame(st.session_state.failed_analyses)
            st.dataframe(failed_df, use_container_width=True)

def render_watchlist_quick_add():
    """
    Render quick add to watchlist section
    """
    if 'scan_results' not in st.session_state or not st.session_state.scan_results:
        return
    
    results = st.session_state.scan_results
    
    # Get top 10 performers for quick add
    top_performers = sorted(results, key=lambda x: x["Score"], reverse=True)[:10]
    
    st.write("**Top 10 Performers:**")
    
    for stock in top_performers:
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.write(f"{stock['Ticker']} - Score: {stock['Score']:.1f}")
            
        with col2:
            st.write(f"{stock['Signal']}")
            
        with col3:
            if st.button("Add", key=f"quick_add_{stock['Ticker']}"):
                add_stock_to_watchlist(stock['Ticker'], stock['Name'])

def add_stock_to_watchlist(ticker, name):
    """
    Add stock to watchlist with feedback
    """
    try:
        add_to_watchlist(ticker, name)
        st.success(f"✅ Added {ticker} to watchlist!")
        # Refresh watchlist in session state if it exists
        if 'watchlist' in st.session_state:
            del st.session_state['watchlist']
    except Exception as e:
        st.error(f"❌ Failed to add {ticker}: {str(e)}")