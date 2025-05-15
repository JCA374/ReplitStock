from config import STOCKHOLM_EXCHANGE_SUFFIX

def normalize_ticker(ticker):
    """
    Normalize ticker symbols, handling special cases like Swedish stocks.
    
    Args:
        ticker (str): The ticker symbol to normalize
        
    Returns:
        str: Normalized ticker symbol
    """
    if not ticker:
        return ticker
    
    # Remove any whitespace
    ticker = ticker.strip()
    
    # Convert to uppercase
    ticker = ticker.upper()
    
    # Handle Swedish stocks - ensure they have the .ST suffix
    if ticker.endswith(".ST"):
        return ticker
    
    # Check if it's likely a Swedish stock (common formats)
    swedish_formats = [
        '.STO', 'STO:', '.SS', '-STO',  # Common variations
        '.STOCKHOLM', 'STOCKHOLM:', '.SE', '-SE'  # Less common but possible
    ]
    
    for fmt in swedish_formats:
        if ticker.endswith(fmt):
            # Replace with the standard .ST suffix
            return ticker.replace(fmt, STOCKHOLM_EXCHANGE_SUFFIX)
    
    return ticker

def get_equivalent_tickers(ticker):
    """
    Get equivalent ticker symbols for different data providers.
    
    Args:
        ticker (str): Base ticker symbol
        
    Returns:
        dict: Dictionary with equivalent tickers for different providers
    """
    normalized = normalize_ticker(ticker)
    
    # Handle Swedish stocks specially
    if normalized.endswith(STOCKHOLM_EXCHANGE_SUFFIX):
        base_ticker = normalized.replace(STOCKHOLM_EXCHANGE_SUFFIX, '')
        return {
            'yahoo': normalized,
            'alpha_vantage': base_ticker + '.STO',
            'nasdaq': base_ticker + '-SEK',
            'bloomberg': base_ticker + 'SS',
            'reuters': base_ticker + '.ST'
        }
    
    # For regular US stocks
    return {
        'yahoo': normalized,
        'alpha_vantage': normalized,
        'nasdaq': normalized,
        'bloomberg': normalized,
        'reuters': normalized
    }
