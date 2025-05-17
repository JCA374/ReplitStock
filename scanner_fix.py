import streamlit as st
import pandas as pd
import numpy as np
from data.stock_data import StockDataFetcher
from analysis.technical import calculate_all_indicators, generate_technical_signals

def main():
    """Simple utility to fix technical indicators in scanner results"""
    st.title("Technical Indicator Fix Utility")
    
    # Check if there are scan results to fix
    if 'scan_results' not in st.session_state or st.session_state.get('scan_results') is None:
        st.warning("No scan results found in session state. Run a scan first.")
        return
    
    if st.session_state.scan_results.empty:
        st.warning("Scan results are empty. Run a scan with matching criteria first.")
        return
    
    # Display original results
    st.subheader("Original Scan Results")
    st.dataframe(st.session_state.scan_results)
    
    # Add a button to fix
    if st.button("Fix Technical Indicators"):
        with st.spinner("Fixing technical indicators..."):
            fix_technical_indicators()
            st.success("Technical indicators fixed successfully!")
            
        # Display fixed results
        st.subheader("Fixed Scan Results")
        st.dataframe(st.session_state.scan_results)

def fix_technical_indicators():
    """Fix technical indicators in the scan results"""
    # Get current scan results
    results = st.session_state.scan_results.copy()
    
    # Create progress indicators
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Initialize data fetcher
    data_fetcher = StockDataFetcher()
    
    # Get period and interval
    period = st.session_state.get('scanner_period', '1y')
    interval = st.session_state.get('scanner_interval', '1wk')
    
    # Process each stock
    updated_rows = []
    
    for i, row in enumerate(results.itertuples()):
        # Update progress
        progress = (i + 1) / len(results)
        progress_bar.progress(progress)
        
        ticker = getattr(row, 'Ticker', None)
        if not ticker:
            updated_rows.append({col: getattr(row, col) for col in results.columns})
            continue
        
        status_text.info(f"Processing {ticker} ({i+1}/{len(results)})")
        
        try:
            # Get stock data
            stock_data = data_fetcher.get_stock_data(ticker, timeframe=interval, period=period)
            
            if stock_data is None or stock_data.empty:
                # Keep original row if data not available
                updated_rows.append({col: getattr(row, col) for col in results.columns})
                continue
            
            # Calculate technical indicators
            indicators = calculate_all_indicators(stock_data)
            
            # Generate signals
            signals = generate_technical_signals(indicators)
            
            # Create updated row
            new_row = {col: getattr(row, col) for col in results.columns}
            
            # Get latest price
            latest_price = stock_data['close'].iloc[-1] if not stock_data.empty else None
            
            # Update technical indicators
            
            # Tech Score
            if 'Tech Score' in new_row:
                new_row['Tech Score'] = signals.get('tech_score', 0)
            
            # Signal
            if 'Signal' in new_row:
                new_row['Signal'] = signals.get('overall_signal', 'NEUTRAL')
            
            # Strength
            if 'Strength' in new_row:
                new_row['Strength'] = f"{signals.get('tech_score', 0)}%"
            
            # RSI
            if 'RSI' in new_row:
                rsi_value = indicators.get('rsi', pd.Series()).iloc[-1] if 'rsi' in indicators and not indicators['rsi'].empty else None
                new_row['RSI'] = round(rsi_value, 2) if rsi_value is not None else None
            
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
            
            # Add updated row
            updated_rows.append(new_row)
            
        except Exception as e:
            st.warning(f"Error processing {ticker}: {str(e)}")
            updated_rows.append({col: getattr(row, col) for col in results.columns})
    
    # Complete progress
    progress_bar.progress(1.0)
    status_text.success("Technical indicators updated successfully!")
    
    # Update session state
    if updated_rows:
        fixed_df = pd.DataFrame(updated_rows)
        st.session_state.scan_results = fixed_df

if __name__ == "__main__":
    main()