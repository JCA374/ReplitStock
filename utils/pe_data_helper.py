"""
Utility functions for enhancing P/E data in batch analysis results
"""
import logging
from data.stock_data import StockDataFetcher

logger = logging.getLogger(__name__)

def add_pe_data_to_results(results):
    """
    Add P/E ratio data to batch analysis results where missing.
    
    Args:
        results: List of analysis result dictionaries
        
    Returns:
        List of enhanced results with P/E ratio data where possible
    """
    fetcher = StockDataFetcher()
    
    logger.info(f"Enhancing P/E data for {len(results)} results")
    pe_count = 0
    
    for result in results:
        if 'error' in result and result['error'] is not None:
            continue  # Skip results with errors
            
        if 'pe_ratio' not in result or result['pe_ratio'] is None:
            ticker = result.get('ticker')
            if ticker:
                try:
                    # Try to fetch fundamentals
                    fundamentals = fetcher.get_fundamentals(ticker)
                    if fundamentals and fundamentals.get('pe_ratio') is not None:
                        result['pe_ratio'] = fundamentals['pe_ratio']
                        pe_count += 1
                        
                        # Also update other fundamental metrics if missing
                        if 'profit_margin' not in result or result['profit_margin'] is None:
                            result['profit_margin'] = fundamentals.get('profit_margin')
                            
                        if 'revenue_growth' not in result or result['revenue_growth'] is None:
                            result['revenue_growth'] = fundamentals.get('revenue_growth')
                except Exception as e:
                    logger.error(f"Error enhancing data for {ticker}: {e}")
    
    logger.info(f"Added P/E data to {pe_count} results")
    return results