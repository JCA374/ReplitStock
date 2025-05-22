import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# Import our database integration functions
from data.db_integration import (
    get_watchlist, get_all_cached_stocks, get_cached_stock_data,
    get_cached_fundamentals, get_all_fundamentals
)
from analysis.scanner import EnhancedScanner
from analysis.technical import calculate_all_indicators, generate_technical_signals
from analysis.fundamental import analyze_fundamentals
from config import SCANNER_CRITERIA

def display_enhanced_scanner():
    st.header("Enhanced Stock Scanner")
    st.write("Scan stocks based on combined database data with advanced ranking and filtering")

    # Sidebar for scanner configuration
    st.sidebar.header("Scanner Settings")

    # Select scan scope
    scan_scope = st.sidebar.radio(
        "Scan Scope:",
        ["All Database Stocks (No API)", "All Available Stocks", "Watchlist Only", "Small Cap", "Mid Cap", "Large Cap"],
        key="scanner_scope",
        help="'All Database Stocks' uses only cached data from databases without API calls"
    )

    # Get available stocks for information
    watchlist = get_watchlist()
    all_stocks = get_all_cached_stocks()

    # Show available stocks count
    if scan_scope == "Watchlist Only":
        st.sidebar.info(f"Watchlist contains {len(watchlist)} stocks")
    else:
        st.sidebar.info(f"Database contains {len(all_stocks)} stocks")

    # Database selection
    st.sidebar.subheader("Data Sources")
    use_supabase = st.sidebar.checkbox("Use Supabase", value=True)
    use_sqlite = st.sidebar.checkbox("Use SQLite", value=True)

    if not use_supabase and not use_sqlite:
        st.warning("At least one database source must be selected.")
        use_sqlite = True

    # Strategy Selection
    st.sidebar.subheader("Strategy")

    strategy_option = st.sidebar.radio(
        "Scanner Mode:",
        ["Value & Momentum Strategy", "Custom Criteria", "Combined Ranking"],
        key="scanner_strategy"
    )

    # Dictionary to store selected criteria
    selected_criteria = {}

    if strategy_option == "Value & Momentum Strategy":
        # Use the Value & Momentum Strategy
        selected_criteria["strategy"] = "value_momentum"

    # Custom filter options
    if strategy_option != "Value & Momentum Strategy":
        st.sidebar.subheader("Custom Criteria")

        # Technical criteria
        with st.sidebar.expander("Technical Filters", expanded=True):
            # Price vs moving averages
            price_sma_option = st.selectbox(
                "Price vs. SMA:",
                ["None", "Price Above SMA", "Price Below SMA"],
                key="scanner_price_sma"
            )

            if price_sma_option != "None":
                sma_period = st.selectbox(
                    "SMA Period:",
                    [20, 50, 200],
                    key="scanner_sma_period"
                )

                if price_sma_option == "Price Above SMA":
                    selected_criteria["price_above_sma"] = sma_period
                else:
                    selected_criteria["price_below_sma"] = sma_period

            # RSI Conditions
            rsi_option = st.selectbox(
                "RSI Condition:",
                ["None", "Overbought (RSI > 70)", "Oversold (RSI < 30)", "RSI > 50", "RSI < 50"],
                key="scanner_rsi"
            )

            if rsi_option == "Overbought (RSI > 70)":
                selected_criteria["rsi_overbought"] = True
            elif rsi_option == "Oversold (RSI < 30)":
                selected_criteria["rsi_oversold"] = True
            elif rsi_option == "RSI > 50":
                selected_criteria["rsi_above_50"] = True
            elif rsi_option == "RSI < 50":
                selected_criteria["rsi_below_50"] = True

            # MACD Signals
            macd_option = st.selectbox(
                "MACD Signal:",
                ["None", "Bullish Cross", "Bearish Cross"],
                key="scanner_macd"
            )

            if macd_option == "Bullish Cross":
                selected_criteria["macd_bullish"] = True
            elif macd_option == "Bearish Cross":
                selected_criteria["macd_bearish"] = True

            # Price levels
            price_level_option = st.selectbox(
                "Price Level:",
                ["None", "Near 52-Week High", "Near 52-Week Low"],
                key="scanner_price_level"
            )

            if price_level_option == "Near 52-Week High":
                selected_criteria["price_near_52w_high"] = True
            elif price_level_option == "Near 52-Week Low":
                selected_criteria["price_near_52w_low"] = True

            # Breakout detection
            breakout_option = st.checkbox("Recent Breakout", key="scanner_breakout")
            if breakout_option:
                selected_criteria["breakout"] = True

            # Minimum tech score
            min_tech_score = st.slider(
                "Minimum Tech Score:",
                0, 100, 0,
                key="scanner_min_tech_score"
            )

            if min_tech_score > 0:
                selected_criteria["min_tech_score"] = min_tech_score

        # Fundamental criteria
        with st.sidebar.expander("Fundamental Filters", expanded=True):
            # P/E Ratio
            pe_option = st.selectbox(
                "P/E Ratio:",
                ["None", "Below Value", "Above Value", "Between Values"],
                key="scanner_pe"
            )

            if pe_option == "Below Value":
                pe_value = st.slider(
                    "P/E Below:",
                    min_value=1.0,
                    max_value=50.0,
                    value=15.0,
                    step=0.5,
                    key="scanner_pe_below"
                )
                selected_criteria["pe_below"] = pe_value
            elif pe_option == "Above Value":
                pe_value = st.slider(
                    "P/E Above:",
                    min_value=1.0,
                    max_value=50.0,
                    value=20.0,
                    step=0.5,
                    key="scanner_pe_above"
                )
                selected_criteria["pe_above"] = pe_value
            elif pe_option == "Between Values":
                pe_min, pe_max = st.slider(
                    "P/E Range:",
                    min_value=1.0,
                    max_value=100.0,
                    value=(10.0, 30.0),
                    step=0.5,
                    key="scanner_pe_range"
                )
                selected_criteria["pe_above"] = pe_min
                selected_criteria["pe_below"] = pe_max

            # Profit Margin
            profit_margin_option = st.checkbox(
                "Minimum Profit Margin",
                key="scanner_profit_margin_check"
            )

            if profit_margin_option:
                profit_margin_value = st.slider(
                    "Profit Margin Above (%):",
                    min_value=0.0,
                    max_value=30.0,
                    value=10.0,
                    step=0.5,
                    key="scanner_profit_margin"
                )
                selected_criteria["profit_margin_above"] = profit_margin_value / 100

            # Revenue Growth
            revenue_growth_option = st.checkbox(
                "Minimum Revenue Growth",
                key="scanner_revenue_growth_check"
            )

            if revenue_growth_option:
                revenue_growth_value = st.slider(
                    "Revenue Growth Above (%):",
                    min_value=0.0,
                    max_value=50.0,
                    value=5.0,
                    step=0.5,
                    key="scanner_revenue_growth"
                )
                selected_criteria["revenue_growth_above"] = revenue_growth_value / 100

            # Profitability filter
            profitability_option = st.checkbox(
                "Profitable Companies Only",
                key="scanner_profitability"
            )

            if profitability_option:
                selected_criteria["is_profitable"] = True

            # Industry/Sector filter
            sectors_available = ["Technology", "Healthcare", "Financials", "Consumer Cyclical", 
                               "Consumer Defensive", "Industrials", "Basic Materials", 
                               "Energy", "Communication Services", "Utilities", "Real Estate"]

            selected_sectors = st.multiselect(
                "Filter by Sectors:",
                options=sectors_available,
                key="scanner_sectors"
            )

            if selected_sectors:
                selected_criteria["sectors"] = selected_sectors

    # Data source filter (separate from database selection)
    st.sidebar.subheader("Data Source Filter")
    data_sources = st.sidebar.multiselect(
        "Data Sources to Include:",
        ["yahoo", "alphavantage", "local", "combined", "supabase", "sqlite"],
        default=["yahoo", "alphavantage", "local", "combined", "supabase", "sqlite"],
        key="scanner_data_sources"
    )

    if data_sources:
        selected_criteria["data_sources"] = data_sources

    # Run Scanner button
    run_scanner = st.sidebar.button("Run Scanner", use_container_width=True, type="primary")

    # Initialize our enhanced scanner utility
    scanner = EnhancedScanner(use_supabase=use_supabase, use_sqlite=use_sqlite)

    # Main area for displaying results
    if run_scanner or ('scanner_results' in st.session_state and scan_scope == st.session_state.get('previous_scan_scope', '')):
        # Show criteria summary
        st.subheader("Scanning with the following criteria:")

        criteria_list = []

        for criterion, value in selected_criteria.items():
            display_name = SCANNER_CRITERIA.get(criterion, criterion.replace('_', ' ').title())

            if isinstance(value, bool):
                criteria_list.append(f"- {display_name}")
            else:
                criteria_list.append(f"- {display_name}: {value}")

        for item in criteria_list:
            st.write(item)

        # Determine which stocks to scan
        if scan_scope == "Watchlist Only":
            stock_list = [item['ticker'] for item in watchlist]
            scan_title = "Watchlist Stocks"
        elif scan_scope == "Small Cap":
            try:
                small_cap_df = pd.read_csv('csv/updated_small.csv')
                stock_list = small_cap_df['YahooTicker'].tolist()
                scan_title = "Small Cap Stocks"
            except Exception as e:
                st.error(f"Error loading Small Cap CSV: {e}")
                stock_list = []
                scan_title = "Stocks"
        elif scan_scope == "Mid Cap":
            try:
                mid_cap_df = pd.read_csv('csv/updated_mid.csv')
                stock_list = mid_cap_df['YahooTicker'].tolist()
                scan_title = "Mid Cap Stocks"
            except Exception as e:
                st.error(f"Error loading Mid Cap CSV: {e}")
                stock_list = []
                scan_title = "Stocks"
        elif scan_scope == "Large Cap":
            try:
                large_cap_df = pd.read_csv('csv/updated_large.csv')
                stock_list = large_cap_df['YahooTicker'].tolist()
                scan_title = "Large Cap Stocks"
            except Exception as e:
                st.error(f"Error loading Large Cap CSV: {e}")
                stock_list = []
                scan_title = "Stocks"
        elif scan_scope == "All Database Stocks (No API)":
            # Only scan stocks that exist in database, no API calls
            stock_list = set()

            # Get stocks from SQLite
            if use_sqlite:
                sqlite_stocks = get_all_cached_stocks()
                stock_list.update(sqlite_stocks)

            # Get stocks from Supabase
            if use_supabase:
                from data.supabase_client import get_supabase_db
                supabase_db = get_supabase_db()

                if supabase_db.is_connected():
                    supabase_stocks = supabase_db.get_all_cached_stocks()
                    stock_list.update(supabase_stocks)

            # Convert to list
            stock_list = list(stock_list)
            scan_title = "Database Stocks (No API)"

            # Show count of stocks being scanned
            st.info(f"Scanning {len(stock_list)} stocks found in database(s)")
        else:
            # All stocks - may trigger API calls
            stock_list = None
            scan_title = "All Stocks"

        # Run the scanner if needed
        if run_scanner:
            progress_container = st.container()
            progress_bar = progress_container.progress(0)
            status_text = progress_container.empty()

            # Define progress callback
            def update_progress(progress, message):
                progress_bar.progress(progress)
                status_text.info(message)

            # Run the scan with progress updates
            with st.spinner(f"Scanning {scan_title}..."):
                results = scanner.scan_stocks(selected_criteria, stock_list, update_progress)

                # Store results and settings in session state
                st.session_state.scanner_results = results
                st.session_state.previous_scan_scope = scan_scope

            # Clear progress indicators
            progress_container.empty()
        else:
            # Use cached results
            results = st.session_state.scanner_results

        # Display results
        if results:
            st.subheader(f"Found {len(results)} matching stocks")

            # Create a DataFrame for display
            display_df = pd.DataFrame(results)

            # Format numeric columns
            if 'pe_ratio' in display_df.columns:
                display_df['pe_ratio'] = display_df['pe_ratio'].apply(
                    lambda x: f"{x:.2f}" if pd.notna(x) else "N/A"
                )

            if 'profit_margin' in display_df.columns:
                display_df['profit_margin'] = display_df['profit_margin'].apply(
                    lambda x: f"{x:.2%}" if pd.notna(x) else "N/A"
                )

            if 'revenue_growth' in display_df.columns:
                display_df['revenue_growth'] = display_df['revenue_growth'].apply(
                    lambda x: f"{x:.2%}" if pd.notna(x) else "N/A"
                )

            if 'price' in display_df.columns:
                display_df['price'] = display_df['price'].apply(
                    lambda x: f"{x:.2f}" if pd.notna(x) else "N/A"
                )

            if 'tech_score' in display_df.columns:
                display_df['tech_score'] = display_df['tech_score'].apply(
                    lambda x: f"{int(x)}" if pd.notna(x) else "N/A"
                )

            if 'overall_score' in display_df.columns:
                display_df['overall_score'] = display_df['overall_score'].apply(
                    lambda x: f"{x:.1f}" if pd.notna(x) else "N/A"
                )

            # Determine columns to display based on strategy
            if strategy_option == "Value & Momentum Strategy":
                columns_to_display = ['ticker', 'name', 'price', 'tech_score', 'signal', 
                                     'pe_ratio', 'profit_margin', 'revenue_growth',
                                     'fundamental_pass', 'data_source']
                rename_map = {
                    'ticker': 'Ticker',
                    'name': 'Name',
                    'price': 'Price',
                    'tech_score': 'Tech Score',
                    'signal': 'Signal',
                    'pe_ratio': 'P/E Ratio',
                    'profit_margin': 'Profit Margin',
                    'revenue_growth': 'Revenue Growth',
                    'fundamental_pass': 'Fundamental Pass',
                    'data_source': 'Data Source'
                }
            elif strategy_option == "Combined Ranking":
                columns_to_display = ['rank', 'ticker', 'name', 'price', 'overall_score', 
                                     'tech_score', 'signal', 'pe_ratio', 'profit_margin', 
                                     'is_profitable', 'data_source']
                rename_map = {
                    'rank': 'Rank',
                    'ticker': 'Ticker',
                    'name': 'Name',
                    'price': 'Price',
                    'overall_score': 'Overall Score',
                    'tech_score': 'Tech Score',
                    'signal': 'Signal',
                    'pe_ratio': 'P/E Ratio',
                    'profit_margin': 'Profit Margin',
                    'is_profitable': 'Profitable',
                    'data_source': 'Data Source'
                }
            else:
                # Custom criteria
                columns_to_display = ['ticker', 'name', 'price', 'tech_score', 'signal',
                                     'pe_ratio', 'profit_margin', 'revenue_growth', 
                                     'is_profitable', 'data_source']
                rename_map = {
                    'ticker': 'Ticker',
                    'name': 'Name',
                    'price': 'Price',
                    'tech_score': 'Tech Score',
                    'signal': 'Signal',
                    'pe_ratio': 'P/E Ratio',
                    'profit_margin': 'Profit Margin',
                    'revenue_growth': 'Revenue Growth',
                    'is_profitable': 'Profitable',
                    'data_source': 'Data Source'
                }

            # Filter and rename columns
            display_columns = [col for col in columns_to_display if col in display_df.columns]
            final_df = display_df[display_columns].rename(columns=rename_map)

            # Display the results table
            st.dataframe(final_df, use_container_width=True)

            # Download button for results
            csv_data = display_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Results as CSV",
                data=csv_data,
                file_name="enhanced_stock_scanner_results.csv",
                mime="text/csv"
            )

            # Visualization of results if enough data
            if len(results) > 0:
                st.subheader("Visualization")

                # Choose visualization type
                viz_type = st.radio(
                    "Select visualization:",
                    ["Tech Score Distribution", "Technical vs. Fundamental Scores", "Sector Breakdown"],
                    key="viz_type"
                )

                if viz_type == "Tech Score Distribution":
                    # Create histogram of tech scores
                    fig = go.Figure()

                    fig.add_trace(go.Histogram(
                        x=display_df['tech_score'].astype(float),
                        nbinsx=20,
                        marker_color='royalblue',
                        opacity=0.75,
                        name='Tech Score'
                    ))

                    fig.update_layout(
                        title="Distribution of Technical Scores",
                        xaxis_title="Technical Score",
                        yaxis_title="Number of Stocks",
                        bargap=0.1,
                        template="plotly_white"
                    )

                    st.plotly_chart(fig, use_container_width=True)

                elif viz_type == "Technical vs. Fundamental Scores":
                    # Create scatter plot
                    if 'tech_score' in display_df.columns and 'pe_ratio' in display_df.columns:
                        # Convert PE ratio to numeric for plotting
                        numeric_pe = pd.to_numeric(display_df['pe_ratio'].str.replace('N/A', '').str.strip(), errors='coerce')

                        fig = go.Figure()

                        fig.add_trace(go.Scatter(
                            x=display_df['tech_score'].astype(float),
                            y=numeric_pe,
                            mode='markers',
                            marker=dict(
                                size=10,
                                color=display_df['tech_score'].astype(float),
                                colorscale='Viridis',
                                showscale=True,
                                colorbar=dict(title="Tech Score")
                            ),
                            text=display_df['ticker'],
                            hovertemplate=
                            '<b>%{text}</b><br>' +
                            'Tech Score: %{x:.1f}<br>' +
                            'P/E Ratio: %{y:.2f}<br>',
                            name='Stocks'
                        ))

                        fig.update_layout(
                            title="Technical Score vs. P/E Ratio",
                            xaxis_title="Technical Score",
                            yaxis_title="P/E Ratio",
                            template="plotly_white"
                        )

                        # Add shape to highlight the Value & Momentum Zone
                        fig.update_layout(
                            shapes=[
                                dict(
                                    type="rect",
                                    x0=70, y0=0,
                                    x1=100, y1=30,
                                    line=dict(color="rgba(0,255,0,0.2)"),
                                    fillcolor="rgba(0,255,0,0.1)",
                                    layer="below"
                                )
                            ],
                            annotations=[
                                dict(
                                    x=85, y=15,
                                    text="Value & Momentum Zone",
                                    showarrow=False,
                                    font=dict(size=12, color="green")
                                )
                            ]
                        )

                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Insufficient data for Technical vs. Fundamental scatter plot.")

                elif viz_type == "Sector Breakdown":
                    # Create sector pie chart
                    if 'sector' in display_df.columns:
                        # Count stocks by sector
                        sector_counts = display_df['sector'].value_counts()

                        # Create a color scale
                        colors = px.colors.qualitative.Plotly

                        fig = go.Figure(data=[go.Pie(
                            labels=sector_counts.index,
                            values=sector_counts.values,
                            hole=.3,
                            textinfo='label+percent',
                            marker=dict(colors=colors[:len(sector_counts)])
                        )])

                        fig.update_layout(
                            title="Sector Breakdown of Selected Stocks",
                            template="plotly_white"
                        )

                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Sector data is not available for visualization.")

        else:
            st.info("No stocks match the selected criteria. Try adjusting your filters.")

    else:
        # Show instructions when no scan has been run
        st.info("Configure your scan criteria using the sidebar, then click 'Run Scanner'")

        # Explanation of scanner modes
        st.subheader("Scanner Modes")

        # Value & Momentum Strategy
        st.markdown("**Value & Momentum Strategy**")
        st.markdown("""
        This strategy combines technical momentum with fundamental quality to find stocks that are both trending up 
        and fundamentally sound. The approach avoids both "value traps" (cheap stocks getting cheaper) 
        and momentum chasing without fundamental backing.

        **Key components:**
        - **Primary Trend**: Uses the 40-week moving average (MA40) as the primary trend indicator
        - **Short-Term Momentum**: Uses the 4-week moving average (MA4) for recent price action
        - **RSI Momentum**: Measures the strength of the price movement (RSI > 50 is bullish)
        - **Relative Strength**: Proximity to 52-week highs indicates market leadership
        - **Fundamental Quality**: Ensures the company is profitable with reasonable valuation
        """)

        # Custom Criteria
        st.markdown("**Custom Criteria**")
        st.markdown("""
        Build your own screening strategy by combining both technical and fundamental factors.
        Select from a wide range of filters including moving averages, RSI conditions, P/E ratios,
        profit margins, and more.
        """)

        # Combined Ranking
        st.markdown("**Combined Ranking**")
        st.markdown("""
        This mode ranks stocks based on a weighted scoring system that balances technical momentum
        and fundamental factors. The scoring system assigns:
        - 60% weight to technical factors (tech score, trend, momentum)
        - 40% weight to fundamental factors (profitability, valuation, growth)

        Each stock receives an Overall Score from 0-100, with higher scores indicating stronger 
        combined technical and fundamental characteristics.
        """)

        # Database integration
        st.subheader("Multi-Database Integration")
        st.markdown("""
        The Enhanced Scanner intelligently combines data from both Supabase and SQLite databases,
        providing the most comprehensive view of your stocks. When data is missing from one source,
        it automatically looks for it in the other database, ensuring maximum data coverage.

        Use the Database Selection options to control which data sources to include in your scan.
        """)
