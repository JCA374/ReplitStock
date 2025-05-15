import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data.db_manager import get_watchlist, add_to_watchlist, remove_from_watchlist
from data.stock_data import StockDataFetcher
from analysis.technical import calculate_all_indicators, generate_technical_signals
from analysis.fundamental import analyze_fundamentals
from utils.ticker_mapping import normalize_ticker

def display_watchlist():
    st.header("Watchlist")
    
    # Get watchlist
    watchlist = get_watchlist()
    
    # Sidebar - Add to watchlist
    with st.sidebar:
        st.subheader("Add to Watchlist")
        
        # Search and add stocks
        ticker_input = st.text_input("Enter ticker symbol", key="watchlist_ticker_input")
        
        if ticker_input:
            # Normalize ticker (handle Swedish stocks)
            ticker = normalize_ticker(ticker_input)
            
            # Get stock data fetcher
            data_fetcher = StockDataFetcher()
            
            # Get stock info
            stock_info = data_fetcher.get_stock_info(ticker)
            
            if stock_info:
                st.write(f"Found: {stock_info['name']} ({ticker})")
                
                if st.button("Add to Watchlist"):
                    success = add_to_watchlist(
                        ticker,
                        stock_info['name'],
                        stock_info['exchange'],
                        stock_info['sector']
                    )
                    
                    if success:
                        st.success(f"Added {ticker} to watchlist")
                        # Force reload
                        st.rerun()
                    else:
                        st.warning(f"{ticker} is already in your watchlist")
            else:
                st.error(f"Could not find information for {ticker}")
    
    # If watchlist is empty
    if not watchlist:
        st.info("Your watchlist is empty. Add stocks using the sidebar.")
        return
    
    # Create a table of watchlist stocks with basic information
    watchlist_df = pd.DataFrame(watchlist)
    
    # Initialize stock data fetcher
    data_fetcher = StockDataFetcher()
    
    # Add current price and change columns
    prices = []
    changes = []
    
    for ticker in watchlist_df['ticker']:
        try:
            stock_data = data_fetcher.get_stock_data(ticker, '1d', '5d')
            
            if not stock_data.empty:
                current_price = stock_data['close'].iloc[-1]
                prev_price = stock_data['close'].iloc[-2] if len(stock_data) > 1 else stock_data['close'].iloc[0]
                change_pct = (current_price - prev_price) / prev_price if prev_price > 0 else 0
                
                prices.append(current_price)
                changes.append(change_pct)
            else:
                prices.append(None)
                changes.append(None)
        except Exception as e:
            st.error(f"Error fetching data for {ticker}: {e}")
            prices.append(None)
            changes.append(None)
    
    watchlist_df['current_price'] = prices
    watchlist_df['change_pct'] = changes
    
    # Display the watchlist table with color formatting for changes
    cols_to_display = ['ticker', 'name', 'exchange', 'sector', 'current_price', 'change_pct']
    
    # Format the table
    formatted_df = watchlist_df[cols_to_display].copy()
    formatted_df['current_price'] = formatted_df['current_price'].apply(
        lambda x: f"${x:.2f}" if x is not None else "N/A"
    )
    formatted_df['change_pct'] = formatted_df['change_pct'].apply(
        lambda x: f"{x:.2%}" if x is not None else "N/A"
    )
    
    # Rename columns for display
    formatted_df.columns = ['Ticker', 'Name', 'Exchange', 'Sector', 'Price', 'Change']
    
    # Display the table
    st.dataframe(formatted_df)
    
    # Options for stock analysis
    st.subheader("Quick Analysis")
    
    # Create columns for display
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_ticker = st.selectbox(
            "Select a stock for quick analysis:",
            options=watchlist_df['ticker'].tolist(),
            key="watchlist_analysis_ticker"
        )
    
    with col2:
        timeframe = st.selectbox(
            "Timeframe:",
            options=['1d', '1wk', '1mo'],
            key="watchlist_timeframe"
        )
    
    with col3:
        period = st.selectbox(
            "Period:",
            options=['1mo', '3mo', '6mo', '1y', '2y', '5y'],
            key="watchlist_period"
        )
    
    if selected_ticker:
        # Fetch data
        stock_data = data_fetcher.get_stock_data(selected_ticker, timeframe, period)
        
        if not stock_data.empty:
            # Calculate indicators
            indicators = calculate_all_indicators(stock_data)
            signals = generate_technical_signals(indicators)
            
            # Get fundamentals
            fundamentals = data_fetcher.get_fundamentals(selected_ticker)
            fundamental_analysis = analyze_fundamentals(fundamentals)
            
            # Create tabs for different analysis types
            tab1, tab2 = st.tabs(["Price Chart", "Summary"])
            
            with tab1:
                # Create price chart with indicators
                fig = go.Figure()
                
                # Add price candlesticks
                fig.add_trace(go.Candlestick(
                    x=stock_data.index,
                    open=stock_data['open'],
                    high=stock_data['high'],
                    low=stock_data['low'],
                    close=stock_data['close'],
                    name="Price"
                ))
                
                # Add moving averages
                if 'sma_short' in indicators:
                    fig.add_trace(go.Scatter(
                        x=stock_data.index,
                        y=indicators['sma_short'],
                        name=f"SMA {20}",
                        line=dict(color='blue', width=1)
                    ))
                
                if 'sma_medium' in indicators:
                    fig.add_trace(go.Scatter(
                        x=stock_data.index,
                        y=indicators['sma_medium'],
                        name=f"SMA {50}",
                        line=dict(color='orange', width=1)
                    ))
                
                # Set chart layout
                fig.update_layout(
                    title=f"{selected_ticker} Price Chart",
                    xaxis_title="Date",
                    yaxis_title="Price",
                    xaxis_rangeslider_visible=False,
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            with tab2:
                # Display summary of technical and fundamental analysis
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Technical Analysis")
                    
                    # Overall signal
                    signal = signals.get('overall_signal', 'neutral')
                    signal_color = 'green' if signal == 'bullish' else 'red' if signal == 'bearish' else 'orange'
                    
                    st.markdown(f"**Overall Signal:** <span style='color:{signal_color}'>{signal.upper()}</span>", unsafe_allow_html=True)
                    
                    # Key indicators
                    st.markdown("**Key Indicators:**")
                    
                    # RSI
                    rsi_value = signals.get('rsi_value')
                    if rsi_value is not None:
                        rsi_status = "Overbought" if signals.get('rsi_overbought', False) else "Oversold" if signals.get('rsi_oversold', False) else "Neutral"
                        st.markdown(f"- RSI: {rsi_value:.2f} ({rsi_status})")
                    
                    # MACD
                    macd_status = "Bullish Cross" if signals.get('macd_bullish_cross', False) else "Bearish Cross" if signals.get('macd_bearish_cross', False) else "Neutral"
                    st.markdown(f"- MACD: {macd_status}")
                    
                    # Price vs. Moving Averages
                    price_vs_sma = "Price above all SMAs" if all([
                        signals.get('price_above_sma_short', False),
                        signals.get('price_above_sma_medium', False),
                        signals.get('price_above_sma_long', False)
                    ]) else "Price below all SMAs" if not any([
                        signals.get('price_above_sma_short', False),
                        signals.get('price_above_sma_medium', False),
                        signals.get('price_above_sma_long', False)
                    ]) else "Mixed SMA signals"
                    
                    st.markdown(f"- Moving Averages: {price_vs_sma}")
                    
                    # Breakouts
                    if signals.get('breakout_up', False):
                        st.markdown("- Breakout: Upward breakout detected")
                    elif signals.get('breakout_down', False):
                        st.markdown("- Breakout: Downward breakout detected")
                
                with col2:
                    st.subheader("Fundamental Analysis")
                    
                    # Overall status
                    status = fundamental_analysis['overall']['status']
                    status_color = 'green' if status == 'positive' else 'red' if status == 'negative' else 'orange'
                    
                    st.markdown(f"**Overall Status:** <span style='color:{status_color}'>{status.upper()}</span>", unsafe_allow_html=True)
                    st.markdown(f"**{fundamental_analysis['overall']['description']}**")
                    
                    # Key metrics
                    st.markdown("**Key Metrics:**")
                    
                    # P/E Ratio
                    pe_analysis = fundamental_analysis.get('pe_ratio', {})
                    pe_value = fundamentals.get('pe_ratio')
                    
                    if pe_value is not None:
                        st.markdown(f"- P/E Ratio: {pe_value:.2f} ({pe_analysis.get('status', 'unknown')})")
                    else:
                        st.markdown("- P/E Ratio: Not available")
                    
                    # Profit Margin
                    margin_analysis = fundamental_analysis.get('profit_margin', {})
                    margin_value = fundamentals.get('profit_margin')
                    
                    if margin_value is not None:
                        st.markdown(f"- Profit Margin: {margin_value:.2%} ({margin_analysis.get('status', 'unknown')})")
                    else:
                        st.markdown("- Profit Margin: Not available")
                    
                    # Revenue Growth
                    growth_analysis = fundamental_analysis.get('revenue_growth', {})
                    growth_value = fundamentals.get('revenue_growth')
                    
                    if growth_value is not None:
                        st.markdown(f"- Revenue Growth: {growth_value:.2%} ({growth_analysis.get('status', 'unknown')})")
                    else:
                        st.markdown("- Revenue Growth: Not available")
        else:
            st.error(f"No data available for {selected_ticker}")
    
    # Option to remove stocks from watchlist
    st.subheader("Manage Watchlist")
    
    ticker_to_remove = st.selectbox(
        "Select stock to remove from watchlist:",
        options=watchlist_df['ticker'].tolist(),
        key="watchlist_remove_ticker"
    )
    
    if ticker_to_remove and st.button("Remove from Watchlist"):
        remove_from_watchlist(ticker_to_remove)
        st.success(f"Removed {ticker_to_remove} from watchlist")
        st.rerun()
