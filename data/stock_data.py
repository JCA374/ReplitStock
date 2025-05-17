import yfinance as yf
from alpha_vantage.timeseries import TimeSeries
import pandas as pd
import numpy as np
from datetime import datetime
import time
import logging
import os

from config import (
    ALPHA_VANTAGE_API_KEY, 
    YAHOO_FINANCE_ENABLED,
    TIMEFRAMES,
    PERIOD_OPTIONS,
    STOCKHOLM_EXCHANGE_SUFFIX
)

# Use the database integration layer to get data from both SQLite and Supabase
from data.db_integration import (
    cache_stock_data, 
    get_cached_stock_data,
    cache_fundamentals,
    get_cached_fundamentals
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockDataFetcher:
    def __init__(self):
        self.alpha_vantage_api_key = ALPHA_VANTAGE_API_KEY
        self.yahoo_finance_enabled = YAHOO_FINANCE_ENABLED
        
        # Initialize Alpha Vantage client if API key is available
        if self.alpha_vantage_api_key:
            self.alpha_vantage = TimeSeries(key=self.alpha_vantage_api_key, output_format='pandas')
        else:
            self.alpha_vantage = None
            logger.warning("Alpha Vantage API key not provided. Fallback source unavailable.")
    
    def get_stock_data(self, ticker, timeframe='1d', period='1y', attempt_fallback=True):
        """
        Get stock price data from primary source, with fallback to secondary source.
        
        Args:
            ticker (str): Stock ticker symbol
            timeframe (str): Timeframe for data (1d, 1wk, 1mo)
            period (str): Period to fetch (1mo, 3mo, 6mo, 1y, etc.)
            attempt_fallback (bool): Whether to try fallback source if primary fails
            
        Returns:
            pandas.DataFrame: Stock price data
        """
        # Check for cached data first
        cached_data = get_cached_stock_data(ticker, timeframe, period, "yahoo")
        if cached_data is not None:
            logger.info(f"Retrieved cached data for {ticker}")
            return cached_data
        
        # Try primary source (Yahoo Finance)
        if self.yahoo_finance_enabled:
            try:
                logger.info(f"Fetching {ticker} data from Yahoo Finance")
                data = self._get_data_from_yahoo(ticker, timeframe, period)
                if data is not None and not data.empty:
                    # Cache the data
                    cache_stock_data(ticker, timeframe, period, data, "yahoo")
                    return data
            except Exception as e:
                logger.error(f"Error fetching data from Yahoo Finance: {e}")
                
        # Fallback to Alpha Vantage if primary source failed and fallback is enabled
        if attempt_fallback and self.alpha_vantage_api_key:
            try:
                logger.info(f"Fetching {ticker} data from Alpha Vantage (fallback)")
                # Check if alpha vantage cached data exists
                cached_av_data = get_cached_stock_data(ticker, timeframe, period, "alphavantage")
                if cached_av_data is not None:
                    return cached_av_data
                    
                data = self._get_data_from_alpha_vantage(ticker, timeframe, period)
                if data is not None and not data.empty:
                    # Cache the data
                    cache_stock_data(ticker, timeframe, period, data, "alphavantage")
                    return data
            except Exception as e:
                logger.error(f"Error fetching data from Alpha Vantage: {e}")
                
        # If we've reached here, both sources failed
        return pd.DataFrame()
    
    def _get_data_from_yahoo(self, ticker, timeframe, period):
        """Fetch stock data from Yahoo Finance."""
        # Handle Swedish stock tickers
        if ticker.endswith(STOCKHOLM_EXCHANGE_SUFFIX) or ticker.upper().endswith(".ST"):
            if not ticker.endswith(STOCKHOLM_EXCHANGE_SUFFIX):
                ticker = f"{ticker}{STOCKHOLM_EXCHANGE_SUFFIX}"
        
        stock = yf.Ticker(ticker)
        data = stock.history(period=period, interval=timeframe)
        
        # Rename columns to standard format
        if not data.empty:
            data = data.rename(columns={
                'Open': 'open', 
                'High': 'high', 
                'Low': 'low', 
                'Close': 'close', 
                'Volume': 'volume'
            })
        
        return data
    
    def _get_data_from_alpha_vantage(self, ticker, timeframe, period):
        """Fetch stock data from Alpha Vantage."""
        if self.alpha_vantage is None:
            return pd.DataFrame()
        
        # Map timeframe to Alpha Vantage format
        av_timeframe_map = {
            '1d': 'daily',
            '1wk': 'weekly',
            '1mo': 'monthly'
        }
        
        # Map period to output size
        output_size = 'full' if period in ['1y', '2y', '5y', 'max'] else 'compact'
        
        # Get appropriate function based on timeframe
        av_timeframe = av_timeframe_map.get(timeframe, 'daily')
        
        if av_timeframe == 'daily':
            data, meta_data = self.alpha_vantage.get_daily(symbol=ticker, outputsize=output_size)
        elif av_timeframe == 'weekly':
            data, meta_data = self.alpha_vantage.get_weekly(symbol=ticker)
        elif av_timeframe == 'monthly':
            data, meta_data = self.alpha_vantage.get_monthly(symbol=ticker)
        
        # Rename columns to standard format
        data = data.rename(columns={
            '1. open': 'open', 
            '2. high': 'high', 
            '3. low': 'low', 
            '4. close': 'close', 
            '5. volume': 'volume'
        })
        
        # Sort by date (Alpha Vantage returns newest first)
        data = data.sort_index()
        
        # Trim data to match requested period
        if period != 'max':
            # Map period string to number of months
            period_map = {
                '1mo': 1,
                '3mo': 3,
                '6mo': 6,
                'ytd': (datetime.now().month),  # Current month number
                '1y': 12,
                '2y': 24,
                '5y': 60
            }
            
            months = period_map.get(period, 12)  # Default to 1 year
            
            # Calculate cutoff date
            last_date = data.index[-1]
            if isinstance(last_date, str):
                last_date = pd.to_datetime(last_date)
                
            if months > 0:
                cutoff_date = last_date - pd.DateOffset(months=months)
                data = data[data.index >= cutoff_date]
        
        return data
    
    def get_stock_info(self, ticker):
        """Get basic stock information."""
        try:
            # Try Yahoo Finance first
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Extract relevant info
            stock_info = {
                'name': info.get('shortName', ticker),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'exchange': info.get('exchange', 'Unknown'),
                'currency': info.get('currency', 'Unknown'),
                'country': info.get('country', 'Unknown')
            }
            
            return stock_info
            
        except Exception as e:
            logger.error(f"Error fetching stock info for {ticker}: {e}")
            # Return basic info
            return {
                'name': ticker,
                'sector': 'Unknown',
                'industry': 'Unknown',
                'exchange': 'Unknown',
                'currency': 'Unknown',
                'country': 'Unknown'
            }
    
    def get_fundamentals(self, ticker):
        """Get fundamental data for a stock."""
        # Check cache first
        cached_fundamentals = get_cached_fundamentals(ticker)
        if cached_fundamentals:
            return cached_fundamentals
        
        try:
            # Use Yahoo Finance for fundamentals
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Get financial data
            try:
                balance_sheet = stock.balance_sheet
                income_stmt = stock.income_stmt
                cash_flow = stock.cashflow
                has_financials = not balance_sheet.empty and not income_stmt.empty
            except Exception:
                has_financials = False
            
            # Calculate fundamental metrics with validation
            fundamentals = {}
            
            # Valuation metrics
            fundamentals['pe_ratio'] = info.get('trailingPE') if isinstance(info.get('trailingPE'), (int, float)) else None
            fundamentals['forward_pe'] = info.get('forwardPE') if isinstance(info.get('forwardPE'), (int, float)) else None
            fundamentals['peg_ratio'] = info.get('pegRatio') if isinstance(info.get('pegRatio'), (int, float)) else None
            fundamentals['price_to_book'] = info.get('priceToBook') if isinstance(info.get('priceToBook'), (int, float)) else None
            fundamentals['enterprise_value'] = info.get('enterpriseValue') if isinstance(info.get('enterpriseValue'), (int, float)) else None
            
            # Profitability metrics
            fundamentals['profit_margin'] = info.get('profitMargins') if isinstance(info.get('profitMargins'), (int, float)) else None
            fundamentals['operating_margin'] = info.get('operatingMargins') if isinstance(info.get('operatingMargins'), (int, float)) else None
            fundamentals['roa'] = info.get('returnOnAssets') if isinstance(info.get('returnOnAssets'), (int, float)) else None
            fundamentals['roe'] = info.get('returnOnEquity') if isinstance(info.get('returnOnEquity'), (int, float)) else None
            
            # Growth metrics (calculated from financial statements)
            fundamentals['revenue_growth'] = None
            fundamentals['earnings_growth'] = None
            
            # Financial health
            fundamentals['book_value'] = info.get('bookValue') if isinstance(info.get('bookValue'), (int, float)) else None
            fundamentals['market_cap'] = info.get('marketCap') if isinstance(info.get('marketCap'), (int, float)) else None
            fundamentals['dividend_yield'] = info.get('dividendYield') if isinstance(info.get('dividendYield'), (int, float)) else None
            fundamentals['debt_to_equity'] = info.get('debtToEquity') if isinstance(info.get('debtToEquity'), (int, float)) else None
            fundamentals['current_ratio'] = info.get('currentRatio') if isinstance(info.get('currentRatio'), (int, float)) else None
            
            # Calculate growth metrics if financial data is available
            if has_financials:
                # Calculate revenue growth
                if not income_stmt.empty and 'Total Revenue' in income_stmt.index:
                    revenues = income_stmt.loc['Total Revenue']
                    if len(revenues) >= 2:
                        latest_revenue = revenues.iloc[0]
                        previous_revenue = revenues.iloc[1]
                        if previous_revenue and previous_revenue > 0:
                            fundamentals['revenue_growth'] = (latest_revenue - previous_revenue) / previous_revenue
                
                # Calculate earnings growth
                if not income_stmt.empty and 'Net Income' in income_stmt.index:
                    earnings = income_stmt.loc['Net Income']
                    if len(earnings) >= 2:
                        latest_earnings = earnings.iloc[0]
                        previous_earnings = earnings.iloc[1]
                        if previous_earnings and previous_earnings > 0:
                            fundamentals['earnings_growth'] = (latest_earnings - previous_earnings) / previous_earnings
            
            # Cache the fundamentals
            cache_fundamentals(ticker, fundamentals)
            
            return fundamentals
            
        except Exception as e:
            logger.error(f"Error fetching fundamentals for {ticker}: {e}")
            return {
                'pe_ratio': None,
                'profit_margin': None,
                'revenue_growth': None,
                'earnings_growth': None,
                'book_value': None,
                'market_cap': None,
                'dividend_yield': None,
            }

    def search_stock(self, query):
        """Search for a stock by name or ticker."""
        try:
            # Use yfinance for search
            tickers = yf.Tickers(query)
            results = []
            
            # This is a workaround as yfinance doesn't have a direct search function
            # We'll try some common suffixes for the query
            suffixes = ['', '.ST', '.TO', '.L', '.F', '.PA', '.AS', '.BR', '.MI', '.MC', '.HK']
            
            for suffix in suffixes:
                try:
                    test_ticker = f"{query}{suffix}"
                    stock = yf.Ticker(test_ticker)
                    info = stock.info
                    
                    # Check if we got valid data
                    if 'shortName' in info and info['shortName']:
                        results.append({
                            'ticker': test_ticker,
                            'name': info['shortName'],
                            'exchange': info.get('exchange', 'Unknown'),
                            'sector': info.get('sector', 'Unknown')
                        })
                except:
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching for stock {query}: {e}")
            return []
