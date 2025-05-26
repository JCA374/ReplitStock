# ui/batch_analysis.py - UPDATED with clickable watchlist icons

# Standard library imports
import logging
import time
from datetime import datetime

# Third-party imports
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Local application imports
from analysis.fundamental import analyze_fundamentals
from analysis.technical import calculate_all_indicators, generate_technical_signals
from config import TIMEFRAMES, PERIOD_OPTIONS
from data.db_integration import (
    get_watchlist, get_all_cached_stocks, get_cached_stock_data,
    get_cached_fundamentals, add_to_watchlist
)
from data.stock_data import StockDataFetcher
from helpers import create_results_table
from utils.ticker_mapping import normalize_ticker
from ui.performance_overview import display_performance_metrics
from data.db_connection import get_db_session_context

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BatchAnalyzer:
    """Enhanced batch analyzer with database-first approach"""

    def __init__(self):
        self.data_fetcher = StockDataFetcher()

    def analyze_stock(self, ticker):
        """
        Analyze a single stock with database-first, then API fallback approach
        Priority: Database -> Alpha Vantage -> Yahoo Finance
        """
        try:
            ticker = normalize_ticker(ticker)
            logger.info(f"Starting analysis for {ticker}")

            # Step 1: Fetch stock data
            stock_data, fundamentals, data_source = self._fetch_stock_data(
                ticker)

            if stock_data is None or stock_data.empty:
                return {
                    "ticker": ticker,
                    "error": "No data available",
                    "error_message": f"Could not retrieve data for {ticker} from any source"
                }

            # Step 2: Get stock info and name
            name, stock_info = self._get_stock_info(ticker)

            # Step 3: Ensure we have fundamentals
            fundamentals = self._get_fundamentals(ticker, fundamentals)

            # Step 4: Calculate technical and fundamental indicators
            indicators, signals = self._calculate_technical_indicators(
                ticker, stock_data)
            fundamental_analysis = self._analyze_fundamentals(
                ticker, fundamentals)

            # Step 5: Get current price safely
            current_price = self._get_current_price(ticker, stock_data)

            # Step 6: Calculate tech score and signals
            tech_score, buy_signal, sell_signal, signal = self._calculate_signals(
                signals, fundamental_analysis)

            # Step 7: Create comprehensive result
            result = {
                "ticker": ticker,
                "name": name,
                "price": current_price,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "tech_score": tech_score,
                "signal": signal,
                "buy_signal": buy_signal,
                "sell_signal": sell_signal,
                "data_source": data_source,

                # Technical indicators (with safe gets)
                "above_ma40": signals.get('above_ma40', False),
                "above_ma4": signals.get('above_ma4', False),
                "rsi": signals.get('rsi_value', None),
                "rsi_above_50": signals.get('rsi_above_50', False),
                "higher_lows": signals.get('higher_lows', False),
                "near_52w_high": signals.get('near_52w_high', False),
                "breakout": signals.get('breakout_up', False),

                # Fundamental indicators (with safe gets)
                "pe_ratio": fundamentals.get('pe_ratio') if fundamentals else None,
                "profit_margin": fundamentals.get('profit_margin') if fundamentals else None,
                "revenue_growth": fundamentals.get('revenue_growth') if fundamentals else None,
                "is_profitable": fundamental_analysis['overall'].get('is_profitable', False),
                "fundamental_check": fundamental_analysis['overall'].get('value_momentum_pass', False),
                "earnings_trend": "Stable"  # Default value
            }

            logger.info(f"Successfully analyzed {ticker}")
            return result

        except Exception as e:
            logger.error(f"Error analyzing {ticker}: {e}")
            return {
                "ticker": ticker,
                "error": str(e),
                "error_message": f"Analysis failed for {ticker}: {str(e)}",
                "name": ticker,
                "price": 0,
                "tech_score": 0,
                "signal": "HÅLL",  # Default to hold on error
                "buy_signal": False,
                "sell_signal": False
            }

    def _fetch_stock_data(self, ticker):
        """Fetch stock data from database first, then APIs"""
        # Step 1: Try to get data from database first
        stock_data = get_cached_stock_data(ticker, '1d', '1y', 'yahoo')
        if stock_data is None:
            stock_data = get_cached_stock_data(
                ticker, '1d', '1y', 'alphavantage')

        fundamentals = get_cached_fundamentals(ticker)
        data_source = "database"

        # Step 2: If no cached data, try Alpha Vantage API
        if stock_data is None or stock_data.empty:
            try:
                logger.info(
                    f"No cached data for {ticker}, trying Alpha Vantage API")
                stock_data = self.data_fetcher.get_stock_data(
                    ticker, '1d', '1y', attempt_fallback=False)
                if not stock_data.empty:
                    data_source = "alphavantage"
                    logger.info(f"Got data from Alpha Vantage for {ticker}")
            except Exception as e:
                logger.warning(f"Alpha Vantage failed for {ticker}: {e}")
                stock_data = None

        # Step 3: If still no data, try Yahoo Finance as final fallback
        if stock_data is None or stock_data.empty:
            try:
                logger.info(f"Trying Yahoo Finance for {ticker}")
                stock_data = self.data_fetcher.get_stock_data(
                    ticker, '1d', '1y', attempt_fallback=True)
                if not stock_data.empty:
                    data_source = "yahoo"
                    logger.info(f"Got data from Yahoo Finance for {ticker}")
            except Exception as e:
                logger.error(f"All data sources failed for {ticker}: {e}")
                stock_data = None

        return stock_data, fundamentals, data_source

    def _get_stock_info(self, ticker):
        """Get stock information"""
        try:
            stock_info = self.data_fetcher.get_stock_info(ticker)
            name = stock_info.get('name', ticker)
            return name, stock_info
        except Exception as e:
            logger.warning(f"Could not get stock info for {ticker}: {e}")
            return ticker, {'name': ticker}

    def _get_fundamentals(self, ticker, existing_fundamentals):
        """Get fundamentals data if not already available"""
        if not existing_fundamentals:
            try:
                return self.data_fetcher.get_fundamentals(ticker)
            except Exception as e:
                logger.warning(f"Could not get fundamentals for {ticker}: {e}")
                return {}
        return existing_fundamentals

    def _calculate_technical_indicators(self, ticker, stock_data):
        """Calculate technical indicators with error handling"""
        try:
            indicators = calculate_all_indicators(stock_data)
            if not indicators:
                logger.warning(
                    f"Could not calculate technical indicators for {ticker}")
                indicators = {}

            # Generate technical signals
            signals = generate_technical_signals(indicators)
            if not signals:
                logger.warning(f"Could not generate signals for {ticker}")
                signals = {}

            return indicators, signals
        except Exception as e:
            logger.warning(f"Error calculating indicators for {ticker}: {e}")
            return {}, {
                'tech_score': 50,
                'overall_signal': 'HOLD',
                'error': str(e)
            }

    def _analyze_fundamentals(self, ticker, fundamentals):
        """Analyze fundamentals with error handling"""
        try:
            return analyze_fundamentals(fundamentals or {})
        except Exception as e:
            logger.warning(f"Error analyzing fundamentals for {ticker}: {e}")
            return {'overall': {'value_momentum_pass': False, 'is_profitable': False}}
