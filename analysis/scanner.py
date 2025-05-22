import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

# Import database connections
from data.db_manager import get_all_fundamentals, get_watchlist, get_cached_stock_data, get_all_cached_stocks
from analysis.technical import calculate_all_indicators, generate_technical_signals
from analysis.fundamental import analyze_fundamentals
from config import SCANNER_CRITERIA

def value_momentum_scan(only_watchlist=False):
    """
    Specialized scanner implementing the Value & Momentum Strategy.
    Optimized to use only cached database data without API searches.
    
    This strategy looks for stocks that:
    1. Have a Tech Score of 70 or higher (technical momentum)
    2. Pass basic fundamental checks (profitable and reasonable valuation)
    
    Args:
        only_watchlist (bool): If True, only scan stocks in the watchlist
        
    Returns:
        list: List of stocks meeting the Value & Momentum criteria
    """
    # Use the EnhancedScanner to perform the scan from both databases
    scanner = EnhancedScanner(use_supabase=True, use_sqlite=True)
    
    # Get list of stocks to scan
    if only_watchlist:
        watchlist = get_watchlist()
        stocks_to_scan = [item['ticker'] for item in watchlist]
    else:
        # Get all stocks from both databases (without API calls)
        stocks_to_scan = set()
        
        # Get stocks from SQLite
        sqlite_stocks = get_all_cached_stocks()
        if sqlite_stocks:
            stocks_to_scan.update(sqlite_stocks)
        
        # Get stocks from Supabase if available
        try:
            from data.supabase_client import get_supabase_db
            supabase_db = get_supabase_db()
            
            if supabase_db.is_connected():
                supabase_stocks = supabase_db.get_all_cached_stocks()
                if supabase_stocks:
                    stocks_to_scan.update(supabase_stocks)
        except Exception as e:
            print(f"Error getting Supabase stocks: {e}")
        
        # Convert to list
        stocks_to_scan = list(stocks_to_scan)
    
    # If no stocks to scan, return empty list
    if not stocks_to_scan:
        return []
    
    # Pre-fetch fundamentals for all stocks (from both databases)
    all_fundamentals = {}
    
    # Get fundamentals from SQLite
    sqlite_fundamentals = get_all_fundamentals()
    for f in sqlite_fundamentals:
        ticker = f.get('ticker')
        if ticker:
            all_fundamentals[ticker] = f
    
    # Get fundamentals from Supabase if available
    try:
        from data.supabase_client import get_supabase_db
        supabase_db = get_supabase_db()
        
        if supabase_db.is_connected():
            supabase_fundamentals = supabase_db.get_all_fundamentals()
            for f in supabase_fundamentals:
                ticker = f.get('ticker')
                if ticker:
                    # Only override if not already in dictionary (prioritize Supabase)
                    if ticker not in all_fundamentals:
                        all_fundamentals[ticker] = f
    except Exception as e:
        print(f"Error getting Supabase fundamentals: {e}")
    
    # Results list
    results = []
    
    # Scan each stock
    for ticker in stocks_to_scan:
        # Get stock data from both databases without API calls
        stock_data, fundamentals, data_source = scanner.get_data_from_both_dbs(ticker, '1d', '1y')
        
        if stock_data is None or stock_data.empty:
            continue
            
        # Use pre-fetched fundamentals if available
        if not fundamentals and ticker in all_fundamentals:
            fundamentals = all_fundamentals[ticker]
        
        # Calculate technical indicators
        indicators = calculate_all_indicators(stock_data)
        
        # Generate technical signals
        signals = generate_technical_signals(indicators)
        
        # Analyze fundamentals
        fundamental_analysis = analyze_fundamentals(fundamentals or {})
        
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
            'pe_ratio': fundamentals.get('pe_ratio') if fundamentals else None,
            'profit_margin': fundamentals.get('profit_margin') if fundamentals else None,
            'revenue_growth': fundamentals.get('revenue_growth') if fundamentals else None,
            'tech_score': tech_score,
            'above_ma40': above_ma40,
            'above_ma4': above_ma4,
            'rsi_above_50': rsi_above_50,
            'near_52w_high': near_52w_high,
            'is_profitable': is_profitable,
            'reasonable_pe': reasonable_pe,
            'fundamental_pass': fundamental_pass,
            'value_momentum_signal': value_momentum_signal,
            'data_source': data_source or "unknown"
        })
    
    # Sort by tech score (descending)
    results.sort(key=lambda x: x.get('tech_score', 0), reverse=True)
    
    return results

