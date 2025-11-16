"""
Demo/Sample Data Provider
Provides sample stock data when all API sources fail.
This ensures the app remains functional even without API keys or cached data.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class DemoDataProvider:
    """Provides demo/sample stock data as a last-resort fallback"""

    # Sample Swedish stocks for demo
    DEMO_STOCKS = {
        'VOLV-B.ST': {
            'name': 'Volvo Group',
            'sector': 'Industrials',
            'industry': 'Auto Manufacturers',
            'pe_ratio': 8.5,
            'profit_margin': 0.095,
            'revenue_growth': 0.08,
            'market_cap': 250000000000
        },
        'ERIC-B.ST': {
            'name': 'Ericsson',
            'sector': 'Technology',
            'industry': 'Telecom Equipment',
            'pe_ratio': 15.2,
            'profit_margin': 0.05,
            'revenue_growth': 0.03,
            'market_cap': 220000000000
        },
        'HM-B.ST': {
            'name': 'H&M',
            'sector': 'Consumer Cyclical',
            'industry': 'Apparel Retail',
            'pe_ratio': 18.5,
            'profit_margin': 0.04,
            'revenue_growth': 0.02,
            'market_cap': 180000000000
        },
        'SEB-A.ST': {
            'name': 'SEB Bank',
            'sector': 'Financial Services',
            'industry': 'Banks',
            'pe_ratio': 9.8,
            'profit_margin': 0.42,
            'revenue_growth': 0.06,
            'market_cap': 170000000000
        },
        'SAND.ST': {
            'name': 'Sandvik',
            'sector': 'Industrials',
            'industry': 'Tools & Accessories',
            'pe_ratio': 16.3,
            'profit_margin': 0.12,
            'revenue_growth': 0.07,
            'market_cap': 160000000000
        }
    }

    @staticmethod
    def generate_demo_price_data(ticker, period='1y', timeframe='1d'):
        """
        Generate realistic-looking demo price data

        Args:
            ticker: Stock ticker symbol
            period: Time period (1mo, 3mo, 6mo, 1y, etc.)
            timeframe: Data interval (1d, 1wk, 1mo)

        Returns:
            pandas.DataFrame with OHLCV data
        """
        try:
            # Map period to number of days
            period_days = {
                '1mo': 30,
                '3mo': 90,
                '6mo': 180,
                'ytd': (datetime.now() - datetime(datetime.now().year, 1, 1)).days,
                '1y': 365,
                '2y': 730,
                '5y': 1825,
                'max': 3650
            }

            days = period_days.get(period, 365)

            # Map timeframe to interval
            interval_days = {
                '1d': 1,
                '1wk': 7,
                '1mo': 30
            }

            interval = interval_days.get(timeframe, 1)
            num_points = days // interval

            # Generate dates
            end_date = datetime.now()
            dates = [end_date - timedelta(days=i * interval) for i in range(num_points)]
            dates.reverse()

            # Generate realistic price movement (random walk with drift)
            base_price = 100.0  # Starting price
            drift = 0.0002  # Small upward drift per day
            volatility = 0.02  # Daily volatility

            # Generate returns
            returns = np.random.normal(drift, volatility, num_points)
            cumulative_returns = np.exp(np.cumsum(returns))

            # Generate prices
            close_prices = base_price * cumulative_returns

            # Generate OHLC data with realistic intraday movements
            opens = close_prices + np.random.normal(0, 0.5, num_points)
            highs = np.maximum(opens, close_prices) + np.abs(np.random.normal(0, 0.5, num_points))
            lows = np.minimum(opens, close_prices) - np.abs(np.random.normal(0, 0.5, num_points))

            # Generate volume (random with some trend)
            avg_volume = 1000000
            volumes = np.random.lognormal(np.log(avg_volume), 0.5, num_points)

            # Create DataFrame
            df = pd.DataFrame({
                'open': opens,
                'high': highs,
                'low': lows,
                'close': close_prices,
                'volume': volumes.astype(int)
            }, index=dates)

            df.index.name = 'Date'

            logger.info(f"Generated demo price data for {ticker}: {len(df)} points")
            return df

        except Exception as e:
            logger.error(f"Error generating demo data for {ticker}: {e}")
            return pd.DataFrame()

    @staticmethod
    def get_demo_fundamentals(ticker):
        """
        Get demo fundamental data for a ticker

        Args:
            ticker: Stock ticker symbol

        Returns:
            dict with fundamental metrics
        """
        # Check if we have predefined demo data for this ticker
        if ticker in DemoDataProvider.DEMO_STOCKS:
            data = DemoDataProvider.DEMO_STOCKS[ticker].copy()
            logger.info(f"Returned predefined demo fundamentals for {ticker}")
            return data

        # Generate generic demo fundamentals for unknown tickers
        fundamentals = {
            'name': ticker.replace('.ST', ''),
            'sector': 'Unknown',
            'industry': 'Unknown',
            'exchange': 'Stockholm',
            'currency': 'SEK',
            'country': 'Sweden',
            'pe_ratio': np.random.uniform(8, 25),
            'profit_margin': np.random.uniform(0.03, 0.15),
            'revenue_growth': np.random.uniform(-0.05, 0.15),
            'earnings_growth': np.random.uniform(-0.05, 0.20),
            'book_value': np.random.uniform(50, 150),
            'market_cap': np.random.uniform(1e9, 5e11),
            'dividend_yield': np.random.uniform(0.01, 0.05),
            'debt_to_equity': np.random.uniform(0.2, 1.5),
            'current_ratio': np.random.uniform(1.0, 2.5),
            'roa': np.random.uniform(0.02, 0.12),
            'roe': np.random.uniform(0.08, 0.25)
        }

        logger.info(f"Generated generic demo fundamentals for {ticker}")
        return fundamentals

    @staticmethod
    def get_demo_stock_info(ticker):
        """
        Get basic demo stock information

        Args:
            ticker: Stock ticker symbol

        Returns:
            dict with basic stock info
        """
        if ticker in DemoDataProvider.DEMO_STOCKS:
            data = DemoDataProvider.DEMO_STOCKS[ticker]
            return {
                'name': data['name'],
                'sector': data['sector'],
                'industry': data['industry'],
                'exchange': 'Stockholm',
                'currency': 'SEK',
                'country': 'Sweden'
            }

        return {
            'name': ticker.replace('.ST', ''),
            'sector': 'Unknown',
            'industry': 'Unknown',
            'exchange': 'Stockholm',
            'currency': 'SEK',
            'country': 'Sweden'
        }

    @staticmethod
    def is_demo_mode_enabled():
        """Check if demo mode should be enabled (when no API keys available)"""
        import os

        # Demo mode is a fallback - it's always available but has lowest priority
        return True

    @staticmethod
    def get_available_demo_tickers():
        """Get list of tickers that have predefined demo data"""
        return list(DemoDataProvider.DEMO_STOCKS.keys())


# Singleton instance for easy access
_demo_provider = None

def get_demo_provider():
    """Get the singleton demo data provider instance"""
    global _demo_provider
    if _demo_provider is None:
        _demo_provider = DemoDataProvider()
    return _demo_provider
