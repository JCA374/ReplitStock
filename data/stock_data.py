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
            self.alpha_vantage = TimeSeries(
                key=self.alpha_vantage_api_key, output_format='pandas')
            logger.info("Alpha Vantage API initialized")
        else:
            self.alpha_vantage = None
            logger.warning(
                "Alpha Vantage API key not provided. Fallback source unavailable.")

    def get_stock_data(self, ticker, timeframe='1d', period='1y', attempt_fallback=True):
        """
        Get stock price data with priority: Database -> Alpha Vantage -> Yahoo Finance
        
        Args:
            ticker (str): Stock ticker symbol
            timeframe (str): Timeframe for data (1d, 1wk, 1mo)
            period (str): Period to fetch (1mo, 3mo, 6mo, 1y, etc.)
            attempt_fallback (bool): Whether to try fallback sources
            
        Returns:
            pandas.DataFrame: Stock price data
        """
        logger.info(
            f"Fetching data for {ticker} (timeframe: {timeframe}, period: {period})")

        # Step 1: Check database cache first (both sources)
        cached_data = get_cached_stock_data(
            ticker, timeframe, period, "alphavantage")
        if cached_data is not None and not cached_data.empty:
            logger.info(f"Retrieved {ticker} from Alpha Vantage cache")
            return cached_data

        cached_data = get_cached_stock_data(ticker, timeframe, period, "yahoo")
        if cached_data is not None and not cached_data.empty:
            logger.info(f"Retrieved {ticker} from Yahoo cache")
            return cached_data

        # Step 2: Try Alpha Vantage API if available
        if self.alpha_vantage_api_key and attempt_fallback:
            try:
                logger.info(f"Fetching {ticker} from Alpha Vantage API")
                data = self._get_data_from_alpha_vantage(
                    ticker, timeframe, period)
                if data is not None and not data.empty:
                    # Cache the data
                    cache_stock_data(ticker, timeframe, period,
                                     data, "alphavantage")
                    logger.info(
                        f"Successfully fetched {ticker} from Alpha Vantage")
                    return data
            except Exception as e:
                logger.warning(f"Alpha Vantage failed for {ticker}: {e}")

        # Step 3: Try Yahoo Finance as fallback
        if self.yahoo_finance_enabled and attempt_fallback:
            try:
                logger.info(f"Fetching {ticker} from Yahoo Finance (fallback)")
                data = self._get_data_from_yahoo(ticker, timeframe, period)
                if data is not None and not data.empty:
                    # Cache the data
                    cache_stock_data(ticker, timeframe, period, data, "yahoo")
                    logger.info(
                        f"Successfully fetched {ticker} from Yahoo Finance")
                    return data
            except Exception as e:
                logger.error(f"Yahoo Finance failed for {ticker}: {e}")

        # Step 4: Return empty DataFrame if all sources failed
        logger.error(f"All data sources failed for {ticker}")
        return pd.DataFrame()

    def _get_data_from_yahoo(self, ticker, timeframe, period):
        """Fetch stock data from Yahoo Finance with enhanced error handling."""
        try:
            # Handle Swedish stock tickers
            if ticker.endswith(STOCKHOLM_EXCHANGE_SUFFIX) or ticker.upper().endswith(".ST"):
                if not ticker.endswith(STOCKHOLM_EXCHANGE_SUFFIX):
                    ticker = f"{ticker}{STOCKHOLM_EXCHANGE_SUFFIX}"

            # Add small delay to avoid rate limiting
            time.sleep(0.1)

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

                # Ensure we have the required columns
                required_columns = ['open', 'high', 'low', 'close', 'volume']
                for col in required_columns:
                    if col not in data.columns:
                        logger.warning(f"Missing column {col} for {ticker}")
                        data[col] = 0

            return data

        except Exception as e:
            logger.error(f"Error fetching Yahoo data for {ticker}: {e}")
            return pd.DataFrame()

    def _get_data_from_alpha_vantage(self, ticker, timeframe, period):
        """Fetch stock data from Alpha Vantage with enhanced error handling."""
        if self.alpha_vantage is None:
            return pd.DataFrame()

        try:
            # Map timeframe to Alpha Vantage format
            av_timeframe_map = {
                '1d': 'daily',
                '1wk': 'weekly',
                '1mo': 'monthly'
            }

            # Map period to output size
            output_size = 'full' if period in [
                '1y', '2y', '5y', 'max'] else 'compact'

            # Get appropriate function based on timeframe
            av_timeframe = av_timeframe_map.get(timeframe, 'daily')

            # Add delay to respect API rate limits
            time.sleep(12)  # Alpha Vantage free tier: 5 calls per minute

            if av_timeframe == 'daily':
                data, meta_data = self.alpha_vantage.get_daily(
                    symbol=ticker, outputsize=output_size)
            elif av_timeframe == 'weekly':
                data, meta_data = self.alpha_vantage.get_weekly(symbol=ticker)
            elif av_timeframe == 'monthly':
                data, meta_data = self.alpha_vantage.get_monthly(symbol=ticker)
            else:
                return pd.DataFrame()

            if data.empty:
                return pd.DataFrame()

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

        except Exception as e:
            logger.error(
                f"Error fetching Alpha Vantage data for {ticker}: {e}")
            return pd.DataFrame()

    def get_stock_info(self, ticker):
        """Get basic stock information with database-first approach."""
        try:
            # First check if we have cached fundamentals
            cached_fundamentals = get_cached_fundamentals(ticker)
            if cached_fundamentals:
                return {
                    'name': cached_fundamentals.get('name', ticker),
                    'sector': cached_fundamentals.get('sector', 'Unknown'),
                    'industry': cached_fundamentals.get('industry', 'Unknown'),
                    'exchange': cached_fundamentals.get('exchange', 'Unknown'),
                    'currency': cached_fundamentals.get('currency', 'Unknown'),
                    'country': cached_fundamentals.get('country', 'Unknown')
                }

            # Try Yahoo Finance for basic info
            stock = yf.Ticker(ticker)
            info = stock.info

            # Extract relevant info
            stock_info = {
                'name': info.get('shortName', info.get('longName', ticker)),
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
        """Get fundamental data with database-first approach."""
        # Check cache first
        cached_fundamentals = get_cached_fundamentals(ticker)
        if cached_fundamentals:
            logger.info(f"Retrieved cached fundamentals for {ticker}")
            return cached_fundamentals

        try:
            # Use Yahoo Finance for fundamentals
            stock = yf.Ticker(ticker)
            info = stock.info

            logger.info(
                f"Fetching fundamentals for {ticker} from Yahoo Finance")

            # Get financial data
            try:
                balance_sheet = stock.balance_sheet
                income_stmt = stock.income_stmt
                cash_flow = stock.cashflow
                has_financials = not balance_sheet.empty and not income_stmt.empty
            except Exception as e:
                logger.warning(
                    f"Error fetching financial statements for {ticker}: {e}")
                has_financials = False

            # Calculate fundamental metrics with validation
            fundamentals = {}

            # Valuation metrics - Try multiple sources for P/E ratio
            fundamentals['pe_ratio'] = info.get('trailingPE')
            if fundamentals['pe_ratio'] is None or not isinstance(fundamentals['pe_ratio'], (int, float)):
                # Try forward P/E if trailing isn't available
                fundamentals['pe_ratio'] = info.get('forwardPE')

            fundamentals['forward_pe'] = info.get('forwardPE') if isinstance(
                info.get('forwardPE'), (int, float)) else None
            fundamentals['peg_ratio'] = info.get('pegRatio') if isinstance(
                info.get('pegRatio'), (int, float)) else None
            fundamentals['price_to_book'] = info.get('priceToBook') if isinstance(
                info.get('priceToBook'), (int, float)) else None
            fundamentals['enterprise_value'] = info.get('enterpriseValue') if isinstance(
                info.get('enterpriseValue'), (int, float)) else None

            # Profitability metrics
            fundamentals['profit_margin'] = info.get('profitMargins') if isinstance(
                info.get('profitMargins'), (int, float)) else None
            fundamentals['operating_margin'] = info.get('operatingMargins') if isinstance(
                info.get('operatingMargins'), (int, float)) else None
            fundamentals['roa'] = info.get('returnOnAssets') if isinstance(
                info.get('returnOnAssets'), (int, float)) else None
            fundamentals['roe'] = info.get('returnOnEquity') if isinstance(
                info.get('returnOnEquity'), (int, float)) else None

            # Growth metrics (calculated from financial statements)
            fundamentals['revenue_growth'] = None
            fundamentals['earnings_growth'] = None

            # Financial health
            fundamentals['book_value'] = info.get('bookValue') if isinstance(
                info.get('bookValue'), (int, float)) else None
            fundamentals['market_cap'] = info.get('marketCap') if isinstance(
                info.get('marketCap'), (int, float)) else None
            fundamentals['dividend_yield'] = info.get('dividendYield') if isinstance(
                info.get('dividendYield'), (int, float)) else None
            fundamentals['debt_to_equity'] = info.get('debtToEquity') if isinstance(
                info.get('debtToEquity'), (int, float)) else None
            fundamentals['current_ratio'] = info.get('currentRatio') if isinstance(
                info.get('currentRatio'), (int, float)) else None

            # Add basic company info
            fundamentals['name'] = info.get(
                'shortName', info.get('longName', ticker))
            fundamentals['sector'] = info.get('sector', 'Unknown')
            fundamentals['industry'] = info.get('industry', 'Unknown')
            fundamentals['exchange'] = info.get('exchange', 'Unknown')
            fundamentals['currency'] = info.get('currency', 'Unknown')
            fundamentals['country'] = info.get('country', 'Unknown')

            # Calculate growth metrics if financial data is available
            if has_financials:
                # Calculate revenue growth
                if not income_stmt.empty and 'Total Revenue' in income_stmt.index:
                    revenues = income_stmt.loc['Total Revenue']
                    if len(revenues) >= 2:
                        latest_revenue = revenues.iloc[0]
                        previous_revenue = revenues.iloc[1]
                        if previous_revenue and previous_revenue > 0:
                            fundamentals['revenue_growth'] = (
                                latest_revenue - previous_revenue) / previous_revenue

                # Calculate earnings growth
                if not income_stmt.empty and 'Net Income' in income_stmt.index:
                    earnings = income_stmt.loc['Net Income']
                    if len(earnings) >= 2:
                        latest_earnings = earnings.iloc[0]
                        previous_earnings = earnings.iloc[1]
                        if previous_earnings and previous_earnings > 0:
                            fundamentals['earnings_growth'] = (
                                latest_earnings - previous_earnings) / previous_earnings

            # Cache the fundamentals
            cache_fundamentals(ticker, fundamentals)
            logger.info(f"Cached fundamentals for {ticker}")

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
                'name': ticker,
                'sector': 'Unknown',
                'industry': 'Unknown',
                'exchange': 'Unknown',
                'currency': 'Unknown',
                'country': 'Unknown'
            }

    def search_stock(self, query):
        """Search for a stock by name or ticker."""
        try:
            # Use yfinance for search
            # This is a workaround as yfinance doesn't have a direct search function
            # We'll try some common suffixes for the query
            suffixes = ['', '.ST', '.TO', '.L', '.F',
                        '.PA', '.AS', '.BR', '.MI', '.MC', '.HK']
            results = []

            for suffix in suffixes:
                try:
                    test_ticker = f"{query}{suffix}"
                    stock = yf.Ticker(test_ticker)
                    info = stock.info

                    # Check if we got valid data
                    if 'shortName' in info and info['shortName']:
                        results.append({
                            'symbol': test_ticker,
                            'shortname': info['shortName'],
                            'longname': info.get('longName', ''),
                            'exchDisp': info.get('exchange', 'Unknown'),
                            'typeDisp': 'Stock'
                        })

                        # Limit results to avoid too many API calls
                        if len(results) >= 5:
                            break

                except Exception:
                    continue

            return results

        except Exception as e:
            logger.error(f"Error searching for stock {query}: {e}")
            return []