class EnhancedScanner:
    """Enhanced stock scanner with support for multiple databases and advanced ranking."""
    
    def __init__(self, use_supabase=True, use_sqlite=True):
        """
        Initialize the scanner with database preferences.
        
        Args:
            use_supabase (bool): Whether to use Supabase data
            use_sqlite (bool): Whether to use SQLite data
        """
        self.use_supabase = use_supabase
        self.use_sqlite = use_sqlite
        
        # Ensure at least one database is enabled
        if not use_supabase and not use_sqlite:
            self.use_sqlite = True
            print("Warning: No database specified, defaulting to SQLite")
    
    def get_data_from_both_dbs(self, ticker, timeframe='1wk', period='1y'):
        """
        Get stock data from both databases, prioritizing Supabase.
        Optimized to avoid API calls and reduce database queries.
        
        Args:
            ticker (str): Stock ticker symbol
            timeframe (str): Data timeframe
            period (str): Data period
            
        Returns:
            tuple: (stock_data, fundamentals, source)
        """
        stock_data = None
        fundamentals = None
        data_source = None
        
        # Try Supabase first if enabled
        if self.use_supabase:
            from data.supabase_client import get_supabase_db
            supabase_db = get_supabase_db()
            
            if supabase_db.is_connected():
                # Get data only from cache, without triggering API calls
                stock_data = supabase_db.get_cached_stock_data(ticker, timeframe, period, 'yahoo')
                fundamentals = supabase_db.get_cached_fundamentals(ticker)
                
                if stock_data is not None or fundamentals is not None:
                    data_source = "supabase"
        
        # If data is missing, try SQLite if enabled
        if (stock_data is None or fundamentals is None) and self.use_sqlite:
            # Only get what's missing
            if stock_data is None:
                # Get data only from cache, without triggering API calls
                stock_data = get_cached_stock_data(ticker, timeframe, period, 'yahoo')
            
            if fundamentals is None:
                # Get fundamentals directly for this ticker instead of getting all
                from data.db_manager import get_cached_fundamentals
                fundamentals = get_cached_fundamentals(ticker)
            
            if stock_data is not None or fundamentals is not None:
                data_source = "sqlite" if data_source is None else "combined"
        
        return stock_data, fundamentals, data_source
    
    def scan_stocks(self, criteria, stock_list=None, progress_callback=None, database_only=False):
        """
        Scan stocks based on criteria, using data from both databases without API searches.
        
        Args:
            criteria (dict): Dictionary of filtering criteria
            stock_list (list, optional): List of stock tickers to scan. If None, all stocks are scanned.
            progress_callback (function, optional): Callback for progress updates
            database_only (bool): If True, only use data from databases without API calls
            
        Returns:
            list: List of stocks meeting the criteria
        """
        # Determine which stocks to scan
        if stock_list is None:
            # Get all unique stocks from both databases without API calls
            stocks_to_scan = set()
            
            if self.use_sqlite:
                # Get all cached stocks from SQLite
                sqlite_stocks = get_all_cached_stocks()
                if sqlite_stocks:
                    stocks_to_scan.update(sqlite_stocks)
            
            if self.use_supabase:
                from data.supabase_client import get_supabase_db
                supabase_db = get_supabase_db()
                
                if supabase_db.is_connected():
                    # Get all cached stocks from Supabase
                    supabase_stocks = supabase_db.get_all_cached_stocks()
                    if supabase_stocks:
                        stocks_to_scan.update(supabase_stocks)
            
            # Convert to list
            stocks_to_scan = list(stocks_to_scan)
        else:
            stocks_to_scan = stock_list
        
        # No stocks to scan
        if not stocks_to_scan:
            return []
        
        # Pre-fetch fundamentals for all stocks to avoid repeated queries
        all_fundamentals = {}
        
        # Get fundamentals from SQLite if enabled
        if self.use_sqlite:
            sqlite_fundamentals = get_all_fundamentals()
            for f in sqlite_fundamentals:
                ticker = f.get('ticker')
                if ticker:
                    all_fundamentals[ticker] = f
        
        # Get fundamentals from Supabase if enabled
        if self.use_supabase:
            from data.supabase_client import get_supabase_db
            supabase_db = get_supabase_db()
            
            if supabase_db.is_connected():
                supabase_fundamentals = supabase_db.get_all_fundamentals()
                for f in supabase_fundamentals:
                    ticker = f.get('ticker')
                    if ticker:
                        # Only override if not already in dictionary (prioritize Supabase)
                        if ticker not in all_fundamentals:
                            all_fundamentals[ticker] = f
        
        # Results list
        results = []
        
        # Process each stock
        for i, ticker in enumerate(stocks_to_scan):
            # Update progress if callback provided
            if progress_callback:
                progress = (i + 1) / len(stocks_to_scan)
                progress_callback(progress, f"Analyzing {ticker} ({i+1}/{len(stocks_to_scan)})")
            
            try:
                # Get data from both databases without API calls
                stock_data, fundamentals, data_source = self.get_data_from_both_dbs(ticker)
                
                # Skip if no stock data available
                if stock_data is None or stock_data.empty:
                    continue
                
                # Use pre-fetched fundamentals if available
                if not fundamentals and ticker in all_fundamentals:
                    fundamentals = all_fundamentals[ticker]
                    if data_source == "supabase":
                        data_source = "combined"
                
                # Calculate technical indicators
                indicators = calculate_all_indicators(stock_data)
                
                # Generate technical signals
                signals = generate_technical_signals(indicators)
                
                # Analyze fundamentals if available
                fundamental_analysis = analyze_fundamentals(fundamentals or {})
                
                # Get latest price
                latest_price = stock_data['close'].iloc[-1] if not stock_data.empty else None
                
                # Create result dictionary
                result = {
                    "ticker": ticker,
                    "name": fundamentals.get("name", ticker) if fundamentals else ticker,
                    "price": latest_price,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    # Technical indicators
                    "tech_score": signals.get('tech_score', 0),
                    "signal": signals.get('overall_signal', 'HOLD'),
                    "above_ma40": signals.get('above_ma40', False),
                    "above_ma4": signals.get('above_ma4', False),
                    "rsi": signals.get('rsi', None),
                    "rsi_above_50": signals.get('rsi_above_50', False),
                    "near_52w_high": signals.get('near_52w_high', False),
                    "breakout": signals.get('breakout', False),
                    # Fundamental indicators
                    "pe_ratio": fundamentals.get('pe_ratio') if fundamentals else None,
                    "profit_margin": fundamentals.get('profit_margin') if fundamentals else None,
                    "revenue_growth": fundamentals.get('revenue_growth') if fundamentals else None,
                    "earnings_growth": fundamentals.get('earnings_growth') if fundamentals else None,
                    "is_profitable": fundamental_analysis.get('overall', {}).get('is_profitable', False),
                    "fundamental_pass": fundamental_analysis.get('overall', {}).get('value_momentum_pass', False),
                    # Additional info
                    "sector": fundamentals.get('sector', "") if fundamentals else "",
                    "exchange": fundamentals.get('exchange', "") if fundamentals else "",
                    "data_source": data_source or "unknown"
                }
                
                # Check if the stock meets Value & Momentum Strategy criteria
                if criteria.get('strategy') == 'value_momentum':
                    # Include if tech score >= 70 and passes fundamental check
                    if signals.get('tech_score', 0) >= 70 and fundamental_analysis.get('overall', {}).get('value_momentum_pass', False):
                        results.append(result)
                    continue
                
                # For custom criteria, check each criterion
                meets_criteria = True
                
                # Apply filtering criteria
                for criterion, value in criteria.items():
                    if criterion == 'strategy':
                        # Skip strategy flag
                        continue
                    elif criterion == 'sectors' and value:
                        # Filter by sector
                        if result.get('sector', '') not in value:
                            meets_criteria = False
                            break
                    elif criterion == 'data_sources' and value:
                        # Filter by data source
                        if result.get('data_source', '') not in value:
                            meets_criteria = False
                            break
                    elif criterion == 'min_tech_score':
                        # Minimum tech score
                        if result.get('tech_score', 0) < value:
                            meets_criteria = False
                            break
                    elif criterion == 'pe_below' and result.get('pe_ratio') is not None:
                        # P/E ratio below value
                        if result['pe_ratio'] > value:
                            meets_criteria = False
                            break
                    elif criterion == 'pe_above' and result.get('pe_ratio') is not None:
                        # P/E ratio above value
                        if result['pe_ratio'] < value:
                            meets_criteria = False
                            break
                    elif criterion == 'profit_margin_above' and result.get('profit_margin') is not None:
                        # Profit margin above value
                        if result['profit_margin'] < value:
                            meets_criteria = False
                            break
                    elif criterion == 'revenue_growth_above' and result.get('revenue_growth') is not None:
                        # Revenue growth above value
                        if result['revenue_growth'] < value:
                            meets_criteria = False
                            break
                    elif criterion == 'is_profitable':
                        # Profitable companies only
                        if not result.get('is_profitable', False):
                            meets_criteria = False
                            break
                    elif criterion == 'price_above_sma':
                        # Price above SMA
                        if not signals.get(f'price_above_sma_{value}', False):
                            meets_criteria = False
                            break
                    elif criterion == 'price_below_sma':
                        # Price below SMA
                        if signals.get(f'price_above_sma_{value}', True):
                            meets_criteria = False
                            break
                    elif criterion == 'rsi_overbought':
                        # RSI overbought
                        if not signals.get('rsi_overbought', False):
                            meets_criteria = False
                            break
                    elif criterion == 'rsi_oversold':
                        # RSI oversold
                        if not signals.get('rsi_oversold', False):
                            meets_criteria = False
                            break
                    elif criterion == 'rsi_above_50':
                        # RSI above 50
                        if not signals.get('rsi_above_50', False):
                            meets_criteria = False
                            break
                    elif criterion == 'rsi_below_50':
                        # RSI below 50
                        if signals.get('rsi_above_50', True):
                            meets_criteria = False
                            break
                    elif criterion == 'macd_bullish':
                        # MACD bullish cross
                        if not signals.get('macd_bullish_cross', False):
                            meets_criteria = False
                            break
                    elif criterion == 'macd_bearish':
                        # MACD bearish cross
                        if not signals.get('macd_bearish_cross', False):
                            meets_criteria = False
                            break
                    elif criterion == 'price_near_52w_high':
                        # Price near 52-week high
                        if not signals.get('near_52w_high', False):
                            meets_criteria = False
                            break
                    elif criterion == 'price_near_52w_low':
                        # Price near 52-week low
                        if not signals.get('near_52w_low', False):
                            meets_criteria = False
                            break
                
                # Include stock if it meets criteria
                if meets_criteria:
                    results.append(result)
                
            except Exception as e:
                print(f"Error analyzing {ticker}: {str(e)}")
        
        # Apply ranking if requested
        if criteria.get('rank_by_score', True):
            results = self.rank_stocks(results)
        
        return results
    
    def rank_stocks(self, analysis_results):
        """
        Rank stocks based on a comprehensive scoring system.
        
        Args:
            analysis_results (list): List of stock analysis results
            
        Returns:
            list: Ranked analysis results
        """
        # Remove errors
        valid_results = [r for r in analysis_results if "error" not in r or r["error"] is None]
        
        if not valid_results:
            return []
        
        # Define scoring weights
        weights = {
            # Technical factors (60% of total score)
            'tech_score': 30,                 # Base technical score
            'above_ma40': 10,                 # Primary trend
            'above_ma4': 5,                   # Short-term momentum
            'rsi_above_50': 5,                # RSI momentum
            'near_52w_high': 5,               # Relative strength
            'breakout': 5,                    # Breakout factor
            
            # Fundamental factors (40% of total score)
            'is_profitable': 15,              # Profitability
            'reasonable_pe': 10,              # PE ratio is reasonable 
            'revenue_growth_positive': 10,    # Revenue growth
            'profit_margin_positive': 5       # Profit margin 
        }
        
        # Calculate scores
        for result in valid_results:
            total_score = 0
            applied_weights = 0
            
            # Calculate technical score component
            for factor, weight in weights.items():
                if factor in result:
                    # For boolean factors
                    if isinstance(result[factor], bool):
                        if result[factor]:
                            total_score += weight
                        applied_weights += weight
                    # For numeric factors like tech_score
                    elif factor == 'tech_score' and result[factor] is not None:
                        score_fraction = result[factor] / 100.0
                        total_score += weight * score_fraction
                        applied_weights += weight
                # Special cases for derived factors
                elif factor == 'reasonable_pe':
                    pe_ratio = result.get('pe_ratio')
                    if pe_ratio is not None and 0 < pe_ratio < 30:  # Reasonable PE range
                        total_score += weight
                    applied_weights += weight
                elif factor == 'revenue_growth_positive':
                    growth = result.get('revenue_growth')
                    if growth is not None and growth > 0:
                        total_score += weight
                    applied_weights += weight
                elif factor == 'profit_margin_positive':
                    margin = result.get('profit_margin')
                    if margin is not None and margin > 0:
                        total_score += weight
                    applied_weights += weight
            
            # Calculate normalized score (0-100)
            if applied_weights > 0:
                normalized_score = (total_score / applied_weights) * 100
            else:
                normalized_score = 0
                
            # Add overall score to result
            result['overall_score'] = round(normalized_score, 1)
        
        # Sort by overall score (descending)
        ranked_results = sorted(valid_results, key=lambda x: x.get('overall_score', 0), reverse=True)
        
        # Add rank to each result
        for i, result in enumerate(ranked_results):
            result['rank'] = i + 1
        
        return ranked_results

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
