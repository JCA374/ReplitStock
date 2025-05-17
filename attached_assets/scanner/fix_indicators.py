import streamlit as st
import pandas as pd
import numpy as np
from data.stock_data import StockDataFetcher
from analysis.technical import calculate_all_indicators, generate_technical_signals

def fix_scanner_indicators():
    """
    Fix the technical indicators in the current scanner results.
    This function recalculates the indicators for stocks with blank/NA values.
    """
    if 'scan_results' not in st.session_state or st.session_state.scan_results is None or st.session_state.scan_results.empty:
        st.warning("No scan results to fix. Please run the scanner first.")
        return False
    
    # Get current scan results
    df = st.session_state.scan_results.copy()
    
    # Create progress indicators
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Initialize data fetcher
    data_fetcher = StockDataFetcher()
    
    # Set period and interval from session state or use defaults
    period = st.session_state.get('scanner_period', '1y')
    interval = st.session_state.get('scanner_interval', '1wk')
    
    # Process each stock in the results
    updated_rows = []
    
    for i, row in enumerate(df.itertuples()):
        # Update progress
        progress_bar.progress((i + 1) / len(df))
        
        # Get ticker from the row
        ticker = getattr(row, 'Ticker', None)
        if not ticker:
            updated_rows.append({col: getattr(row, col) for col in df.columns})
            continue
        
        status_text.info(f"Processing {ticker} ({i+1}/{len(df)})")
        
        try:
            # Get stock data
            stock_data = data_fetcher.get_stock_data(ticker, timeframe=interval, period=period)
            
            if stock_data is None or stock_data.empty:
                # Keep original row if we can't get data
                updated_rows.append({col: getattr(row, col) for col in df.columns})
                continue
            
            # Calculate indicators
            tech_indicators = calculate_all_indicators(stock_data)
            
            # Generate signals
            tech_signals = generate_technical_signals(tech_indicators)
            
            # Create updated row
            new_row = {col: getattr(row, col) for col in df.columns}
            
            # Get the latest price
            latest_price = stock_data['close'].iloc[-1] if not stock_data.empty else None
            
            # Update technical indicators
            
            # Tech Score
            if 'Tech Score' in new_row:
                new_row['Tech Score'] = tech_signals.get('tech_score', 0)
            
            # Signal
            if 'Signal' in new_row:
                new_row['Signal'] = tech_signals.get('overall_signal', 'NEUTRAL')
            
            # Strength
            if 'Strength' in new_row:
                new_row['Strength'] = f"{tech_signals.get('tech_score', 0)}%"
            
            # RSI
            if 'RSI' in new_row:
                rsi_value = tech_indicators.get('rsi', pd.Series()).iloc[-1] if 'rsi' in tech_indicators and not tech_indicators['rsi'].empty else None
                new_row['RSI'] = rsi_value
            
            # Get SMA values
            sma20 = tech_indicators.get('sma_short', pd.Series()).iloc[-1] if 'sma_short' in tech_indicators and not tech_indicators['sma_short'].empty else None
            sma50 = tech_indicators.get('sma_medium', pd.Series()).iloc[-1] if 'sma_medium' in tech_indicators and not tech_indicators['sma_medium'].empty else None
            sma200 = tech_indicators.get('sma_long', pd.Series()).iloc[-1] if 'sma_long' in tech_indicators and not tech_indicators['sma_long'].empty else None
            
            # Update SMA comparison columns
            if 'vs SMA20' in new_row:
                new_row['vs SMA20'] = "Above" if sma20 is not None and latest_price > sma20 else "Below" if sma20 is not None else "N/A"
            
            if 'vs SMA50' in new_row:
                new_row['vs SMA50'] = "Above" if sma50 is not None and latest_price > sma50 else "Below" if sma50 is not None else "N/A"
            
            if 'vs SMA200' in new_row:
                new_row['vs SMA200'] = "Above" if sma200 is not None and latest_price > sma200 else "Below" if sma200 is not None else "N/A"
            
            # Update MACD column
            if 'MACD' in new_row:
                new_row['MACD'] = "Bullish" if tech_signals.get('macd_bullish_cross', False) else "Bearish" if tech_signals.get('macd_bearish_cross', False) else "Neutral"
            
            # Update 52-week high column
            if 'Near 52w High' in new_row:
                new_row['Near 52w High'] = "Yes" if tech_signals.get('near_52w_high', False) else "No"
            
            # Update breakout column
            if 'Breakout' in new_row:
                new_row['Breakout'] = "Yes" if tech_signals.get('breakout_up', False) else "No"
            
            # Add the updated row
            updated_rows.append(new_row)
            
        except Exception as e:
            st.warning(f"Error updating {ticker}: {e}")
            # Keep original row on error
            updated_rows.append({col: getattr(row, col) for col in df.columns})
    
    # Complete progress
    progress_bar.progress(1.0)
    status_text.success("Technical indicators updated successfully!")
    
    # Update session state with fixed data
    if updated_rows:
        fixed_df = pd.DataFrame(updated_rows)
        st.session_state.scan_results = fixed_df
        
    return True