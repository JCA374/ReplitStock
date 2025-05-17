import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data.stock_data import StockDataFetcher
from data.db_manager import get_watchlist
from analysis.technical import calculate_all_indicators, generate_technical_signals
from analysis.fundamental import analyze_fundamentals
from utils.ticker_mapping import normalize_ticker
from config import TIMEFRAMES, PERIOD_OPTIONS

def display_batch_analysis():
    st.header("Batch Analysis")
    st.write("Analyze multiple stocks at once to compare their technical and fundamental indicators.")
    
    # Initialize data fetcher
    data_fetcher = StockDataFetcher()
    
    # Get watchlist for quick selection
    watchlist = get_watchlist()
    watchlist_tickers = [item['ticker'] for item in watchlist]
    
    # Input methods for batch analysis
    input_method = st.radio(
        "Select stocks from:",
        ["Watchlist", "Manual Entry"],
        key="batch_input_method"
    )
    
    selected_tickers = []
    
    if input_method == "Watchlist":
        if not watchlist:
            st.warning("Your watchlist is empty. Please add stocks to your watchlist or use manual entry.")
        else:
            selected_tickers = st.multiselect(
                "Select stocks from your watchlist:",
                options=watchlist_tickers,
                key="batch_watchlist_select"
            )
    else:  # Manual Entry
        ticker_input = st.text_input(
            "Enter ticker symbols (comma-separated):",
            key="batch_manual_tickers"
        )
        
        if ticker_input:
            # Parse and normalize tickers
            raw_tickers = [t.strip() for t in ticker_input.split(",")]
            selected_tickers = [normalize_ticker(t) for t in raw_tickers if t]
    
    # Analysis parameters
    col1, col2 = st.columns(2)
    
    with col1:
        timeframe = st.selectbox(
            "Timeframe:",
            options=list(TIMEFRAMES.keys()),
            key="batch_timeframe"
        )
    
    with col2:
        period = st.selectbox(
            "Period:",
            options=list(PERIOD_OPTIONS.keys()),
            key="batch_period"
        )
    
    # Convert selected options to API format
    timeframe_value = TIMEFRAMES[timeframe]
    period_value = PERIOD_OPTIONS[period]
    
    # Analysis button
    if selected_tickers and st.button("Run Batch Analysis"):
        # Create a progress bar
        progress_bar = st.progress(0)
        
        # Results container
        results = []
        
        # Process each ticker
        for i, ticker in enumerate(selected_tickers):
            progress_value = (i / len(selected_tickers))
            progress_bar.progress(progress_value, f"Analyzing {ticker}...")
            
            try:
                # Fetch data
                stock_data = data_fetcher.get_stock_data(ticker, timeframe_value, period_value)
                
                if stock_data.empty:
                    results.append({
                        'ticker': ticker,
                        'status': 'error',
                        'message': 'No data available'
                    })
                    continue
                
                # Get stock info
                stock_info = data_fetcher.get_stock_info(ticker)
                
                # Get fundamentals
                fundamentals = data_fetcher.get_fundamentals(ticker)
                
                # Calculate technical indicators
                indicators = calculate_all_indicators(stock_data)
                
                # Add current price to the indicators for proper signal generation
                if not stock_data.empty and 'close' in stock_data.columns:
                    if 'price_pattern' not in indicators or not indicators['price_pattern']:
                        indicators['price_pattern'] = {'current_price': stock_data['close'].iloc[-1]}
                    else:
                        indicators['price_pattern']['current_price'] = stock_data['close'].iloc[-1]
                
                # Generate signals
                signals = generate_technical_signals(indicators)
                
                # Analyze fundamentals
                fundamental_analysis = analyze_fundamentals(fundamentals)
                
                # Get last price and change
                last_price = stock_data['close'].iloc[-1]
                prev_price = stock_data['close'].iloc[-2] if len(stock_data) > 1 else stock_data['close'].iloc[0]
                price_change = (last_price - prev_price) / prev_price if prev_price > 0 else 0
                
                # Aggregate results
                result = {
                    'ticker': ticker,
                    'name': stock_info.get('name', ticker),
                    'sector': stock_info.get('sector', 'Unknown'),
                    'last_price': last_price,
                    'price_change': price_change,
                    'technical_signal': signals.get('overall_signal', 'neutral'),
                    'signal_strength': signals.get('signal_strength', 0),
                    'rsi': signals.get('rsi_value'),
                    'price_above_sma20': signals.get('price_above_sma_short'),
                    'price_above_sma50': signals.get('price_above_sma_medium'),
                    'price_above_sma200': signals.get('price_above_sma_long'),
                    'macd_signal': 'bullish' if signals.get('macd_bullish_cross', False) else 'bearish' if signals.get('macd_bearish_cross', False) else 'neutral',
                    'fundamental_status': fundamental_analysis['overall']['status'],
                    'pe_ratio': fundamentals.get('pe_ratio'),
                    'profit_margin': fundamentals.get('profit_margin'),
                    'revenue_growth': fundamentals.get('revenue_growth'),
                    'status': 'success'
                }
                
                results.append(result)
                
            except Exception as e:
                results.append({
                    'ticker': ticker,
                    'status': 'error',
                    'message': str(e)
                })
        
        # Complete the progress bar
        progress_bar.progress(1.0, "Analysis complete!")
        
        # Display results
        if results:
            # Filter successful analyses
            success_results = [r for r in results if r.get('status') == 'success']
            error_results = [r for r in results if r.get('status') == 'error']
            
            if success_results:
                # Create DataFrame for display
                results_df = pd.DataFrame(success_results)
                
                # Create summary table
                summary_cols = [
                    'ticker', 'name', 'last_price', 'price_change', 
                    'technical_signal', 'fundamental_status'
                ]
                
                summary_df = results_df[summary_cols].copy()
                
                # Format columns
                summary_df['price_change'] = summary_df['price_change'].apply(lambda x: f"{x:.2%}")
                summary_df['technical_signal'] = summary_df['technical_signal'].str.upper()
                summary_df['fundamental_status'] = summary_df['fundamental_status'].str.capitalize()
                
                # Rename columns for display
                summary_df.columns = [
                    'Ticker', 'Name', 'Price', 'Change', 
                    'Technical Signal', 'Fundamentals'
                ]
                
                st.subheader("Analysis Summary")
                st.dataframe(summary_df, hide_index=True, use_container_width=True)
                
                # Create tabs for technical and fundamental details
                tab1, tab2 = st.tabs(["Technical Analysis", "Fundamental Analysis"])
                
                with tab1:
                    # Technical indicators table
                    tech_cols = [
                        'ticker', 'technical_signal', 'signal_strength', 'rsi',
                        'price_above_sma20', 'price_above_sma50', 'price_above_sma200',
                        'macd_signal'
                    ]
                    
                    tech_df = results_df[tech_cols].copy()
                    
                    # Format columns
                    tech_df['signal_strength'] = tech_df['signal_strength'].apply(lambda x: f"{x*100:.1f}%")
                    tech_df['rsi'] = tech_df['rsi'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")
                    
                    for col in ['price_above_sma20', 'price_above_sma50', 'price_above_sma200']:
                        tech_df[col] = tech_df[col].apply(
                            lambda x: "Above" if x else "Below" if pd.notna(x) else "N/A"
                        )
                    
                    tech_df['macd_signal'] = tech_df['macd_signal'].str.capitalize()
                    
                    # Rename columns for display
                    tech_df.columns = [
                        'Ticker', 'Signal', 'Strength', 'RSI',
                        'vs SMA20', 'vs SMA50', 'vs SMA200',
                        'MACD'
                    ]
                    
                    st.subheader("Technical Indicators")
                    st.dataframe(tech_df, hide_index=True, use_container_width=True)
                    
                    # Technical signals chart
                    st.subheader("Technical Signals Comparison")
                    
                    # Prepare data for visualization
                    chart_data = results_df[['ticker', 'signal_strength']].copy()
                    chart_data['signal_color'] = results_df['technical_signal'].apply(
                        lambda x: 'green' if x == 'bullish' else 'red' if x == 'bearish' else 'orange'
                    )
                    chart_data['signal_strength'] = chart_data['signal_strength'] * 100  # Convert to percentage
                    
                    # Sort by signal strength
                    chart_data = chart_data.sort_values('signal_strength', ascending=False)
                    
                    # Create horizontal bar chart
                    fig = go.Figure()
                    
                    fig.add_trace(go.Bar(
                        y=chart_data['ticker'],
                        x=chart_data['signal_strength'],
                        orientation='h',
                        marker_color=chart_data['signal_color'],
                        text=chart_data['signal_strength'].apply(lambda x: f"{x:.1f}%"),
                        textposition='auto'
                    ))
                    
                    fig.update_layout(
                        title="Technical Signal Strength",
                        xaxis_title="Signal Strength (%)",
                        yaxis_title="Ticker",
                        height=max(300, len(chart_data) * 30),
                        margin=dict(l=0, r=0, t=40, b=0)
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                with tab2:
                    # Fundamental metrics table
                    fund_cols = [
                        'ticker', 'fundamental_status', 'pe_ratio',
                        'profit_margin', 'revenue_growth'
                    ]
                    
                    fund_df = results_df[fund_cols].copy()
                    
                    # Format columns
                    fund_df['pe_ratio'] = fund_df['pe_ratio'].apply(
                        lambda x: f"{x:.2f}" if pd.notna(x) else "N/A"
                    )
                    fund_df['profit_margin'] = fund_df['profit_margin'].apply(
                        lambda x: f"{x:.2%}" if pd.notna(x) else "N/A"
                    )
                    fund_df['revenue_growth'] = fund_df['revenue_growth'].apply(
                        lambda x: f"{x:.2%}" if pd.notna(x) else "N/A"
                    )
                    fund_df['fundamental_status'] = fund_df['fundamental_status'].str.capitalize()
                    
                    # Rename columns for display
                    fund_df.columns = [
                        'Ticker', 'Status', 'P/E Ratio',
                        'Profit Margin', 'Revenue Growth'
                    ]
                    
                    st.subheader("Fundamental Metrics")
                    st.dataframe(fund_df, hide_index=True, use_container_width=True)
                    
                    # P/E Ratio comparison chart
                    pe_data = results_df[['ticker', 'pe_ratio']].dropna(subset=['pe_ratio']).copy()
                    
                    if not pe_data.empty:
                        # Sort by P/E ratio
                        pe_data = pe_data.sort_values('pe_ratio')
                        
                        # Create color based on P/E range
                        pe_data['color'] = pe_data['pe_ratio'].apply(
                            lambda x: 'green' if x < 15 else 'red' if x > 30 else 'orange'
                        )
                        
                        # Create bar chart
                        fig = go.Figure()
                        
                        fig.add_trace(go.Bar(
                            x=pe_data['ticker'],
                            y=pe_data['pe_ratio'],
                            marker_color=pe_data['color'],
                            text=pe_data['pe_ratio'].apply(lambda x: f"{x:.2f}"),
                            textposition='auto'
                        ))
                        
                        fig.update_layout(
                            title="P/E Ratio Comparison",
                            xaxis_title="Ticker",
                            yaxis_title="P/E Ratio",
                            height=400
                        )
                        
                        # Add reference lines for P/E thresholds
                        fig.add_shape(
                            type="line",
                            x0=-1,
                            y0=15,
                            x1=len(pe_data),
                            y1=15,
                            line=dict(
                                color="green",
                                width=1,
                                dash="dash",
                            )
                        )
                        
                        fig.add_shape(
                            type="line",
                            x0=-1,
                            y0=30,
                            x1=len(pe_data),
                            y1=30,
                            line=dict(
                                color="red",
                                width=1,
                                dash="dash",
                            )
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No P/E ratio data available for comparison")
                    
                    # Profit margin comparison chart
                    margin_data = results_df[['ticker', 'profit_margin']].dropna(subset=['profit_margin']).copy()
                    
                    if not margin_data.empty:
                        # Sort by profit margin
                        margin_data = margin_data.sort_values('profit_margin', ascending=False)
                        
                        # Create color based on profit margin
                        margin_data['color'] = margin_data['profit_margin'].apply(
                            lambda x: 'red' if x < 0 else 'orange' if x < 0.1 else 'green'
                        )
                        
                        # Create bar chart
                        fig = go.Figure()
                        
                        fig.add_trace(go.Bar(
                            x=margin_data['ticker'],
                            y=margin_data['profit_margin'],
                            marker_color=margin_data['color'],
                            text=margin_data['profit_margin'].apply(lambda x: f"{x:.2%}"),
                            textposition='auto'
                        ))
                        
                        fig.update_layout(
                            title="Profit Margin Comparison",
                            xaxis_title="Ticker",
                            yaxis_title="Profit Margin",
                            height=400
                        )
                        
                        # Add reference line for profit margin threshold
                        fig.add_shape(
                            type="line",
                            x0=-1,
                            y0=0.1,
                            x1=len(margin_data),
                            y1=0.1,
                            line=dict(
                                color="green",
                                width=1,
                                dash="dash",
                            )
                        )
                        
                        fig.add_shape(
                            type="line",
                            x0=-1,
                            y0=0,
                            x1=len(margin_data),
                            y1=0,
                            line=dict(
                                color="red",
                                width=1,
                                dash="dash",
                            )
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No profit margin data available for comparison")
            
            # Display errors, if any
            if error_results:
                st.subheader("Errors")
                
                for error in error_results:
                    st.error(f"Error analyzing {error['ticker']}: {error.get('message', 'Unknown error')}")
        else:
            st.warning("No results to display. Please check your ticker symbols and try again.")
    else:
        # Display instructions or sample image
        if not selected_tickers:
            st.info("Select stocks to analyze and click 'Run Batch Analysis'")
            st.image("https://pixabay.com/get/ga24cbf3b19c72cc00ac094bb8451c213f9f584cb07b51ab73be52ec9479fba91e8e8b993cf18d66670ca559e2450dd376bea205101c9f8603ede44ab1861bdb4_1280.jpg", 
                    caption="Batch analysis allows you to compare multiple stocks at once")