def display_batch_analysis():
    st.header("Batch Analysis")
    st.write("Analyze a list of stocks from our database(s)")

    # Input stock tickers
    stock_input = st.text_input("Enter stock tickers separated by commas (e.g., AAPL, MSFT, GOOG):", "")
    tickers = [s.strip().upper() for s in stock_input.split(',') if s.strip()]

    if tickers:
        st.subheader(f"Analyzing {len(tickers)} stocks: {', '.join(tickers)}")

        # Data sources selection
        st.subheader("Data Sources")
        use_supabase = st.checkbox("Use Supabase", value=True)
        use_sqlite = st.checkbox("Use SQLite", value=True)

        if not use_supabase and not use_sqlite:
            st.warning("At least one database source must be selected.")

        # Strategy Selection
        st.subheader("Strategy")
        strategy_option = st.selectbox(
            "Analysis Mode:",
            ["Technical Analysis", "Fundamental Analysis", "Combined Analysis"]
        )

        # Initialize our enhanced scanner utility
        scanner = EnhancedScanner(use_supabase=use_supabase, use_sqlite=use_sqlite)

        # Choose timeframe
        from analysis.technical import TIMEFRAMES

        # Analysis parameters
        col1, col2, col3 = st.columns(3)

        with col1:
            timeframe = st.selectbox(
                "Timeframe:",
                options=list(TIMEFRAMES.keys()),
                key="batch_timeframe"
            )

        database_only = st.checkbox("Use only database data (no API calls)", value=False)


        # Analyze
        if st.button("Analyze"):
            # Strategy Implementation
            if strategy_option == "Technical Analysis":
                from analysis.technical import TechnicalAnalysisStrategy
                strategy = TechnicalAnalysisStrategy(scanner.supabase_db, scanner.sqlite_db, timeframe)
            elif strategy_option == "Fundamental Analysis":
                from analysis.fundamental import FundamentalAnalysisStrategy
                strategy = FundamentalAnalysisStrategy(scanner.supabase_db, scanner.sqlite_db)
            else:
                from analysis.combined import CombinedAnalysisStrategy
                strategy = CombinedAnalysisStrategy(scanner.supabase_db, scanner.sqlite_db, timeframe)

            # Progress bar setup
            progress_container = st.container()
            progress_bar = progress_container.progress(0)
            status_text = progress_container.empty()

            # Define progress callback
            def update_progress(progress, message):
                progress_bar.progress(progress)
                status_text.info(message)

            # Execute the batch analysis
            with st.spinner(f"Analyzing {len(tickers)} stocks..."):
                results = strategy.batch_analyze(tickers, update_progress, database_only=database_only)

                # Clear progress indicators
                progress_container.empty()

            # Display results
            if results:
                st.subheader("Analysis Results")

                # Create a DataFrame for display
                display_df = pd.DataFrame(results)

                # Determine columns to display based on strategy
                if strategy_option == "Technical Analysis":
                    columns_to_display = ['ticker', 'name', 'price', 'signal', 'data_source']
                    rename_map = {
                        'ticker': 'Ticker',
                        'name': 'Name',
                        'price': 'Price',
                        'signal': 'Signal',
                        'data_source': 'Data Source'
                    }
                elif strategy_option == "Fundamental Analysis":
                    columns_to_display = ['ticker', 'name', 'pe_ratio', 'profit_margin', 'revenue_growth', 'data_source']
                    rename_map = {
                        'ticker': 'Ticker',
                        'name': 'Name',
                        'pe_ratio': 'P/E Ratio',
                        'profit_margin': 'Profit Margin',
                        'revenue_growth': 'Revenue Growth',
                        'data_source': 'Data Source'
                    }
                else:
                    # Combined analysis
                    columns_to_display = ['ticker', 'name', 'price', 'signal', 'pe_ratio', 'profit_margin', 'revenue_growth', 'data_source']
                    rename_map = {
                        'ticker': 'Ticker',
                        'name': 'Name',
                        'price': 'Price',
                        'signal': 'Signal',
                        'pe_ratio': 'P/E Ratio',
                        'profit_margin': 'Profit Margin',
                        'revenue_growth': 'Revenue Growth',
                        'data_source': 'Data Source'
                    }

                # Format numeric columns
                if 'pe_ratio' in display_df.columns:
                    display_df['pe_ratio'] = display_df['pe_ratio'].apply(
                        lambda x: f"{x:.2f}" if pd.notna(x) else "N/A"
                    )

                if 'profit_margin' in display_df.columns:
                    display_df['profit_margin'] = display_df['profit_margin'].apply(
                        lambda x: f"{x:.2%}" if pd.notna(x) else "N/A"
                    )

                if 'revenue_growth' in display_df.columns:
                    display_df['revenue_growth'] = display_df['revenue_growth'].apply(
                        lambda x: f"{x:.2%}" if pd.notna(x) else "N/A"
                    )

                if 'price' in display_df.columns:
                    display_df['price'] = display_df['price'].apply(
                        lambda x: f"{x:.2f}" if pd.notna(x) else "N/A"
                    )

                # Filter and rename columns
                display_columns = [col for col in columns_to_display if col in display_df.columns]
                final_df = display_df[display_columns].rename(columns=rename_map)

                # Display the results table
                st.dataframe(final_df, use_container_width=True)

                # Download button for results
                csv_data = display_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Results as CSV",
                    data=csv_data,
                    file_name="batch_analysis_results.csv",
                    mime="text/csv"
                )
            else:
                st.info("No results to display.")