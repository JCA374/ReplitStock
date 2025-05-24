import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time
import logging

# Import data sources in priority order
from data.db_integration import (
    get_watchlist, get_all_cached_stocks, get_cached_stock_data,
    get_cached_fundamentals, add_to_watchlist
)
from data.stock_data import StockDataFetcher
from analysis.technical import calculate_all_indicators, generate_technical_signals
from analysis.fundamental import analyze_fundamentals
from utils.ticker_mapping import normalize_ticker
from config import TIMEFRAMES, PERIOD_OPTIONS
from helpers import create_results_table

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

            # Step 1: Try to get data from database first
            stock_data = get_cached_stock_data(ticker, '1d', '1y', 'yahoo')
            if stock_data is None:
                stock_data = get_cached_stock_data(
                    ticker, '1d', '1y', 'alphavantage')

            fundamentals = get_cached_fundamentals(ticker)

            data_source = "database"

            # Step 2: If no cached data, try Alpha Vantage API
            if stock_data is None or stock_data.empty:
                try:
                    logger.info(
                        f"No cached data for {ticker}, trying Alpha Vantage API")
                    stock_data = self.data_fetcher.get_stock_data(
                        ticker, '1d', '1y', attempt_fallback=False)
                    if not stock_data.empty:
                        data_source = "alphavantage"
                        logger.info(
                            f"Got data from Alpha Vantage for {ticker}")
                except Exception as e:
                    logger.warning(f"Alpha Vantage failed for {ticker}: {e}")
                    stock_data = None

            # Step 3: If still no data, try Yahoo Finance as final fallback
            if stock_data is None or stock_data.empty:
                try:
                    logger.info(f"Trying Yahoo Finance for {ticker}")
                    stock_data = self.data_fetcher.get_stock_data(
                        ticker, '1d', '1y', attempt_fallback=True)
                    if not stock_data.empty:
                        data_source = "yahoo"
                        logger.info(
                            f"Got data from Yahoo Finance for {ticker}")
                except Exception as e:
                    logger.error(f"All data sources failed for {ticker}: {e}")
                    return {
                        "ticker": ticker,
                        "error": f"Failed to fetch data: {str(e)}",
                        "error_message": f"No data available for {ticker}"
                    }

            if stock_data is None or stock_data.empty:
                return {
                    "ticker": ticker,
                    "error": "No data available",
                    "error_message": f"Could not retrieve data for {ticker} from any source"
                }

            # Get stock info
            try:
                stock_info = self.data_fetcher.get_stock_info(ticker)
                name = stock_info.get('name', ticker)
            except:
                name = ticker
                stock_info = {'name': ticker}

            # Get fundamentals if not from cache
            if not fundamentals:
                try:
                    fundamentals = self.data_fetcher.get_fundamentals(ticker)
                except Exception as e:
                    logger.warning(
                        f"Could not get fundamentals for {ticker}: {e}")
                    fundamentals = {}

            # Calculate technical indicators
            try:
                indicators = calculate_all_indicators(stock_data)
                if not indicators:
                    logger.warning(
                        f"Could not calculate technical indicators for {ticker}")
                    indicators = {}
            except Exception as e:
                logger.error(f"Error calculating technical indicators for {ticker}: {e}")
                indicators = {}

            # Generate technical signals
            try:
                signals = generate_technical_signals(indicators)
                if not signals:
                    logger.warning(f"Could not generate signals for {ticker}")
                    signals = {}
            except Exception as e:
                logger.error(f"Error generating technical signals for {ticker}: {e}")
                signals = {}

            # Analyze fundamentals
            try:
                fundamental_analysis = analyze_fundamentals(fundamentals or {})
            except Exception as e:
                logger.error(f"Error analyzing fundamentals for {ticker}: {e}")
                fundamental_analysis = {'overall': {'value_momentum_pass': False, 'is_profitable': False}}

            # Get current price
            current_price = stock_data['close'].iloc[-1] if not stock_data.empty else 0

            # Calculate tech score and signals
            tech_score = signals.get('tech_score', 0)
            buy_signal = tech_score >= 70 and fundamental_analysis['overall'].get(
                'value_momentum_pass', False)
            sell_signal = tech_score < 40 or not signals.get(
                'above_ma40', False)

            signal = "KÖP" if buy_signal else "SÄLJ" if sell_signal else "HÅLL"

            # Create comprehensive result
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

                # Technical indicators
                "above_ma40": signals.get('above_ma40', False),
                "above_ma4": signals.get('above_ma4', False),
                "rsi": signals.get('rsi_value', None),
                "rsi_above_50": signals.get('rsi_above_50', False),
                "higher_lows": signals.get('higher_lows', False),
                "near_52w_high": signals.get('near_52w_high', False),
                "breakout": signals.get('breakout_up', False),

                # Fundamental indicators
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
                "error_message": f"Analysis failed for {ticker}: {str(e)}"
            }

    def batch_analyze(self, tickers, progress_callback=None):
        """Analyze multiple stocks with progress tracking"""
        results = []

        for i, ticker in enumerate(tickers):
            if progress_callback:
                progress = (i + 1) / len(tickers)
                progress_callback(
                    progress, f"Analyzing {ticker}... ({i+1}/{len(tickers)})")

            result = self.analyze_stock(ticker)
            results.append(result)

            # Small delay to prevent rate limiting
            time.sleep(0.1)

        return results


