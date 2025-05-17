# file: scanner_fix.py

import streamlit as st
import pandas as pd
import numpy as np
from data.stock_data import StockDataFetcher
from analysis.technical import calculate_all_indicators, generate_technical_signals


def fix_technical_indicators():
    """
    Fix the technical indicators in the current scanner results.
    This function recalculates technical indicators for stocks in scan results.
    """
    if 'scan_results' not in st.session_state or st.session_state.scan_results is None or st.session_state.scan_results.empty:
        st.warning("No scan results to fix. Please run the scanner first.")
        return False

    # Get current scan results
    df_res = st.session_state.scan_results.copy()

    # Create progress indicators
    progress_bar = st.progress(0)
    status_text = st.empty()

    # Initialize data fetcher
    data_fetcher = StockDataFetcher()

    # Process each stock in the results
    updated_rows = []

    # Get the period and interval from session state or use defaults
    period = st.session_state.get('scanner_period', '1y')
    interval = st.session_state.get('scanner_interval', '1wk')

    for i, row in enumerate(df_res.itertuples()):
        ticker = getattr(row, 'Ticker', None)
        if not ticker:
            updated_rows.append({col: getattr(row, col)
                                for col in df_res.columns})
            continue

        # Update progress
        progress = (i + 1) / len(df_res)
        progress_bar.progress(progress)
        status_text.info(f"Processing {ticker} ({i+1}/{len(df_res)})")

        try:
            # Get stock data
            stock_data = data_fetcher.get_stock_data(
                ticker, timeframe=interval, period=period)

            if stock_data is None or stock_data.empty:
                # Keep original data if we can't fetch new data
                updated_rows.append({col: getattr(row, col)
                                    for col in df_res.columns})
                continue

            # Calculate technical indicators
            tech_indicators = calculate_all_indicators(stock_data)

            # Generate technical signals
            tech_signals = generate_technical_signals(tech_indicators)

            # Get latest price
            latest_price = stock_data['close'].iloc[-1] if not stock_data.empty else 0

            # Create new row with updated values
            new_row = {col: getattr(row, col) for col in df_res.columns}

            # Update technical values

            # Tech Score
            if 'Tech Score' in new_row:
                new_row['Tech Score'] = tech_signals.get('tech_score', 0)

            # Signal
            if 'Signal' in new_row:
                new_row['Signal'] = tech_signals.get(
                    'overall_signal', 'NEUTRAL')

            # Strength
            if 'Strength' in new_row:
                new_row['Strength'] = f"{tech_signals.get('tech_score', 0)}%"

            # RSI
            if 'RSI' in new_row:
                rsi_value = tech_indicators.get('rsi', pd.Series(
                )).iloc[-1] if 'rsi' in tech_indicators and not tech_indicators['rsi'].empty else None
                new_row['RSI'] = rsi_value

            # Calculate SMA values
            sma20 = tech_indicators.get('sma_short', pd.Series(
            )).iloc[-1] if 'sma_short' in tech_indicators and not tech_indicators['sma_short'].empty else None
            sma50 = tech_indicators.get('sma_medium', pd.Series(
            )).iloc[-1] if 'sma_medium' in tech_indicators and not tech_indicators['sma_medium'].empty else None
            sma200 = tech_indicators.get('sma_long', pd.Series(
            )).iloc[-1] if 'sma_long' in tech_indicators and not tech_indicators['sma_long'].empty else None

            # Compare price to SMAs
            if 'vs SMA20' in new_row:
                new_row['vs SMA20'] = "Above" if sma20 is not None and latest_price > sma20 else "Below" if sma20 is not None else "N/A"

            if 'vs SMA50' in new_row:
                new_row['vs SMA50'] = "Above" if sma50 is not None and latest_price > sma50 else "Below" if sma50 is not None else "N/A"

            if 'vs SMA200' in new_row:
                new_row['vs SMA200'] = "Above" if sma200 is not None and latest_price > sma200 else "Below" if sma200 is not None else "N/A"

            # MACD signal
            if 'MACD' in new_row:
                new_row['MACD'] = "Bullish" if tech_signals.get(
                    'macd_bullish_cross', False) else "Bearish" if tech_signals.get('macd_bearish_cross', False) else "Neutral"

            # Near 52-week high
            if 'Near 52w High' in new_row:
                new_row['Near 52w High'] = "Yes" if tech_signals.get(
                    'near_52w_high', False) else "No"

            # Breakout
            if 'Breakout' in new_row:
                new_row['Breakout'] = "Yes" if tech_signals.get(
                    'breakout_up', False) else "No"

            # Add updated row
            updated_rows.append(new_row)

        except Exception as e:
            # Keep original row on error
            st.warning(f"Error processing {ticker}: {e}")
            updated_rows.append({col: getattr(row, col)
                                for col in df_res.columns})

    # Complete progress
    progress_bar.progress(1.0)
    status_text.success("Technical indicators updated successfully!")

    # Update session state with fixed data
    if updated_rows:
        fixed_df = pd.DataFrame(updated_rows)
        st.session_state.scan_results = fixed_df

    return True
