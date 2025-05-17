import streamlit as st
import pandas as pd
import numpy as np
from data.stock_data import StockDataFetcher
from analysis.technical import calculate_all_indicators, generate_technical_signals

def main():
    """Simple utility to fix technical indicators in scanner results"""
    st.title("Technical Indicators Fix Utility")
    
    if 'scan_results' not in st.session_state or st.session_state.scan_results is None or st.session_state.scan_results.empty:
        st.warning("No scan results found in session state. Please run the scanner first.")
        return
    
    st.info("This utility will recalculate all technical indicators for the stocks in your scan results.")
    
    if st.button("Fix Technical Indicators"):
        fix_technical_indicators()

def fix_technical_indicators():
    """Fix technical indicators in the scan results"""
    if 'scan_results' not in st.session_state or st.session_state.scan_results is None or st.session_state.scan_results.empty:
        st.warning("No scan results found in session state.")
        return
    
    # Get current scan results
    df = st.session_state.scan_results.copy()
    
    # Create progress indicators
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Initialize data fetcher
    data_fetcher = StockDataFetcher()
    
    # Get default period and interval
    period = '1y'
    interval = '1wk'
    
    # Process each stock
    updated_rows = []
    
    for i, row in enumerate(df.itertuples()):
        # Update progress
        progress = (i + 1) / len(df)
        progress_bar.progress(progress)
        
        # Get ticker from row
        ticker = getattr(row, 'Ticker', None)
        if not ticker:
            continue
        
        # Update status
        status_text.info(f"Processing {ticker} ({i+1}/{len(df)})")
        
        try:
            # Get stock data
            stock_data = data_fetcher.get_stock_data(ticker, timeframe=interval, period=period)
            
            if stock_data is None or stock_data.empty:
                # Keep original row if no data
                updated_rows.append({col: getattr(row, col) for col in df.columns})
                continue
            
            # Calculate technical indicators
            indicators = calculate_all_indicators(stock_data)
            
            # Generate signals
            signals = generate_technical_signals(indicators)
            
            # Create new row with updated values
            new_row = {col: getattr(row, col) for col in df.columns}
            
            # Get latest price
            latest_price = stock_data['close'].iloc[-1] if not stock_data.empty else None
            
            # Update technical values
            
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
            
            # MACD
            if 'MACD' in new_row:
                new_row['MACD'] = "Bullish" if signals.get('macd_bullish_cross', False) else "Bearish" if signals.get('macd_bearish_cross', False) else "Neutral"
            
            # 52-week high
            if 'Near 52w High' in new_row:
                new_row['Near 52w High'] = "Yes" if signals.get('near_52w_high', False) else "No"
            
            # Breakout
            if 'Breakout' in new_row:
                new_row['Breakout'] = "Yes" if signals.get('breakout_up', False) else "No"
            
            # Add the updated row
            updated_rows.append(new_row)
            
        except Exception as e:
            st.error(f"Error processing {ticker}: {str(e)}")
            # Keep original row on error
            updated_rows.append({col: getattr(row, col) for col in df.columns})
    
    # Complete progress
    progress_bar.progress(1.0)
    status_text.success("Technical indicators updated successfully!")
    
    # Update session state with fixed data
    if updated_rows:
        fixed_df = pd.DataFrame(updated_rows)
        st.session_state.scan_results = fixed_df
        
        # Display updated results
        st.subheader("Updated Technical Indicators")
        st.dataframe(fixed_df, use_container_width=True)
        
        # Show which columns were updated
        tech_columns = ['Tech Score', 'Signal', 'Strength', 'RSI', 
                       'vs SMA20', 'vs SMA50', 'vs SMA200', 
                       'MACD', 'Near 52w High', 'Breakout']
        
        updated_cols = [col for col in tech_columns if col in fixed_df.columns]
        st.write(f"Updated columns: {', '.join(updated_cols)}")
        
        return True
    
    return False

if __name__ == "__main__":
    main()