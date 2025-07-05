"""
Utility functions for cleaning and normalizing ticker symbols from CSV files
"""

import pandas as pd
import re

def clean_ticker(ticker):
    """
    Clean and normalize a ticker symbol for Yahoo Finance compatibility
    
    Args:
        ticker (str): Raw ticker from CSV
        
    Returns:
        str: Cleaned ticker with proper .ST suffix
    """
    if pd.isna(ticker) or not ticker or ticker.strip() == '':
        return None
        
    ticker = str(ticker).strip().upper()
    
    # Skip empty or invalid tickers
    if ticker in ['.ST', 'ST', '']:
        return None
    
    # Handle tickers that are just "ST" without the dot
    if ticker == 'ST':
        return None
        
    # Fix common malformed patterns
    patterns = [
        (r'([A-Z0-9-]+)ST$', r'\1.ST'),  # ACADST -> ACAD.ST
        (r'([A-Z0-9-]+)\.ST\.ST$', r'\1.ST'),  # Remove double .ST
        (r'^([A-Z0-9-]+)$(?!\.ST)', r'\1.ST'),  # Add .ST if missing
    ]
    
    for pattern, replacement in patterns:
        ticker = re.sub(pattern, replacement, ticker)
    
    # Ensure it ends with .ST if it's a Swedish stock
    if not ticker.endswith('.ST') and not ticker.endswith('.US'):
        ticker = ticker + '.ST'
    
    return ticker

def load_and_clean_csv_tickers(csv_path):
    """
    Load tickers from CSV and clean them
    
    Args:
        csv_path (str): Path to CSV file
        
    Returns:
        list: List of cleaned tickers
    """
    try:
        df = pd.read_csv(csv_path)
        
        if 'YahooTicker' not in df.columns:
            return []
            
        tickers = []
        for ticker in df['YahooTicker'].tolist():
            cleaned = clean_ticker(ticker)
            if cleaned:
                tickers.append(cleaned)
                
        return tickers
        
    except Exception as e:
        print(f"Error loading CSV {csv_path}: {e}")
        return []

def validate_tickers(tickers):
    """
    Validate that tickers follow expected format
    
    Args:
        tickers (list): List of ticker symbols
        
    Returns:
        tuple: (valid_tickers, invalid_tickers)
    """
    valid = []
    invalid = []
    
    for ticker in tickers:
        if ticker and re.match(r'^[A-Z0-9-]+\.ST$', ticker):
            valid.append(ticker)
        else:
            invalid.append(ticker)
            
    return valid, invalid