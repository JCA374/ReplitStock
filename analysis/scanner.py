import pandas as pd
from data.db_manager import get_all_fundamentals, get_watchlist, get_cached_stock_data, get_all_cached_stocks
from analysis.technical import calculate_all_indicators, generate_technical_signals
from analysis.fundamental import analyze_fundamentals
from config import SCANNER_CRITERIA

def scan_stocks(criteria, only_watchlist=False):
    """
    Scan stocks based on specified criteria.
    
    Args:
        criteria (dict): Dictionary with criteria keys and values
        only_watchlist (bool): If True, only scan stocks in the watchlist
        
    Returns:
        list: List of stocks meeting the criteria, with details
    """
    # Get list of stocks to scan
    if only_watchlist:
        watchlist = get_watchlist()
        stocks_to_scan = [item['ticker'] for item in watchlist]
    else:
        # Get all stocks in the database
        stocks_to_scan = get_all_cached_stocks()
    
    # If no stocks to scan, return empty list
    if not stocks_to_scan:
        return []
    
    # Get fundamentals for all stocks
    all_fundamentals = get_all_fundamentals()
    fundamentals_by_ticker = {f['ticker']: f for f in all_fundamentals}
    
    # Results list
    results = []
    
    # Scan each stock
    for ticker in stocks_to_scan:
        # Get stock data
        stock_data = get_cached_stock_data(ticker, '1d', '1y', 'yahoo')
        
        if stock_data is None or stock_data.empty:
            continue
            
        # Get fundamentals
        fundamentals = fundamentals_by_ticker.get(ticker, {})
        
        # Calculate technical indicators
        indicators = calculate_all_indicators(stock_data)
        
        # Generate technical signals
        signals = generate_technical_signals(indicators)
        
        # Analyze fundamentals
        fundamental_analysis = analyze_fundamentals(fundamentals)
        
        # Check if the stock meets all criteria
        meets_criteria = True
        
        for criterion, value in criteria.items():
            if criterion == 'pe_below' and fundamentals.get('pe_ratio') is not None:
                if not (fundamentals['pe_ratio'] <= float(value)):
                    meets_criteria = False
                    break
                    
            elif criterion == 'pe_above' and fundamentals.get('pe_ratio') is not None:
                if not (fundamentals['pe_ratio'] >= float(value)):
                    meets_criteria = False
                    break
                    
            elif criterion == 'profit_margin_above' and fundamentals.get('profit_margin') is not None:
                if not (fundamentals['profit_margin'] >= float(value)):
                    meets_criteria = False
                    break
                    
            elif criterion == 'revenue_growth_above' and fundamentals.get('revenue_growth') is not None:
                if not (fundamentals['revenue_growth'] >= float(value)):
                    meets_criteria = False
                    break
                    
            elif criterion == 'price_above_sma' and 'price_above_sma_short' in signals:
                window = int(value)
                if window == 50 and 'price_above_sma_medium' in signals:
                    if not signals['price_above_sma_medium']:
                        meets_criteria = False
                        break
                elif window == 200 and 'price_above_sma_long' in signals:
                    if not signals['price_above_sma_long']:
                        meets_criteria = False
                        break
                elif not signals['price_above_sma_short']:
                    meets_criteria = False
                    break
                    
            elif criterion == 'price_below_sma' and 'price_above_sma_short' in signals:
                window = int(value)
                if window == 50 and 'price_above_sma_medium' in signals:
                    if signals['price_above_sma_medium']:
                        meets_criteria = False
                        break
                elif window == 200 and 'price_above_sma_long' in signals:
                    if signals['price_above_sma_long']:
                        meets_criteria = False
                        break
                elif signals['price_above_sma_short']:
                    meets_criteria = False
                    break
                    
            elif criterion == 'rsi_overbought' and 'rsi_overbought' in signals:
                if not signals['rsi_overbought']:
                    meets_criteria = False
                    break
                    
            elif criterion == 'rsi_oversold' and 'rsi_oversold' in signals:
                if not signals['rsi_oversold']:
                    meets_criteria = False
                    break
                    
            elif criterion == 'macd_bullish' and 'macd_bullish_cross' in signals:
                if not signals['macd_bullish_cross']:
                    meets_criteria = False
                    break
                    
            elif criterion == 'macd_bearish' and 'macd_bearish_cross' in signals:
                if not signals['macd_bearish_cross']:
                    meets_criteria = False
                    break
                    
            elif criterion == 'price_near_52w_high' and 'near_52w_high' in signals:
                if not signals['near_52w_high']:
                    meets_criteria = False
                    break
                    
            elif criterion == 'price_near_52w_low' and 'near_52w_low' in signals:
                if not signals['near_52w_low']:
                    meets_criteria = False
                    break
        
        # If the stock meets all criteria, add it to the results
        if meets_criteria:
            # Get last price
            last_price = stock_data['close'].iloc[-1] if not stock_data.empty else None
            
            # Add to results
            results.append({
                'ticker': ticker,
                'last_price': last_price,
                'pe_ratio': fundamentals.get('pe_ratio'),
                'profit_margin': fundamentals.get('profit_margin'),
                'revenue_growth': fundamentals.get('revenue_growth'),
                'technical_signal': signals.get('overall_signal'),
                'signal_strength': signals.get('signal_strength'),
                'fundamental_status': fundamental_analysis['overall']['status']
            })
    
    return results
