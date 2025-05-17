# scanner/analysis.py
import streamlit as st
import pandas as pd
import numpy as np
import time
from data.stock_data import StockDataFetcher
from analysis.technical import calculate_all_indicators, generate_technical_signals, ensure_indicators_not_blank
from analysis.fundamental import analyze_fundamentals

def perform_scan(tickers, period="1y", interval="1wk", rsi_range=(30, 70), 
                vol_multiplier=1.5, lookback=30, batch_size=25, continuous_scan=True):
    """
    Perform a stock scan on the provided tickers.
    
    Args:
        tickers (list): List of ticker pairs (display_name, ticker_symbol)
        period (str): Period to analyze (1mo, 3mo, 6mo, 1y, etc.)
        interval (str): Time interval (1d, 5d, 1wk, etc.)
        rsi_range (tuple): (min, max) range for RSI filter
        vol_multiplier (float): Volume multiplier for volume filter
        lookback (int): Days to look back for crossovers
        batch_size (int): Number of tickers to process in each batch
        continuous_scan (bool): If True, add delays between batches
    """
    # Initialize state if needed
    if 'scan_results' not in st.session_state:
        st.session_state.scan_results = pd.DataFrame()
    
    if 'failed_tickers' not in st.session_state:
        st.session_state.failed_tickers = []
    
    # Set scanner running state
    st.session_state.scanner_running = True
    
    # Create progress indicators
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Initialize data fetcher
    data_fetcher = StockDataFetcher()
    
    # Create results list
    results = []
    failed = []
    
    # Calculate total batches for progress tracking
    total_tickers = len(tickers)
    total_batches = (total_tickers + batch_size - 1) // batch_size
    
    # Process tickers in batches
    for batch_idx in range(total_batches):
        # Update progress
        progress = batch_idx / total_batches
        progress_bar.progress(progress)
        
        # Check if scanner was stopped
        if not st.session_state.get('scanner_running', True):
            status_text.warning("Scanner stopped by user")
            break
            
        # Get current batch
        start_idx = batch_idx * batch_size
        end_idx = min(start_idx + batch_size, total_tickers)
        current_batch = tickers[start_idx:end_idx]
        
        # Update status message
        status_msg = f"Processing batch {batch_idx+1}/{total_batches} ({start_idx+1}-{end_idx} of {total_tickers})"
        status_text.info(status_msg)
        st.session_state.status_message = status_msg
        
        # Process each ticker in the batch
        for idx, (display_name, ticker) in enumerate(current_batch):
            try:
                # Update ticker-specific status
                ticker_status = f"Processing {ticker} ({idx+1}/{len(current_batch)})"
                status_text.info(f"{status_msg} - {ticker_status}")
                
                # Get stock data
                stock_data = data_fetcher.get_stock_data(ticker, 
                                                       timeframe=interval, 
                                                       period=period)
                
                if stock_data is None or stock_data.empty:
                    failed.append(ticker)
                    continue
                
                # Get stock info for fundamentals
                stock_info = data_fetcher.get_stock_info(ticker)
                
                # Calculate technical indicators
                tech_indicators = calculate_all_indicators(stock_data)
                
                # Ensure indicators are not blank
                from analysis.technical import ensure_indicators_not_blank
                tech_indicators = ensure_indicators_not_blank(tech_indicators, stock_data)
                
                # Generate technical signals
                tech_signals = generate_technical_signals(tech_indicators)
                
                # Get fundamentals data
                fundamentals = data_fetcher.get_fundamentals(ticker)
                
                # Analyze fundamentals
                fund_analysis = analyze_fundamentals(fundamentals)
                
                # Prepare result data
                last_price = stock_data['close'].iloc[-1] if not stock_data.empty else None
                stock_name = stock_info.get('shortName', ticker) if stock_info else ticker
                
                # Extract actual values for key indicators (not just Boolean flags)
                # Get RSI value directly from the indicators - it's a more reliable source
                rsi_value = tech_indicators.get('rsi', pd.Series()).iloc[-1] if 'rsi' in tech_indicators and not tech_indicators['rsi'].empty else None
                
                # Make sure tech_score is never zero or empty
                tech_score = tech_signals.get('tech_score', 50)
                if tech_score == 0:
                    # If tech_score is 0, set a default value of 50 (neutral)
                    tech_score = 50
                
                signal = tech_signals.get('overall_signal', 'NEUTRAL')
                
                # Extract SMA values for display
                latest_price = stock_data['close'].iloc[-1] if not stock_data.empty else 0
                
                # Calculate SMA values
                sma20 = tech_indicators.get('sma_short', pd.Series()).iloc[-1] if 'sma_short' in tech_indicators and not tech_indicators['sma_short'].empty else None
                sma50 = tech_indicators.get('sma_medium', pd.Series()).iloc[-1] if 'sma_medium' in tech_indicators and not tech_indicators['sma_medium'].empty else None
                sma200 = tech_indicators.get('sma_long', pd.Series()).iloc[-1] if 'sma_long' in tech_indicators and not tech_indicators['sma_long'].empty else None
                
                # Compare price to SMAs
                vs_sma20 = "Above" if sma20 is not None and latest_price > sma20 else "Below" if sma20 is not None else "N/A"
                vs_sma50 = "Above" if sma50 is not None and latest_price > sma50 else "Below" if sma50 is not None else "N/A"
                vs_sma200 = "Above" if sma200 is not None and latest_price > sma200 else "Below" if sma200 is not None else "N/A"
                
                # Get MACD signal
                macd_signal = "Bullish" if tech_signals.get('macd_bullish_cross', False) else "Bearish" if tech_signals.get('macd_bearish_cross', False) else "Neutral"
                
                # Check for near 52-week high
                near_52w_high = "Yes" if tech_signals.get('near_52w_high', False) else "No"
                
                # Check for breakout
                breakout = "Yes" if tech_signals.get('breakout_up', False) else "No"
                
                # Determine signal strength (as percentage)
                # If tech_score is None or 0, use a default neutral value of 50%
                if tech_score is None or tech_score == 0:
                    tech_score = 50  # Set a neutral default score
                
                signal_strength = f"{tech_score}%"
                
                # Prepare fundamentals data
                pe_ratio = fundamentals.get('pe_ratio', None)
                profit_margin = fundamentals.get('profit_margin', None)
                revenue_growth = fundamentals.get('revenue_growth', None)
                fund_ok = "Yes" if fund_analysis['overall'].get('value_momentum_pass', False) else "No"
                
                # Add to results
                results.append({
                    'Ticker': ticker,
                    'Name': stock_name,
                    'Last Price': last_price,
                    'Tech Score': tech_score,
                    'Signal': signal,
                    'Strength': signal_strength,
                    'RSI': rsi_value,
                    'vs SMA20': vs_sma20,
                    'vs SMA50': vs_sma50,
                    'vs SMA200': vs_sma200,
                    'MACD': macd_signal,
                    'Near 52w High': near_52w_high,
                    'Breakout': breakout,
                    'P/E Ratio': pe_ratio,
                    'Profit Margin': profit_margin,
                    'Revenue Growth': revenue_growth,
                    'Fund OK': fund_ok
                })
                
            except Exception as e:
                failed.append(ticker)
                print(f"Error processing {ticker}: {e}")
                
            # Check if scanner was stopped during ticker processing
            if not st.session_state.get('scanner_running', True):
                status_text.warning("Scanner stopped by user")
                break
        
        # After batch completes, update results DataFrame
        if results:
            # Convert to DataFrame
            results_df = pd.DataFrame(results)
            
            # Store in session state
            st.session_state.scan_results = results_df
            
            # Store failed tickers
            st.session_state.failed_tickers = failed
            
        # Add delay between batches if continuous_scan is enabled
        if continuous_scan and batch_idx < total_batches - 1:
            time.sleep(1)  # 1-second delay to avoid rate limits
    
    # Complete progress bar when done
    progress_bar.progress(1.0)
    
    # Update status
    st.session_state.scanner_running = False
    if failed:
        status_text.warning(f"Scan complete with {len(failed)} failures")
    else:
        status_text.success("Scan complete!")
    
    # Return results
    return results