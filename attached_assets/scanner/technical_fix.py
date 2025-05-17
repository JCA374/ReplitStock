import streamlit as st
import pandas as pd
import numpy as np
from data.stock_data import StockDataFetcher
from analysis.technical import calculate_all_indicators, generate_technical_signals

def add_fix_button():
    """Add a button to fix technical indicators in the scanner results"""
    if 'scan_results' not in st.session_state or st.session_state.scan_results is None or st.session_state.scan_results.empty:
        return
        
    st.button("🔧 Fix Technical Indicators", 
             on_click=fix_technical_indicators,
             help="Recalculate all technical indicators for the current scan results")
    
def fix_technical_indicators():
    """Recalculate and fix all technical indicators in the current scan results"""
    if 'scan_results' not in st.session_state or st.session_state.scan_results is None or st.session_state.scan_results.empty:
        st.warning("No scan results available to fix")
        return
        
    with st.spinner("Fixing technical indicators..."):
        # Get the current scan results
        results = st.session_state.scan_results.copy()
        
        # Create data fetcher
        data_fetcher = StockDataFetcher()
        
        # Get period and interval from session state
        period = st.session_state.get('scanner_period', '1y')
        interval = st.session_state.get('scanner_interval', '1wk')
        
        # Show progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Process each ticker
        updated_results = []
        
        for i, row in enumerate(results.itertuples()):
            ticker = getattr(row, 'Ticker', None)
            if not ticker:
                continue
                
            # Update progress
            progress = (i + 1) / len(results)
            progress_bar.progress(progress)
            status_text.info(f"Processing {ticker} ({i+1}/{len(results)})")
            
            try:
                # Get stock data
                stock_data = data_fetcher.get_stock_data(ticker, timeframe=interval, period=period)
                
                if stock_data is None or stock_data.empty:
                    # Keep original data if we can't get new data
                    updated_results.append({col: getattr(row, col) for col in results.columns})
                    continue
                    
                # Calculate technical indicators
                indicators = calculate_all_indicators(stock_data)
                
                # Generate signals based on indicators
                signals = generate_technical_signals(indicators)
                
                # Create new row with updated values
                new_row = {col: getattr(row, col) for col in results.columns}
                
                # Latest price
                latest_price = stock_data['close'].iloc[-1] if not stock_data.empty else 0
                
                # Update technical indicator values
                
                # Tech Score
                if 'Tech Score' in new_row:
                    new_row['Tech Score'] = int(signals.get('tech_score', 0))
                
                # Signal
                if 'Signal' in new_row:
                    new_row['Signal'] = signals.get('overall_signal', 'NEUTRAL')
                
                # Strength
                if 'Strength' in new_row:
                    new_row['Strength'] = f"{signals.get('tech_score', 0)}%"
                
                # RSI
                if 'RSI' in new_row:
                    rsi_value = indicators.get('rsi', pd.Series()).iloc[-1] if 'rsi' in indicators and not indicators['rsi'].empty else None
                    new_row['RSI'] = rsi_value
                
                # SMA values
                sma20 = indicators.get('sma_short', pd.Series()).iloc[-1] if 'sma_short' in indicators and not indicators['sma_short'].empty else None
                sma50 = indicators.get('sma_medium', pd.Series()).iloc[-1] if 'sma_medium' in indicators and not indicators['sma_medium'].empty else None
                sma200 = indicators.get('sma_long', pd.Series()).iloc[-1] if 'sma_long' in indicators and not indicators['sma_long'].empty else None
                
                # SMA comparisons
                if 'vs SMA20' in new_row:
                    new_row['vs SMA20'] = "Above" if sma20 is not None and latest_price > sma20 else "Below" if sma20 is not None else "N/A"
                    
                if 'vs SMA50' in new_row:
                    new_row['vs SMA50'] = "Above" if sma50 is not None and latest_price > sma50 else "Below" if sma50 is not None else "N/A"
                    
                if 'vs SMA200' in new_row:
                    new_row['vs SMA200'] = "Above" if sma200 is not None and latest_price > sma200 else "Below" if sma200 is not None else "N/A"
                
                # MACD
                if 'MACD' in new_row:
                    new_row['MACD'] = "Bullish" if signals.get('macd_bullish_cross', False) else "Bearish" if signals.get('macd_bearish_cross', False) else "Neutral"
                
                # 52-week high
                if 'Near 52w High' in new_row:
                    new_row['Near 52w High'] = "Yes" if signals.get('near_52w_high', False) else "No"
                
                # Breakout
                if 'Breakout' in new_row:
                    new_row['Breakout'] = "Yes" if signals.get('breakout_up', False) else "No"
                
                # Add updated row to results
                updated_results.append(new_row)
                
            except Exception as e:
                st.error(f"Error processing {ticker}: {str(e)}")
                # Keep original row on error
                updated_results.append({col: getattr(row, col) for col in results.columns})
        
        # Complete progress and show success message
        progress_bar.progress(1.0)
        status_text.success("Technical indicators updated successfully!")
        
        # Update session state with fixed results
        if updated_results:
            st.session_state.scan_results = pd.DataFrame(updated_results)