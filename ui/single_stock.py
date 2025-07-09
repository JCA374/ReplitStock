import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.subplots as sp
from datetime import datetime
import numpy as np

from data.stock_data import StockDataFetcher
from data.db_manager import add_to_watchlist
from analysis.technical import calculate_all_indicators, generate_technical_signals
from analysis.fundamental import analyze_fundamentals
from analysis.strategy import ValueMomentumStrategy
from utils.ticker_mapping import normalize_ticker
from config import TIMEFRAMES, PERIOD_OPTIONS, STOCKHOLM_EXCHANGE_SUFFIX

def display_single_stock_analysis():
    # Mobile-responsive CSS
    st.markdown("""
    <style>
        /* Mobile-friendly adjustments */
        @media (max-width: 768px) {
            /* Stacked metrics on mobile */
            div[data-testid="metric-container"] {
                padding: 0.5rem;
            }

            /* Responsive charts */
            .js-plotly-plot {
                max-width: 100%;
                overflow-x: auto;
            }

            /* Compact buttons */
            .stButton > button {
                padding: 0.25rem 0.5rem;
                font-size: 0.875rem;
            }

            /* Responsive tables */
            .dataframe {
                font-size: 0.75rem;
            }
        }

        /* Enhanced metric cards */
        div[data-testid="metric-container"] {
            background-color: rgba(28, 131, 225, 0.1);
            border-radius: 0.5rem;
            padding: 1rem;
            border: 1px solid rgba(28, 131, 225, 0.2);
            transition: all 0.3s ease;
        }

        div[data-testid="metric-container"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        /* Signal badges */
        .signal-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 1rem;
            font-weight: bold;
            font-size: 0.875rem;
            margin: 0.25rem;
        }

        .signal-buy {
            background-color: #28a745;
            color: white;
        }

        .signal-sell {
            background-color: #dc3545;
            color: white;
        }

        .signal-hold {
            background-color: #ffc107;
            color: black;
        }
    </style>
    """, unsafe_allow_html=True)
    
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

        # Fetch stock data
        with st.spinner(f"Fetching data for {ticker}..."):
            stock_data = data_fetcher.get_stock_data(ticker, timeframe_value, period_value)

            if stock_data.empty:
                st.error(f"No data found for {ticker}. Please check the ticker symbol.")
                return

            # Get stock info
            stock_info = data_fetcher.get_stock_info(ticker)

            # Get fundamentals
            fundamentals = data_fetcher.get_fundamentals(ticker)

            # Calculate technical indicators
            indicators = calculate_all_indicators(stock_data)

            # Generate signals
            signals = generate_technical_signals(indicators)

            # Calculate tech score using strategy's method for consistency
            strategy = ValueMomentumStrategy()
            tech_score = strategy.calculate_tech_score(signals)
            signals['tech_score'] = tech_score

            # Analyze fundamentals
            fundamental_analysis = analyze_fundamentals(fundamentals)
            
            # Calculate Value & Momentum signal for consistency with batch analysis
            fundamental_pass = fundamental_analysis['overall'].get('value_momentum_pass', False)
            
            if tech_score >= 70 and fundamental_pass:
                value_momentum_signal = "BUY"
            elif tech_score < 40 or not signals.get('above_ma40', False):
                value_momentum_signal = "SELL"
            else:
                value_momentum_signal = "HOLD"
            
            # Update signals with consistent values
            signals['overall_signal'] = value_momentum_signal.lower()
            signals['signal_strength'] = tech_score / 100
            signals['value_momentum_signal'] = value_momentum_signal

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

        # Quick action toolbar
        st.markdown("---")
        quick_col1, quick_col2, quick_col3, quick_col4, quick_col5 = st.columns(5)

        with quick_col1:
            if st.button("🔄 Refresh Data", help="Fetch latest market data"):
                # Clear cache for this ticker
                st.session_state[f'cache_{ticker}'] = None
                st.rerun()

        with quick_col2:
            if st.button("📋 Compare", help="Add to comparison list"):
                if 'comparison_list' not in st.session_state:
                    st.session_state.comparison_list = []
                if ticker not in st.session_state.comparison_list:
                    st.session_state.comparison_list.append(ticker)
                    st.success(f"Added {ticker} to comparison")

        with quick_col3:
            if st.button("📰 News", help="Show latest news"):
                st.session_state[f'show_news_{ticker}'] = not st.session_state.get(f'show_news_{ticker}', False)

        with quick_col4:
            if st.button("📈 Similar", help="Find similar stocks"):
                st.session_state[f'show_similar_{ticker}'] = True

        with quick_col5:
            if st.button("🎯 Set Alert", help="Set price alert"):
                st.session_state[f'show_alert_{ticker}'] = True

        # Get current price and change
        current_price = stock_data['close'].iloc[-1]
        prev_close = stock_data['close'].iloc[-2] if len(stock_data) > 1 else None

        if prev_close:
            price_change = current_price - prev_close
            price_change_pct = (price_change / prev_close) * 100

            # Quick Stats Card
            with st.container():
                st.markdown("""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            color: white; padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1rem;">
                    <h3 style="margin: 0; color: white;">Quick Analysis Summary</h3>
                </div>
                """, unsafe_allow_html=True)

                quick_stats_cols = st.columns(5)

                with quick_stats_cols[0]:
                    st.markdown(f"""
                    <div style="text-align: center;">
                        <h4>${current_price:.2f}</h4>
                        <p style="color: {'green' if price_change > 0 else 'red'};">
                            {'+' if price_change > 0 else ''}{price_change_pct:.2f}%
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                with quick_stats_cols[1]:
                    pe_ratio = fundamentals.get('pe_ratio', 'N/A')
                    pe_display = f"{pe_ratio:.1f}" if isinstance(pe_ratio, (int, float)) else "N/A"
                    st.markdown(f"""
                    <div style="text-align: center;">
                        <h4>P/E: {pe_display}</h4>
                        <p>Valuation</p>
                    </div>
                    """, unsafe_allow_html=True)

                with quick_stats_cols[2]:
                    volume_avg = stock_data['volume'].mean()
                    volume_today = stock_data['volume'].iloc[-1]
                    volume_ratio = volume_today / volume_avg if volume_avg > 0 else 0
                    st.markdown(f"""
                    <div style="text-align: center;">
                        <h4>{volume_ratio:.1f}x</h4>
                        <p>Vol vs Avg</p>
                    </div>
                    """, unsafe_allow_html=True)

                with quick_stats_cols[3]:
                    fifty_two_high = stock_data['high'].rolling(252).max().iloc[-1]
                    distance_from_high = ((fifty_two_high - current_price) / fifty_two_high) * 100
                    st.markdown(f"""
                    <div style="text-align: center;">
                        <h4>-{distance_from_high:.1f}%</h4>
                        <p>From 52W High</p>
                    </div>
                    """, unsafe_allow_html=True)

                with quick_stats_cols[4]:
                    volatility = stock_data['close'].pct_change().std() * np.sqrt(252) * 100
                    st.markdown(f"""
                    <div style="text-align: center;">
                        <h4>{volatility:.1f}%</h4>
                        <p>Annual Vol</p>
                    </div>
                    """, unsafe_allow_html=True)

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
            # Enhanced interactive chart with drawing tools
            def create_interactive_chart(stock_data, ticker, indicators):
                fig = go.Figure()

                # Candlestick chart
                fig.add_trace(go.Candlestick(
                    x=stock_data.index,
                    open=stock_data['open'],
                    high=stock_data['high'],
                    low=stock_data['low'],
                    close=stock_data['close'],
                    name='Price',
                    increasing_line_color='green',
                    decreasing_line_color='red'
                ))

                # Add volume with better visibility
                fig.add_trace(go.Bar(
                    x=stock_data.index,
                    y=stock_data['volume'],
                    name='Volume',
                    yaxis='y2',
                    marker_color='lightblue',
                    opacity=0.3
                ))

                # Add moving averages with better styling
                for ma_period, color in [(20, 'orange'), (50, 'blue'), (200, 'purple')]:
                    if ma_period == 20:
                        ma_key = 'sma_short'
                    elif ma_period == 50:
                        ma_key = 'sma_medium'
                    elif ma_period == 200:
                        ma_key = 'sma_long'
                    
                    if ma_key in indicators:
                        fig.add_trace(go.Scatter(
                            x=stock_data.index,
                            y=indicators[ma_key],
                            mode='lines',
                            name=f'MA{ma_period}',
                            line=dict(color=color, width=2),
                            hovertemplate=f'MA{ma_period}: %{{y:.2f}}<br>Date: %{{x}}'
                        ))

                # Enhanced layout with dark theme option
                fig.update_layout(
                    title=f'{ticker} - Interactive Price Analysis',
                    yaxis=dict(title='Price', side='left'),
                    yaxis2=dict(title='Volume', overlaying='y', side='right'),
                    xaxis=dict(
                        rangeselector=dict(
                            buttons=list([
                                dict(count=1, label="1D", step="day", stepmode="backward"),
                                dict(count=5, label="5D", step="day", stepmode="backward"),
                                dict(count=1, label="1M", step="month", stepmode="backward"),
                                dict(count=3, label="3M", step="month", stepmode="backward"),
                                dict(count=6, label="6M", step="month", stepmode="backward"),
                                dict(count=1, label="1Y", step="year", stepmode="backward"),
                                dict(step="all", label="All")
                            ])
                        ),
                        rangeslider=dict(visible=True),
                        type="date"
                    ),
                    height=600,
                    hovermode='x unified',
                    dragmode='pan'  # Enable panning by default
                )

                # Add modebar with drawing tools
                config = {
                    'modeBarButtonsToAdd': [
                        'drawline',
                        'drawopenpath',
                        'drawclosedpath',
                        'drawcircle',
                        'drawrect',
                        'eraseshape'
                    ],
                    'displaylogo': False,
                    'displayModeBar': True
                }

                return fig, config

            # Use the enhanced chart
            fig, config = create_interactive_chart(stock_data, ticker, indicators)
            st.plotly_chart(fig, use_container_width=True, config=config)

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

            # Signal Dashboard
            st.subheader("📊 Live Signal Dashboard")

            # Create metric cards for key signals
            dash_col1, dash_col2, dash_col3, dash_col4 = st.columns(4)

            with dash_col1:
                tech_score = signals.get('tech_score', 0)
                delta_color = "normal" if tech_score >= 50 else "inverse"
                st.metric(
                    "Technical Score",
                    f"{tech_score}/100",
                    delta=f"{tech_score - 50} vs neutral",
                    delta_color=delta_color
                )

            with dash_col2:
                rsi_value = indicators.get('rsi', [0])[-1] if 'rsi' in indicators else 0
                rsi_signal = "🟢 Bullish" if rsi_value > 50 else "🔴 Bearish"
                st.metric("RSI Signal", rsi_signal, f"{rsi_value:.1f}")

            with dash_col3:
                ma_signal = "🟢" if signals.get('above_ma40') else "🔴"
                st.metric("Trend", f"{ma_signal} MA40", 
                          "Above" if signals.get('above_ma40') else "Below")

            with dash_col4:
                vm_signal = signals.get('value_momentum_signal', 'HOLD')
                signal_color = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}.get(vm_signal, "⚪")
                st.metric("V&M Signal", f"{signal_color} {vm_signal}")

            # Interactive signal explanation
            with st.expander("🎯 Understanding the Signals", expanded=False):
                st.markdown("""
                ### Signal Interpretation Guide

                **Technical Score (0-100)**
                - 70+ = Strong Buy Signal
                - 50-70 = Neutral/Hold
                - Below 50 = Caution/Sell Signal

                **RSI (Relative Strength Index)**
                - Above 70 = Overbought (potential reversal)
                - 50-70 = Bullish momentum
                - 30-50 = Bearish momentum
                - Below 30 = Oversold (potential bounce)

                **Trend (MA40)**
                - Price above 40-day MA = Uptrend
                - Price below 40-day MA = Downtrend

                **V&M Signal (Value & Momentum)**
                - Combines technical and fundamental analysis
                - BUY = Both technical and fundamentals are strong
                - HOLD = Mixed signals
                - SELL = Weak technical or fundamental indicators
                """)

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

        # Stock Comparison Feature
        if st.session_state.get('comparison_list'):
            st.markdown("---")
            st.subheader("📊 Stock Comparison")

            comparison_tickers = st.multiselect(
                "Compare with:",
                options=st.session_state.comparison_list,
                default=st.session_state.comparison_list[:3]  # Max 3 for clarity
            )

            if comparison_tickers:
                # Fetch comparison data
                comparison_data = {}
                for comp_ticker in comparison_tickers:
                    comp_data = data_fetcher.get_stock_data(comp_ticker, timeframe_value, period_value)
                    if not comp_data.empty:
                        comparison_data[comp_ticker] = comp_data

                # Normalized price comparison
                fig_comp = go.Figure()

                for comp_ticker, comp_data in comparison_data.items():
                    # Normalize to percentage change
                    normalized = (comp_data['close'] / comp_data['close'].iloc[0] - 1) * 100
                    fig_comp.add_trace(go.Scatter(
                        x=comp_data.index,
                        y=normalized,
                        mode='lines',
                        name=comp_ticker,
                        hovertemplate=f'{comp_ticker}: %{{y:.2f}}%<br>Date: %{{x}}'
                    ))

                # Add current stock
                normalized_current = (stock_data['close'] / stock_data['close'].iloc[0] - 1) * 100
                fig_comp.add_trace(go.Scatter(
                    x=stock_data.index,
                    y=normalized_current,
                    mode='lines',
                    name=f"{ticker} (Current)",
                    line=dict(width=3),
                    hovertemplate=f'{ticker}: %{{y:.2f}}%<br>Date: %{{x}}'
                ))

                fig_comp.update_layout(
                    title="Relative Performance Comparison (%)",
                    yaxis_title="Percentage Change",
                    hovermode='x unified',
                    height=400
                )

                st.plotly_chart(fig_comp, use_container_width=True)

        # Price Alert Setting
        if st.session_state.get(f'show_alert_{ticker}'):
            with st.form(f"alert_form_{ticker}"):
                st.subheader("🎯 Set Price Alert")

                alert_col1, alert_col2 = st.columns(2)

                with alert_col1:
                    alert_type = st.selectbox(
                        "Alert Type",
                        ["Price Above", "Price Below", "% Change", "Volume Spike"]
                    )

                with alert_col2:
                    if alert_type in ["Price Above", "Price Below"]:
                        alert_value = st.number_input(
                            "Target Price",
                            value=float(current_price),
                            min_value=0.0,
                            step=0.01
                        )
                    elif alert_type == "% Change":
                        alert_value = st.number_input(
                            "Percentage Change",
                            value=5.0,
                            min_value=0.0,
                            max_value=100.0,
                            step=0.5
                        )
                    else:  # Volume Spike
                        alert_value = st.number_input(
                            "Volume Multiplier",
                            value=2.0,
                            min_value=1.0,
                            step=0.1
                        )

                alert_note = st.text_area("Note (optional)", height=60)

                if st.form_submit_button("Set Alert"):
                    # Store alert in session state (in production, save to DB)
                    if 'alerts' not in st.session_state:
                        st.session_state.alerts = []

                    st.session_state.alerts.append({
                        'ticker': ticker,
                        'type': alert_type,
                        'value': alert_value,
                        'note': alert_note,
                        'created': datetime.now()
                    })

                    st.success(f"Alert set for {ticker}: {alert_type} {alert_value}")
                    st.session_state[f'show_alert_{ticker}'] = False
                    st.rerun()
    else:
        # Show an example dashboard with stock photos
        st.info("Enter a stock ticker above to begin analysis")

        # Display a sample chart
        st.image("https://pixabay.com/get/g844714abae74a053749f7775bf14da4f908e79308bda609ea5be5d4af61b9c09f6a7c642255fabb084b47bc799362677abc8a791f8509c23e3cbecc600ef919b_1280.jpg", 
                caption="Example stock analysis dashboard")