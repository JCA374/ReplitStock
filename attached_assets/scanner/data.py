# scanner/data.py
import pandas as pd
import csv
import os
import streamlit as st

def load_ticker_list(universe="updated_mid.csv", custom_tickers="", scan_all=True):
    """
    Load ticker list from a CSV file or from custom input.
    
    Args:
        universe (str): The CSV file to load tickers from
        custom_tickers (str): Custom ticker list (comma separated)
        scan_all (bool): If True, scan all tickers, otherwise just the first 20
        
    Returns:
        list: List of ticker pairs (display_name, ticker_symbol)
    """
    tickers = []
    
    # Special case for "Failed Tickers"
    if universe == "Failed Tickers":
        return load_retry_tickers()
    
    # First try to load from custom input
    if custom_tickers:
        custom_list = [t.strip() for t in custom_tickers.split(',')]
        for ticker in custom_list:
            if ticker:  # Skip empty strings
                tickers.append([ticker, ticker])
    
    # Then load from CSV file if it exists
    csv_path = os.path.join('attached_assets', universe)
    if os.path.exists(csv_path):
        try:
            with open(csv_path, 'r') as file:
                reader = csv.reader(file)
                # Skip header
                next(reader, None)
                for row in reader:
                    if len(row) >= 2:
                        # Format is [display_name, ticker_symbol]
                        tickers.append([row[0].strip(), row[1].strip()])
        except Exception as e:
            st.error(f"Error loading ticker list from {universe}: {e}")
    
    # Limit number of tickers if not scan_all
    if not scan_all and len(tickers) > 20:
        tickers = tickers[:20]
    
    return tickers


def load_retry_tickers():
    """
    Load tickers that failed to scan previously.
    
    Returns:
        list: List of ticker pairs (ticker, ticker)
    """
    if 'failed_tickers' in st.session_state and st.session_state.failed_tickers:
        return [[ticker, ticker] for ticker in st.session_state.failed_tickers]
    return []