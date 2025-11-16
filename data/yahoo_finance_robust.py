"""
Robust Yahoo Finance Data Fetcher

Multiple fallback methods with retry logic and comprehensive error handling.
Designed for Swedish stocks (.ST suffix).
"""

import logging
import time
import json
import urllib.request
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class RobustYahooFetcher:
    """
    Robust Yahoo Finance data fetcher with multiple fallback methods.

    Methods (in order):
    1. yfinance (primary - convenient API)
    2. urllib (fallback - no dependencies, very reliable)
    3. requests (fallback - if available)
    """

    def __init__(self, max_retries: int = 3, retry_delay: float = 2.0):
        """
        Initialize robust fetcher

        Args:
            max_retries: Maximum number of retry attempts per method
            retry_delay: Delay between retries in seconds
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Try to import optional libraries
        self.yfinance = self._try_import_yfinance()
        self.requests = self._try_import_requests()

    def _try_import_yfinance(self):
        """Try to import yfinance"""
        try:
            import yfinance as yf
            logger.info(f"yfinance available (version {yf.__version__})")
            return yf
        except ImportError:
            logger.warning("yfinance not available")
            return None

    def _try_import_requests(self):
        """Try to import requests"""
        try:
            import requests
            logger.info(f"requests library available")
            return requests
        except ImportError:
            logger.warning("requests not available")
            return None

    def get_historical_data(
        self,
        ticker: str,
        period: str = '1y',
        interval: str = '1d'
    ) -> Optional[pd.DataFrame]:
        """
        Get historical price data for a stock using multiple fallback methods

        Args:
            ticker: Stock ticker (e.g., 'VOLV-B.ST')
            period: Time period ('1mo', '3mo', '6mo', '1y', '2y', etc.)
            interval: Data interval ('1d', '1wk', '1mo')

        Returns:
            DataFrame with OHLCV data, or None if all methods fail
        """
        logger.info(f"Fetching {ticker} data (period={period}, interval={interval})")

        # Method 1: Try yfinance (most convenient)
        if self.yfinance:
            data = self._fetch_with_yfinance(ticker, period, interval)
            if data is not None:
                return data

        # Method 2: Try urllib (most reliable, no deps)
        data = self._fetch_with_urllib(ticker, period, interval)
        if data is not None:
            return data

        # Method 3: Try requests (if available)
        if self.requests:
            data = self._fetch_with_requests(ticker, period, interval)
            if data is not None:
                return data

        # All methods failed
        logger.error(f"All fetching methods failed for {ticker}")
        return None

    def _fetch_with_yfinance(
        self,
        ticker: str,
        period: str,
        interval: str
    ) -> Optional[pd.DataFrame]:
        """Fetch data using yfinance library"""

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Attempting yfinance fetch (attempt {attempt}/{self.max_retries})")

                stock = self.yfinance.Ticker(ticker)
                hist = stock.history(period=period, interval=interval)

                if not hist.empty:
                    # Normalize column names to lowercase
                    hist.columns = [col.lower() for col in hist.columns]

                    logger.info(f"✓ yfinance success: {len(hist)} rows")
                    return hist
                else:
                    logger.warning(f"yfinance returned empty data")

            except Exception as e:
                logger.warning(f"yfinance attempt {attempt} failed: {e}")

                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)

        return None

    def _fetch_with_urllib(
        self,
        ticker: str,
        period: str,
        interval: str
    ) -> Optional[pd.DataFrame]:
        """Fetch data using urllib (built-in, very reliable)"""

        # Convert period to range parameter
        range_param = self._period_to_range(period)

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Attempting urllib fetch (attempt {attempt}/{self.max_retries})")

                # Yahoo Finance query API
                url = f'https://query2.finance.yahoo.com/v8/finance/chart/{ticker}'
                url += f'?interval={interval}&range={range_param}'

                req = urllib.request.Request(
                    url,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                )

                with urllib.request.urlopen(req, timeout=15) as response:
                    data = json.loads(response.read().decode('utf-8'))

                # Parse response
                df = self._parse_yahoo_json(data)

                if df is not None and not df.empty:
                    logger.info(f"✓ urllib success: {len(df)} rows")
                    return df
                else:
                    logger.warning(f"urllib returned empty data")

            except Exception as e:
                logger.warning(f"urllib attempt {attempt} failed: {e}")

                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)

        return None

    def _fetch_with_requests(
        self,
        ticker: str,
        period: str,
        interval: str
    ) -> Optional[pd.DataFrame]:
        """Fetch data using requests library"""

        range_param = self._period_to_range(period)

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Attempting requests fetch (attempt {attempt}/{self.max_retries})")

                url = f'https://query2.finance.yahoo.com/v8/finance/chart/{ticker}'
                url += f'?interval={interval}&range={range_param}'

                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }

                response = self.requests.get(url, headers=headers, timeout=15)
                response.raise_for_status()

                data = response.json()

                # Parse response
                df = self._parse_yahoo_json(data)

                if df is not None and not df.empty:
                    logger.info(f"✓ requests success: {len(df)} rows")
                    return df
                else:
                    logger.warning(f"requests returned empty data")

            except Exception as e:
                logger.warning(f"requests attempt {attempt} failed: {e}")

                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)

        return None

    def _parse_yahoo_json(self, data: Dict) -> Optional[pd.DataFrame]:
        """Parse Yahoo Finance JSON response into DataFrame"""

        try:
            if 'chart' not in data or 'result' not in data['chart']:
                return None

            result = data['chart']['result'][0]

            # Extract timestamps
            timestamps = result.get('timestamp', [])
            if not timestamps:
                return None

            # Convert to datetime
            dates = [datetime.fromtimestamp(ts) for ts in timestamps]

            # Extract OHLCV data
            quotes = result.get('indicators', {}).get('quote', [{}])[0]

            df = pd.DataFrame({
                'open': quotes.get('open', []),
                'high': quotes.get('high', []),
                'low': quotes.get('low', []),
                'close': quotes.get('close', []),
                'volume': quotes.get('volume', [])
            }, index=dates)

            # Add dividends and splits if available
            adjclose = result.get('indicators', {}).get('adjclose', [{}])[0]
            if adjclose:
                df['Dividends'] = 0  # Placeholder
                df['Stock Splits'] = 0  # Placeholder

            return df

        except Exception as e:
            logger.error(f"Error parsing Yahoo JSON: {e}")
            return None

    def _period_to_range(self, period: str) -> str:
        """Convert yfinance period to Yahoo Finance range parameter"""

        period_map = {
            '1d': '1d',
            '5d': '5d',
            '1mo': '1mo',
            '3mo': '3mo',
            '6mo': '6mo',
            '1y': '1y',
            '2y': '2y',
            '5y': '5y',
            '10y': '10y',
            'ytd': 'ytd',
            'max': 'max'
        }

        return period_map.get(period, '1y')

    def get_fundamentals(self, ticker: str) -> Optional[Dict]:
        """
        Get fundamental data for a stock

        Args:
            ticker: Stock ticker (e.g., 'VOLV-B.ST')

        Returns:
            Dict with fundamental data, or None if failed
        """

        # Method 1: Try yfinance
        if self.yfinance:
            data = self._fetch_fundamentals_yfinance(ticker)
            if data:
                return data

        # Method 2: Try urllib
        data = self._fetch_fundamentals_urllib(ticker)
        if data:
            return data

        logger.error(f"All methods failed for fundamentals: {ticker}")
        return None

    def _fetch_fundamentals_yfinance(self, ticker: str) -> Optional[Dict]:
        """Fetch fundamentals using yfinance"""

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Fetching fundamentals with yfinance (attempt {attempt})")

                stock = self.yfinance.Ticker(ticker)
                info = stock.info

                if info and len(info) > 5:
                    logger.info(f"✓ Got {len(info)} fundamental fields")
                    return info

            except Exception as e:
                logger.warning(f"yfinance fundamentals attempt {attempt} failed: {e}")

                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)

        return None

    def _fetch_fundamentals_urllib(self, ticker: str) -> Optional[Dict]:
        """Fetch fundamentals using urllib"""

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Fetching fundamentals with urllib (attempt {attempt})")

                url = f'https://query2.finance.yahoo.com/v10/finance/quoteSummary/{ticker}'
                url += '?modules=summaryDetail,financialData,defaultKeyStatistics'

                req = urllib.request.Request(
                    url,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                )

                with urllib.request.urlopen(req, timeout=15) as response:
                    data = json.loads(response.read().decode('utf-8'))

                if 'quoteSummary' in data and 'result' in data['quoteSummary']:
                    result = data['quoteSummary']['result'][0]

                    # Flatten the nested structure
                    fundamentals = {}
                    for module in result.values():
                        if isinstance(module, dict):
                            for key, value in module.items():
                                if isinstance(value, dict) and 'raw' in value:
                                    fundamentals[key] = value['raw']
                                else:
                                    fundamentals[key] = value

                    logger.info(f"✓ Got {len(fundamentals)} fundamental fields")
                    return fundamentals

            except Exception as e:
                logger.warning(f"urllib fundamentals attempt {attempt} failed: {e}")

                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)

        return None


# Convenience function
def get_stock_data(ticker: str, period: str = '1y', interval: str = '1d') -> Optional[pd.DataFrame]:
    """
    Simple function to get stock data using robust fetcher

    Args:
        ticker: Stock ticker (e.g., 'VOLV-B.ST')
        period: Time period ('1mo', '3mo', '6mo', '1y', etc.)
        interval: Data interval ('1d', '1wk', '1mo')

    Returns:
        DataFrame with OHLCV data, or None if failed
    """
    fetcher = RobustYahooFetcher()
    return fetcher.get_historical_data(ticker, period, interval)
