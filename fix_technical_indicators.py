"""
Fix technical indicators in the batch scanner.
This script directly modifies the technical indicators in the Streamlit session state.
"""
import streamlit as st
import pandas as pd
import numpy as np
from data.stock_data import StockDataFetcher
from analysis.technical import calculate_all_indicators, generate_technical_signals

def fix_technical_indicators():
    """
    Fix the technical indicators in the current scanner results.
    Directly calculate and replace the values in the session state DataFrame.
    """
    # Check if we have scan results to fix
    if 'scan_results' not in st.session_state or st.session_state.scan_results is None or st.session_state.scan_results.empty:
        st.error("No scan results available. Please run the scanner first.")
        return False
    
    results_df = st.session_state.scan_results.copy()
    
    # Initialize the data fetcher
    data_fetcher = StockDataFetcher()
    
    # Create progress indicators
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Get the period and interval from session state or use defaults
    period = st.session_state.get('scanner_period', '1y')
    interval = st.session_state.get('scanner_interval', '1wk')
    
    # Process each stock
    updated_rows = []
    
    for i, row in enumerate(results_df.itertuples()):
        # Update progress
        progress = (i + 1) / len(results_df)
        progress_bar.progress(progress)
        
        # Get the ticker from the row
        ticker = getattr(row, 'Ticker', None)
        if not ticker:
            continue
        
        status_text.info(f"Processing {ticker} ({i+1}/{len(results_df)})")
        
        try:
            # Get stock data
            stock_data = data_fetcher.get_stock_data(ticker, timeframe=interval, period=period)
            
            if stock_data is None or stock_data.empty:
                # Keep the original row if we can't get data
                updated_rows.append({col: getattr(row, col) for col in results_df.columns})
                continue
            
            # Calculate technical indicators
            indicators = calculate_all_indicators(stock_data)
            
            # Generate technical signals
            signals = generate_technical_signals(indicators)
            
            # Create new row with updated technical data
            new_row = {col: getattr(row, col) for col in results_df.columns}
            
            # Calculate the latest values
            latest_price = stock_data['close'].iloc[-1] if not stock_data.empty else None
            
            # Update technical columns
            if 'Tech Score' in new_row:
                new_row['Tech Score'] = signals.get('tech_score', 0)
                
            if 'Signal' in new_row:
                new_row['Signal'] = signals.get('overall_signal', 'NEUTRAL')
                
            if 'Strength' in new_row:
                new_row['Strength'] = f"{signals.get('tech_score', 0)}%"
                
            if 'RSI' in new_row:
                rsi_value = indicators.get('rsi', pd.Series()).iloc[-1] if 'rsi' in indicators and not indicators['rsi'].empty else None
                new_row['RSI'] = rsi_value
                
            # Calculate SMA values
            sma20 = indicators.get('sma_short', pd.Series()).iloc[-1] if 'sma_short' in indicators and not indicators['sma_short'].empty else None
            sma50 = indicators.get('sma_medium', pd.Series()).iloc[-1] if 'sma_medium' in indicators and not indicators['sma_medium'].empty else None
            sma200 = indicators.get('sma_long', pd.Series()).iloc[-1] if 'sma_long' in indicators and not indicators['sma_long'].empty else None
            
            # Update SMA comparison columns
            if 'vs SMA20' in new_row:
                new_row['vs SMA20'] = "Above" if sma20 is not None and latest_price > sma20 else "Below" if sma20 is not None else "N/A"
                
            if 'vs SMA50' in new_row:
                new_row['vs SMA50'] = "Above" if sma50 is not None and latest_price > sma50 else "Below" if sma50 is not None else "N/A"
                
            if 'vs SMA200' in new_row:
                new_row['vs SMA200'] = "Above" if sma200 is not None and latest_price > sma200 else "Below" if sma200 is not None else "N/A"
                
            # Update MACD column
            if 'MACD' in new_row:
                new_row['MACD'] = "Bullish" if signals.get('macd_bullish_cross', False) else "Bearish" if signals.get('macd_bearish_cross', False) else "Neutral"
                
            # Update 52-week high column
            if 'Near 52w High' in new_row:
                new_row['Near 52w High'] = "Yes" if signals.get('near_52w_high', False) else "No"
                
            # Update breakout column
            if 'Breakout' in new_row:
                new_row['Breakout'] = "Yes" if signals.get('breakout_up', False) else "No"
                
            # Add the updated row
            updated_rows.append(new_row)
            
        except Exception as e:
            # If there's an error, keep the original row
            st.warning(f"Error updating {ticker}: {e}")
            updated_rows.append({col: getattr(row, col) for col in results_df.columns})
    
    # Complete progress
    progress_bar.progress(1.0)
    status_text.success("Technical indicators updated successfully!")
    
    # Update the session state with the fixed data
    if updated_rows:
        fixed_df = pd.DataFrame(updated_rows)
        st.session_state.scan_results = fixed_df
        
    return True


if __name__ == "__main__":
    # This will run when the script is executed directly
    fix_technical_indicators()