def display_batch_analysis():
    """Main batch analysis interface"""
    st.header("Batch Analysis")
    st.write(
        "Analyze multiple stocks at once using database cache first, then API fallback.")

    # Initialize analyzer
    if 'batch_analyzer' not in st.session_state:
        st.session_state.batch_analyzer = BatchAnalyzer()

    analyzer = st.session_state.batch_analyzer

    # Get watchlist for quick selection
    watchlist = get_watchlist()
    watchlist_tickers = [item['ticker']
                         for item in watchlist] if watchlist else []

    # Input methods for batch analysis
    st.sidebar.header("Batch Analysis Settings")

    analysis_mode = st.sidebar.radio(
        "Analysis Mode:",
        ["All Watchlist Stocks", "All Small Cap",
            "All Mid Cap", "All Large Cap", "Selected Stocks"],
        key="batch_analysis_mode"
    )

    selected_tickers = []

    if analysis_mode == "All Watchlist Stocks":
        if not watchlist:
            st.warning(
                "Your watchlist is empty. Please add stocks to your watchlist or use another mode.")
        else:
            selected_tickers = watchlist_tickers
            st.success(
                f"Ready to analyze all {len(selected_tickers)} stocks in your watchlist")

    elif analysis_mode == "All Small Cap":
        try:
            small_cap_df = pd.read_csv('csv/updated_small.csv')
            small_cap_tickers = small_cap_df['YahooTicker'].tolist()
            selected_tickers = [t for t in small_cap_tickers if pd.notna(t)]
            st.success(
                f"Ready to analyze all {len(selected_tickers)} stocks from Small Cap list")
        except Exception as e:
            st.error(f"Failed to load Small Cap CSV file: {str(e)}")

    elif analysis_mode == "All Mid Cap":
        try:
            mid_cap_df = pd.read_csv('csv/updated_mid.csv')
            mid_cap_tickers = mid_cap_df['YahooTicker'].tolist()
            selected_tickers = [t for t in mid_cap_tickers if pd.notna(t)]
            st.success(
                f"Ready to analyze all {len(selected_tickers)} stocks from Mid Cap list")
        except Exception as e:
            st.error(f"Failed to load Mid Cap CSV file: {str(e)}")

    elif analysis_mode == "All Large Cap":
        try:
            large_cap_df = pd.read_csv('csv/updated_large.csv')
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
                small_cap_df = pd.read_csv('csv/updated_small.csv')
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
                mid_cap_df = pd.read_csv('csv/updated_mid.csv')
                mid_cap_tickers = mid_cap_df['YahooTicker'].tolist()
                selected_tickers = st.multiselect(
                    "Select stocks from Mid Cap list:",
                    options=[t for t in mid_cap_tickers if pd.notna(t)],
                    key="batch_mid_cap_select"
                )
            except Exception as e:
                st.error(f"Failed to load Mid Cap CSV file: {str(e)}")

        elif input_method == "Large Cap CSV":
            try:
                large_cap_df = pd.read_csv('csv/updated_large.csv')
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
    results = None
    run_button = st.button("🚀 Run Batch Analysis",
                           type="primary", disabled=len(selected_tickers) == 0)

    if run_button and selected_tickers:
        # Create progress indicators
        progress_bar = st.progress(0)
        status_text = st.empty()

        def update_progress(progress, text):
            progress_bar.progress(progress)
            status_text.text(text)

        # Run analysis
        with st.spinner(f"Analyzing {len(selected_tickers)} stocks..."):
            results = analyzer.batch_analyze(selected_tickers, update_progress)

        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()

        # Store results in session state
        st.session_state.batch_analysis_results = results

        st.success(f"✅ Analysis complete! Processed {len(results)} stocks.")

    # Display results if available
    if 'batch_analysis_results' in st.session_state:
        results = st.session_state.batch_analysis_results

        if results:
            # Filter successful analyses
            success_results = [r for r in results if "error" not in r]
            error_results = [r for r in results if "error" in r]

            if success_results:
                st.subheader(
                    f"📈 Analysis Results ({len(success_results)} successful)")

                # Create results table
                results_df = create_results_table(success_results)

                if not results_df.empty:
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
                        data_source_filter = st.multiselect(
                            "Data Source:",
                            ["Database", "Alphavantage", "Yahoo"],
                            default=["Database", "Alphavantage", "Yahoo"],
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

                    # Sort by Tech Score
                    if "Tech Score" in filtered_df.columns:
                        filtered_df = filtered_df.sort_values(
                            "Tech Score", ascending=False)

                    # Display results table
                    st.dataframe(
                        filtered_df, use_container_width=True, hide_index=True)

                    # Download button
                    csv_data = filtered_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Results as CSV",
                        data=csv_data,
                        file_name=f"batch_analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )

                    # Quick add to watchlist section
                    if not filtered_df.empty:
                        st.subheader("📝 Quick Add to Watchlist")

                        # Get top performers for quick add
                        top_performers = filtered_df.head(10)

                        selected_for_watchlist = st.multiselect(
                            "Select stocks to add to watchlist:",
                            options=top_performers["Ticker"].tolist(
                            ) if "Ticker" in top_performers.columns else [],
                            format_func=lambda x: f"{x} - {top_performers[top_performers['Ticker'] == x]['Signal'].iloc[0] if 'Signal' in top_performers.columns else ''}"
                        )

                        if selected_for_watchlist and st.button("Add Selected to Watchlist"):
                            added_count = 0
                            for ticker in selected_for_watchlist:
                                # Find the stock info
                                stock_row = top_performers[top_performers["Ticker"] == ticker]
                                if not stock_row.empty:
                                    name = stock_row["Namn"].iloc[0] if "Namn" in stock_row.columns else ticker
                                    try:
                                        add_to_watchlist(ticker, name)
                                        added_count += 1
                                    except:
                                        pass  # Stock might already be in watchlist

                            if added_count > 0:
                                st.success(
                                    f"✅ Added {added_count} stock(s) to your watchlist!")
                            else:
                                st.info(
                                    "Selected stocks might already be in your watchlist.")

                else:
                    st.warning("No results to display after filtering.")

            # Show errors if any
            if error_results:
                with st.expander(f"❌ Failed Analyses ({len(error_results)} stocks)", expanded=False):
                    for error in error_results:
                        st.error(
                            f"**{error.get('ticker', 'Unknown')}**: {error.get('error_message', 'Unknown error')}")

    elif not selected_tickers:
        st.info(
            "👆 Select stocks to analyze using the options above, then click 'Run Batch Analysis'.")


if __name__ == "__main__":
    display_batch_analysis()
