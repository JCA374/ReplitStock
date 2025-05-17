import pandas as pd
from data.db_manager import get_all_fundamentals, get_watchlist, get_cached_stock_data, get_all_cached_stocks
from analysis.technical import calculate_all_indicators, generate_technical_signals
from analysis.fundamental import analyze_fundamentals
from config import SCANNER_CRITERIA

def value_momentum_scan(only_watchlist=False):
    """
    Specialized scanner implementing the Value & Momentum Strategy.
    
    This strategy looks for stocks that:
    1. Have a Tech Score of 70 or higher (technical momentum)
    2. Pass basic fundamental checks (profitable and reasonable valuation)
    
    Args:
        only_watchlist (bool): If True, only scan stocks in the watchlist
        
    Returns:
        list: List of stocks meeting the Value & Momentum criteria
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
        
        # Get key metrics for Value & Momentum Strategy
        
        # 1. Technical momentum score (0-100)
        tech_score = signals.get('tech_score', 0)
        
        # 2. Fundamental "pass/fail" check
        fundamental_pass = fundamental_analysis['overall'].get('value_momentum_pass', False)
        
        # 3. Individual signal components
        above_ma40 = signals.get('above_ma40', False)  # Primary trend
        above_ma4 = signals.get('above_ma4', False)    # Short-term momentum
        rsi_above_50 = signals.get('rsi_above_50', False)  # RSI momentum
        near_52w_high = signals.get('near_52w_high', False)  # Near 52-week high
        
        # 4. Is the stock profitable?
        is_profitable = fundamental_analysis['overall'].get('is_profitable', False)
        
        # 5. Does it have a reasonable P/E?
        reasonable_pe = fundamental_analysis['overall'].get('reasonable_pe', True)
        
        # Determine the Value & Momentum signal
        if tech_score >= 70 and fundamental_pass:
            value_momentum_signal = "BUY"
        elif tech_score < 40 or not above_ma40:
            value_momentum_signal = "SELL"
        else:
            value_momentum_signal = "HOLD"
        
        # Add to results
        last_price = stock_data['close'].iloc[-1] if not stock_data.empty else None
        
        results.append({
            'ticker': ticker,
            'last_price': last_price,
            'pe_ratio': fundamentals.get('pe_ratio'),
            'profit_margin': fundamentals.get('profit_margin'),
            'revenue_growth': fundamentals.get('revenue_growth'),
            'tech_score': tech_score,
            'above_ma40': above_ma40,
            'above_ma4': above_ma4,
            'rsi_above_50': rsi_above_50,
            'near_52w_high': near_52w_high,
            'is_profitable': is_profitable,
            'reasonable_pe': reasonable_pe,
            'fundamental_pass': fundamental_pass,
            'value_momentum_signal': value_momentum_signal
        })
    
    # Sort by tech score (descending)
    results.sort(key=lambda x: x.get('tech_score', 0), reverse=True)
    
    return results

def scan_stocks(criteria, only_watchlist=False):
    """
    Scan stocks based on specified criteria.
    
    Args:
        criteria (dict): Dictionary with criteria keys and values
        only_watchlist (bool): If True, only scan stocks in the watchlist
        
    Returns:
        list: List of stocks meeting the criteria, with details
    """
    # Special case for Value & Momentum Strategy scan
    if criteria.get('strategy') == 'value_momentum':
        return value_momentum_scan(only_watchlist)
    
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
