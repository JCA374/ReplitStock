import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.subplots as sp
from datetime import datetime

from data.stock_data import StockDataFetcher
from data.db_manager import add_to_watchlist
from analysis.technical import calculate_all_indicators, generate_technical_signals
from analysis.fundamental import analyze_fundamentals
from analysis.strategy import ValueMomentumStrategy
from utils.ticker_mapping import normalize_ticker
from config import TIMEFRAMES, PERIOD_OPTIONS, STOCKHOLM_EXCHANGE_SUFFIX

def analyze_single_stock_optimized(ticker, strategy):
    """Optimized single stock analysis with bulk preloading"""
    
    # Preload data using bulk loader for consistency
    strategy.preload_data_bulk([ticker])
    
    # Now analyze (will use preloaded data)
    result = strategy.analyze_stock(ticker)
    return result

def display_single_stock_analysis():
    st.header("Single Stock Analysis")

    # Initialize StockDataFetcher
    data_fetcher = StockDataFetcher()

    # Check for automatic analysis from batch results
    auto_ticker = None
    show_auto_analysis_banner = False
    if 'analyze_ticker' in st.session_state:
        auto_ticker = st.session_state.analyze_ticker
        # Check if this is from auto_analyze trigger
        if 'auto_analyze' in st.session_state:
            show_auto_analysis_banner = True
            del st.session_state.auto_analyze
        
    # Show banner if this is from batch analysis
    if show_auto_analysis_banner and auto_ticker:
        st.markdown(f"""
        <div style="background-color: #28a745; color: white; padding: 12px; border-radius: 8px; text-align: center; margin-bottom: 20px; font-weight: bold;">
            🎯 Now analyzing <strong>{auto_ticker}</strong> from batch results
        </div>
        """, unsafe_allow_html=True)

    # Input for ticker symbol
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        # Pre-fill ticker input if coming from batch analysis
        default_value = auto_ticker if auto_ticker else ""
        ticker_input = st.text_input("Enter stock ticker:", value=default_value, key="single_ticker_input")

    with col2:
        timeframe = st.selectbox(
            "Timeframe:",
            options=list(TIMEFRAMES.keys()),
            key="single_timeframe"
        )

    with col3:
        period = st.selectbox(
            "Period:",
            options=list(PERIOD_OPTIONS.keys()),
            key="single_period"
        )

    # Convert selected options to API format
    timeframe_value = TIMEFRAMES[timeframe]
    period_value = PERIOD_OPTIONS[period]

    # When ticker is entered or auto-triggered, fetch and display data
    if ticker_input or auto_ticker:
        # Use auto_ticker if available, otherwise use manual input
        analysis_ticker = auto_ticker if auto_ticker else ticker_input
        # Normalize ticker (handle Swedish stocks)
        ticker = normalize_ticker(analysis_ticker)

        # Use optimized analysis with bulk preloading
        with st.spinner(f"Analyzing {ticker} with optimized bulk loading..."):
            # Initialize strategy
            strategy = ValueMomentumStrategy()
            
            # Use optimized single stock analysis
            analysis_result = analyze_single_stock_optimized(ticker, strategy)
            
            if analysis_result.get('error'):
                st.error(f"No data found for {ticker}. Please check the ticker symbol.")
                return

            # Extract data from analysis result
            stock_data = analysis_result.get('historical_data')
            fundamentals = {
                'pe_ratio': analysis_result.get('pe_ratio'),
                'profit_margin': analysis_result.get('profit_margin'),
                'revenue_growth': analysis_result.get('revenue_growth')
            }
            
            # Get stock info (fallback to data fetcher if not in result)
            try:
                stock_info = data_fetcher.get_stock_info(ticker)
            except:
                stock_info = {
                    'name': analysis_result.get('name', ticker),
                    'sector': 'N/A',
                    'industry': 'N/A',
                    'exchange': 'Stockholm',
                    'currency': 'SEK'
                }

            # Use signals from analysis result
            signals = {
                'tech_score': analysis_result.get('tech_score', 0),
                'above_ma40': analysis_result.get('above_ma40', False),
                'above_ma4': analysis_result.get('above_ma4', False),
                'rsi_above_50': analysis_result.get('rsi_above_50', False),
                'rsi_value': analysis_result.get('rsi'),
                'overall_signal': analysis_result.get('value_momentum_signal', 'HOLD').lower(),
                'signal_strength': analysis_result.get('tech_score', 0) / 100,
                'value_momentum_signal': analysis_result.get('value_momentum_signal', 'HOLD')
            }
            
            # Calculate technical indicators for chart display
            indicators = calculate_all_indicators(stock_data)
            
            # Analyze fundamentals for display
            fundamental_analysis = analyze_fundamentals(fundamentals)

        # Display stock header with company information
        st.subheader(f"{stock_info['name']} ({ticker})")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Sector", stock_info['sector'])

        with col2:
            st.metric("Industry", stock_info['industry'])

        with col3:
            st.metric("Exchange", stock_info['exchange'])

        with col4:
            # Add to watchlist button
            if st.button("Add to Watchlist"):
                success = add_to_watchlist(
                    ticker,
                    stock_info['name'],
                    stock_info['exchange'],
                    stock_info['sector']
                )

                if success:
                    st.success(f"Added {ticker} to watchlist")
                else:
                    st.info(f"{ticker} is already in your watchlist")

        # Get current price and change
        current_price = stock_data['close'].iloc[-1]
        prev_close = stock_data['close'].iloc[-2] if len(stock_data) > 1 else None

        if prev_close:
            price_change = current_price - prev_close
            price_change_pct = (price_change / prev_close) * 100

            # Display price metrics
            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "Current Price",
                    f"{current_price:.2f} {stock_info['currency']}",
                    f"{price_change:.2f} ({price_change_pct:.2f}%)",
                    delta_color="normal"
                )

            with col2:
                # Display technical signal
                signal = signals.get('overall_signal', 'neutral')
                signal_strength = signals.get('signal_strength', 0) * 100

                st.metric(
                    "Technical Signal",
                    signal.upper(),
                    f"Strength: {signal_strength:.1f}%",
                    delta_color="normal"
                )

        # Create tabs for different analysis views
        tab1, tab2, tab3 = st.tabs(["Price Chart", "Technical Analysis", "Fundamentals"])

        with tab1:
            # Main price chart
            fig = go.Figure()

            # Add candlestick chart
            fig.add_trace(go.Candlestick(
                x=stock_data.index,
                open=stock_data['open'],
                high=stock_data['high'],
                low=stock_data['low'],
                close=stock_data['close'],
                name="Price"
            ))

            # Add volume as a bar chart
            fig.add_trace(go.Bar(
                x=stock_data.index,
                y=stock_data['volume'],
                name="Volume",
                marker_color='rgba(0, 0, 255, 0.3)',
                opacity=0.3,
                yaxis="y2"
            ))

            # Add moving averages
            if 'sma_short' in indicators:
                fig.add_trace(go.Scatter(
                    x=stock_data.index,
                    y=indicators['sma_short'],
                    name=f"SMA (20)",
                    line=dict(color='blue', width=1)
                ))

            if 'sma_medium' in indicators:
                fig.add_trace(go.Scatter(
                    x=stock_data.index,
                    y=indicators['sma_medium'],
                    name=f"SMA (50)",
                    line=dict(color='orange', width=1)
                ))

            if 'sma_long' in indicators:
                fig.add_trace(go.Scatter(
                    x=stock_data.index,
                    y=indicators['sma_long'],
                    name=f"SMA (200)",
                    line=dict(color='red', width=1)
                ))

            # Set up secondary y-axis for volume
            fig.update_layout(
                title=f"{ticker} Price Chart",
                yaxis_title="Price",
                xaxis_title="Date",
                yaxis2=dict(
                    title=dict(text="Volume", font=dict(color="blue")),
                    tickfont=dict(color="blue"),
                    anchor="x",
                    overlaying="y",
                    side="right",
                    showgrid=False
                ),
                xaxis_rangeslider_visible=False,
                height=600
            )

            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            # Technical indicators tab

            # Create a figure with subplots
            fig = sp.make_subplots(
                rows=3, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.05,
                subplot_titles=("Price with Bollinger Bands", "RSI", "MACD"),
                row_heights=[0.5, 0.25, 0.25]
            )

            # Price and Bollinger Bands
            fig.add_trace(
                go.Candlestick(
                    x=stock_data.index,
                    open=stock_data['open'],
                    high=stock_data['high'],
                    low=stock_data['low'],
                    close=stock_data['close'],
                    name="Price"
                ),
                row=1, col=1
            )

            # Add Bollinger Bands
            if 'bollinger_middle' in indicators:
                fig.add_trace(
                    go.Scatter(
                        x=stock_data.index,
                        y=indicators['bollinger_middle'],
                        name="BB Middle",
                        line=dict(color='purple', width=1)
                    ),
                    row=1, col=1
                )

            if 'bollinger_upper' in indicators and 'bollinger_lower' in indicators:
                fig.add_trace(
                    go.Scatter(
                        x=stock_data.index,
                        y=indicators['bollinger_upper'],
                        name="BB Upper",
                        line=dict(color='teal', width=1)
                    ),
                    row=1, col=1
                )

                fig.add_trace(
                    go.Scatter(
                        x=stock_data.index,
                        y=indicators['bollinger_lower'],
                        name="BB Lower",
                        line=dict(color='teal', width=1)
                    ),
                    row=1, col=1
                )

            # Add RSI
            if 'rsi' in indicators:
                fig.add_trace(
                    go.Scatter(
                        x=stock_data.index,
                        y=indicators['rsi'],
                        name="RSI",
                        line=dict(color='orange', width=1)
                    ),
                    row=2, col=1
                )

                # Add RSI reference lines (30 and 70)
                fig.add_trace(
                    go.Scatter(
                        x=[stock_data.index[0], stock_data.index[-1]],
                        y=[30, 30],
                        name="RSI Oversold",
                        line=dict(color='green', width=1, dash='dash')
                    ),
                    row=2, col=1
                )

                fig.add_trace(
                    go.Scatter(
                        x=[stock_data.index[0], stock_data.index[-1]],
                        y=[70, 70],
                        name="RSI Overbought",
                        line=dict(color='red', width=1, dash='dash')
                    ),
                    row=2, col=1
                )

            # Add MACD
            if 'macd' in indicators and 'macd_signal' in indicators:
                fig.add_trace(
                    go.Scatter(
                        x=stock_data.index,
                        y=indicators['macd'],
                        name="MACD",
                        line=dict(color='blue', width=1)
                    ),
                    row=3, col=1
                )

                fig.add_trace(
                    go.Scatter(
                        x=stock_data.index,
                        y=indicators['macd_signal'],
                        name="MACD Signal",
                        line=dict(color='red', width=1)
                    ),
                    row=3, col=1
                )

                # Add MACD histogram
                if 'macd_histogram' in indicators:
                    colors = ['green' if val >= 0 else 'red' for val in indicators['macd_histogram']]

                    fig.add_trace(
                        go.Bar(
                            x=stock_data.index,
                            y=indicators['macd_histogram'],
                            name="MACD Histogram",
                            marker_color=colors
                        ),
                        row=3, col=1
                    )

            # Update layout
            fig.update_layout(
                height=800,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="center",
                    x=0.5
                ),
                xaxis_rangeslider_visible=False
            )

            st.plotly_chart(fig, use_container_width=True)

            # Display technical analysis summary
            st.subheader("Technical Analysis Summary")
            
            # Display tech score prominently
            tech_score = signals.get('tech_score', 0)
            st.metric("Tech Score", f"{tech_score}/100", help="Technical strength score based on multiple indicators")

            # Create columns for different indicator groups
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("**Moving Averages**")

                if 'price_above_sma_short' in signals:
                    status = "Above" if signals['price_above_sma_short'] else "Below"
                    st.markdown(f"- Price vs SMA (20): {status}")

                if 'price_above_sma_medium' in signals:
                    status = "Above" if signals['price_above_sma_medium'] else "Below"
                    st.markdown(f"- Price vs SMA (50): {status}")

                if 'price_above_sma_long' in signals:
                    status = "Above" if signals['price_above_sma_long'] else "Below"
                    st.markdown(f"- Price vs SMA (200): {status}")

                if 'sma_short_above_medium' in signals:
                    status = "Yes" if signals['sma_short_above_medium'] else "No"
                    st.markdown(f"- SMA (20) above SMA (50): {status}")

            with col2:
                st.markdown("**Momentum Indicators**")

                if 'rsi_value' in signals:
                    rsi_val = signals['rsi_value']
                    rsi_status = "Overbought" if signals.get('rsi_overbought') else "Oversold" if signals.get('rsi_oversold') else "Neutral"
                    st.markdown(f"- RSI: {rsi_val:.2f} ({rsi_status})")

                if 'macd_bullish_cross' in signals:
                    macd_status = "Bullish" if signals['macd_bullish_cross'] else "Bearish" if signals.get('macd_bearish_cross') else "Neutral"
                    st.markdown(f"- MACD: {macd_status}")

            with col3:
                st.markdown("**Price Patterns**")

                if 'price_pattern' in indicators:
                    pattern = indicators['price_pattern']

                    if pattern.get('higher_lows'):
                        st.markdown("- Higher Lows (Uptrend)")

                    if pattern.get('lower_highs'):
                        st.markdown("- Lower Highs (Downtrend)")

                    if pattern.get('near_52w_high'):
                        st.markdown("- Near 52-Week High")

                    if pattern.get('near_52w_low'):
                        st.markdown("- Near 52-Week Low")

                if 'breakout' in indicators:
                    breakout = indicators['breakout']

                    if breakout.get('breakout_up'):
                        st.markdown("- Upward Breakout Detected")

                    if breakout.get('breakout_down'):
                        st.markdown("- Downward Breakout Detected")

                    if breakout.get('volume_surge'):
                        st.markdown("- Volume Surge Detected")

        with tab3:
            # Fundamentals tab
            st.subheader("Fundamental Analysis")

            # Display overall fundamental verdict
            status = fundamental_analysis['overall']['status']
            description = fundamental_analysis['overall']['description']

            status_color = {
                'positive': 'green',
                'negative': 'red',
                'neutral': 'orange',
                'unknown': 'gray'
            }.get(status, 'gray')

            st.markdown(f"**Overall Assessment:** <span style='color:{status_color}'>{status.upper()}</span>", unsafe_allow_html=True)
            st.markdown(f"**{description}**")

            # Create columns for fundamental metrics
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Valuation Metrics**")

                metrics_table = {
                    "P/E Ratio": f"{fundamentals.get('pe_ratio', 'N/A'):.2f}" if fundamentals.get('pe_ratio') is not None else "N/A",
                    "Book Value": f"{fundamentals.get('book_value', 'N/A'):.2f}" if fundamentals.get('book_value') is not None else "N/A",
                    "Market Cap": f"{fundamentals.get('market_cap', 'N/A'):,.0f}" if fundamentals.get('market_cap') is not None else "N/A",
                    "Dividend Yield": f"{fundamentals.get('dividend_yield', 'N/A'):.2%}" if fundamentals.get('dividend_yield') is not None else "N/A"
                }

                metrics_df = pd.DataFrame(list(metrics_table.items()), columns=["Metric", "Value"])
                st.dataframe(metrics_df, hide_index=True)

                # Display P/E analysis
                pe_analysis = fundamental_analysis.get('pe_ratio', {})
                if pe_analysis.get('status') != 'unknown':
                    st.markdown(f"**P/E Analysis:** {pe_analysis.get('description', '')}")

            with col2:
                st.markdown("**Growth & Profitability**")

                growth_table = {
                    "Profit Margin": f"{fundamentals.get('profit_margin', 'N/A'):.2%}" if fundamentals.get('profit_margin') is not None else "N/A",
                    "Revenue Growth": f"{fundamentals.get('revenue_growth', 'N/A'):.2%}" if fundamentals.get('revenue_growth') is not None else "N/A",
                    "Earnings Growth": f"{fundamentals.get('earnings_growth', 'N/A'):.2%}" if fundamentals.get('earnings_growth') is not None else "N/A"
                }

                growth_df = pd.DataFrame(list(growth_table.items()), columns=["Metric", "Value"])
                st.dataframe(growth_df, hide_index=True)

                # Display profit margin analysis
                margin_analysis = fundamental_analysis.get('profit_margin', {})
                if margin_analysis.get('status') != 'unknown':
                    st.markdown(f"**Profit Margin Analysis:** {margin_analysis.get('description', '')}")

                # Display revenue growth analysis
                growth_analysis = fundamental_analysis.get('revenue_growth', {})
                if growth_analysis.get('status') != 'unknown':
                    st.markdown(f"**Revenue Growth Analysis:** {growth_analysis.get('description', '')}")
    else:
        # Show an example dashboard with stock photos
        st.info("Enter a stock ticker above to begin analysis")

        # Display a sample chart
        st.image("https://pixabay.com/get/g844714abae74a053749f7775bf14da4f908e79308bda609ea5be5d4af61b9c09f6a7c642255fabb084b47bc799362677abc8a791f8509c23e3cbecc600ef919b_1280.jpg", 
                caption="Example stock analysis dashboard")