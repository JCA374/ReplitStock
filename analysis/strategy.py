# Standard library imports
import json
import logging
import os
import time
from datetime import datetime, timedelta

# Third-party imports
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

# Local application imports
from data.db_integration import (
    get_cached_stock_data, get_cached_fundamentals,
    cache_stock_data, cache_fundamentals,
    store_analysis_result
)
from data.stock_data import StockDataFetcher

# Set up logging
logging.basicConfig(level=logging.INFO)


class ValueMomentumStrategy:
    def __init__(self):
        """Initialize the Value Momentum Strategy with database-first approach"""
        # Configuration parameters
        self.today = datetime.now()
        self.start_date = self.today - timedelta(days=365*3)  # 3 years of data

        # Strategy parameters
        self.ma_short = 4   # 4-week MA (approx. 1 month)
        self.ma_long = 40   # 40-week MA (approx. 200 days)
        self.rsi_period = 14
        self.rsi_threshold = 50  # RSI above this is bullish
        self.near_high_threshold = 0.98  # Within 2% of 52-week high
        self.pe_max = 30    # Maximum P/E ratio considered reasonable

        # Initialize data fetcher
        self.data_fetcher = StockDataFetcher()

        # Set up logging
        self.logger = logging.getLogger('ValueMomentumStrategy')

    def calculate_rsi(self, prices, window=14):
        """Calculate Relative Strength Index without using pandas_ta"""
        # Handle edge case with insufficient data
        if len(prices) <= window:
            return np.array([np.nan] * len(prices))

        # Calculate price changes
        deltas = np.diff(prices)
        seed = deltas[:window+1]

        # Initial values
        up = seed[seed >= 0].sum() / window
        down = -seed[seed < 0].sum() / window

        # Avoid division by zero
        if down == 0:
            return np.ones_like(prices) * 100

        rs = up / down
        rsi = np.zeros_like(prices)
        rsi[:window+1] = 100. - (100. / (1. + rs))

        # Calculate RSI for the rest of the price data
        for i in range(window+1, len(prices)):
            delta = deltas[i-1]  # Adjust index

            if delta > 0:
                upval = delta
                downval = 0
            else:
                upval = 0
                downval = -delta

            # Use EMA for calculating averages
            up = (up * (window - 1) + upval) / window
            down = (down * (window - 1) + downval) / window

            rs = up / down if down != 0 else 999  # Avoid division by zero
            rsi[i] = 100. - (100. / (1. + rs))

        return rsi

    def _calculate_higher_lows(self, data, lookback=10):
        """Helper function to identify higher lows"""
        if 'low' not in data.columns or data.empty:
            return pd.Series(np.zeros(len(data)))

        highs_lows = pd.DataFrame()
        highs_lows['min'] = data['low'].rolling(
            window=lookback, center=True).min()

        # Simple heuristic to identify higher lows
        higher_lows = np.zeros(len(data))

        for i in range(lookback*2, len(data)):
            min_values = highs_lows['min'].iloc[i-lookback:i].dropna()
            if len(min_values) >= 2:  # Ensure we have enough data
                diffs = min_values.diff().dropna()
                if len(diffs) > 0 and (diffs > 0).all():
                    higher_lows[i] = 1

        return pd.Series(higher_lows, index=data.index)

    def analyze_stock(self, ticker):
        """
        Analyze a single stock with database-first approach
        Priority: Database Cache -> Alpha Vantage -> Yahoo Finance
        """
        result = {"ticker": ticker, "error": None, "error_message": None}

        try:
            self.logger.info(f"Starting analysis for {ticker}")

            # Step 1: Fetch stock data and fundamentals
            stock_data, fundamentals, data_source = self._fetch_stock_data(ticker)
            
            if stock_data is None or stock_data.empty:
                return {
                    "ticker": ticker,
                    "error": "No data available",
                    "error_message": f"Could not retrieve data for {ticker} from any source"
                }

            # Step 2: Get stock info
            name, stock_info = self._get_stock_info(ticker, fundamentals)

            # Step 3: Calculate price
            price = stock_data['close'].iloc[-1] if not stock_data.empty else 0

            # Step 4: Calculate technical and fundamental indicators
            tech_analysis = self._calculate_technical_indicators(stock_data)
            fund_analysis = self._calculate_fundamental_indicators(fundamentals, stock_info)

            # Step 5: Calculate signals and scores
            tech_score = self.calculate_tech_score(tech_analysis)
            fund_check = fund_analysis['fundamental_check']
            buy_signal = tech_score >= 70 and fund_check
            sell_signal = tech_score < 40 or not tech_analysis['above_ma40']

            # Step 6: Process historical data to add indicators
            processed_hist = self._process_historical_data(stock_data)

            # Step 7: Create results dictionary
            result = {
                "ticker": ticker,
                "name": name,
                "price": price,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "tech_score": tech_score,
                "signal": "KÖP" if buy_signal else "SÄLJ" if sell_signal else "HÅLL",
                "buy_signal": buy_signal,
                "sell_signal": sell_signal,
                "fundamental_check": fund_check,
                "technical_check": tech_score >= 60,
                "historical_data": processed_hist,
                "rsi": tech_analysis.get('rsi', None),
                "data_source": data_source
            }

            # Combine technical and fundamental indicators into result
            result.update(tech_analysis)
            result.update(fund_analysis)

            self.logger.info(f"Successfully analyzed {ticker}")
            return result

        except Exception as e:
            err = str(e)
            self.logger.error(f"Error analyzing {ticker}: {err}")
            return {
                "ticker": ticker,
                "error": err,
                "error_message": f"Fel vid analys: {err}"
            }
            
    def _fetch_stock_data(self, ticker):
        """Fetch stock data and fundamentals with fallback mechanisms"""
        # Try to get data from database cache first
        stock_data = get_cached_stock_data(ticker, '1d', '1y', 'alphavantage')
        if stock_data is None or stock_data.empty:
            stock_data = get_cached_stock_data(ticker, '1d', '1y', 'yahoo')

        fundamentals = get_cached_fundamentals(ticker)
        data_source = "database"

        # If no cached data, fetch from APIs
        if stock_data is None or stock_data.empty:
            self.logger.info(f"No cached data for {ticker}, fetching from APIs")
            # Try Alpha Vantage first, then Yahoo Finance
            stock_data = self.data_fetcher.get_stock_data(
                ticker, '1d', '1y', attempt_fallback=True)
            data_source = "api"

        return stock_data, fundamentals, data_source
        
    def _get_stock_info(self, ticker, fundamentals):
        """Get stock information and handle exceptions"""
        try:
            if not fundamentals:
                fundamentals = self.data_fetcher.get_fundamentals(ticker)

            stock_info = self.data_fetcher.get_stock_info(ticker)
            name = stock_info.get('name', ticker)
            return name, stock_info
        except Exception as e:
            self.logger.warning(f"Could not get stock info for {ticker}: {e}")
            return ticker, {'name': ticker}
            
    def _process_historical_data(self, stock_data):
        """Process historical data to add technical indicators"""
        # Make a copy to avoid modifying original data
        processed_hist = stock_data.copy()
        
        # Add moving averages
        processed_hist['MA4'] = processed_hist['close'].rolling(
            window=20).mean()  # 20 trading days ≈ 4 weeks
        processed_hist['MA40'] = processed_hist['close'].rolling(
            window=200).mean()  # 200 trading days ≈ 40 weeks
            
        # Add RSI
        processed_hist['RSI'] = self.calculate_rsi(
            processed_hist['close'].values, window=self.rsi_period)
            
        return processed_hist

    def _calculate_technical_indicators(self, hist):
        """Calculate technical indicators from historical price data"""
        # Make a copy of the dataframe to avoid warnings
        data = hist.copy()

        # Check for empty dataframes
        if data.empty:
            return {
                "above_ma40": False,
                "above_ma4": False,
                "rsi_above_50": False,
                "higher_lows": False,
                "near_52w_high": False,
                "breakout": False
            }

        # Ensure we have enough data
        if len(hist) < max(self.ma_long, 52):  # Need at least 40 weeks (or as specified for MA40)
            return {
                "above_ma40": False,
                "above_ma4": False,
                "rsi_above_50": False,
                "higher_lows": False,
                "near_52w_high": False,
                "breakout": False
            }

        # Calculate moving averages
        data['MA4'] = data['close'].rolling(
            window=20).mean()  # 20 trading days ≈ 4 weeks
        data['MA40'] = data['close'].rolling(
            window=200).mean()  # 200 trading days ≈ 40 weeks

        # Calculate RSI with our improved function
        data['RSI'] = self.calculate_rsi(
            data['close'].values, window=self.rsi_period)

        # Calculate higher lows (using new function)
        data['higher_lows'] = self._calculate_higher_lows(data)

        # 52-week highest level
        data['52w_high'] = data['high'].rolling(
            window=252).max()  # 252 trading days ≈ 52 weeks
        # Within 2% of highest level
        data['at_52w_high'] = (
            data['close'] >= data['52w_high'] * self.near_high_threshold)

        # Consolidation phase breakout (simple implementation)
        data['volatility'] = data['close'].pct_change().rolling(window=12).std()
        data['breakout'] = (data['volatility'].shift(4) < data['volatility']) & (
            data['close'] > data['close'].shift(4))

        # Get the latest data point
        latest = data.iloc[-1]

        # Return technical indicators as a dictionary
        return {
            "above_ma40": latest['close'] > latest['MA40'] if not np.isnan(latest['MA40']) else False,
            "above_ma4": latest['close'] > latest['MA4'] if not np.isnan(latest['MA4']) else False,
            "rsi_above_50": latest['RSI'] > self.rsi_threshold if not np.isnan(latest['RSI']) else False,
            # Add actual RSI value
            "rsi": float(latest['RSI']) if not np.isnan(latest['RSI']) else None,
            "higher_lows": bool(latest['higher_lows']),
            "near_52w_high": bool(latest['at_52w_high']),
            "breakout": bool(latest['breakout'])
        }

    def _calculate_fundamental_indicators(self, fundamentals, stock_info):
        """Enhanced fundamental analysis with additional metrics"""
        # Initialize results dictionary with default values
        results = {
            "pe_ratio": None,
            "profit_margin": None, 
            "revenue_growth": None,
            "is_profitable": False,
            "reasonable_pe": True,
            "fundamental_check": False,
            "earnings_trend": "Unknown",
            # NEW METRICS
            "debt_to_equity": None,
            "return_on_equity": None,
            "price_to_book": None,
            "fundamental_score": 0
        }

        try:
            # Check if company is profitable
            profit_margin = fundamentals.get('profit_margin') if fundamentals else None
            results["is_profitable"] = profit_margin is not None and profit_margin > 0

            # Get P/E ratio
            pe_ratio = fundamentals.get('pe_ratio') if fundamentals else None
            results["pe_ratio"] = pe_ratio

            # Get revenue growth
            revenue_growth = fundamentals.get('revenue_growth') if fundamentals else None
            if revenue_growth is not None and pd.notna(revenue_growth):
                results["revenue_growth"] = revenue_growth

            # Get profit margin
            if profit_margin is not None and pd.notna(profit_margin):
                results["profit_margin"] = profit_margin

            # NEW: Add debt analysis
            debt_to_equity = fundamentals.get('debt_to_equity') if fundamentals else None
            if debt_to_equity is not None:
                results["debt_to_equity"] = debt_to_equity
                # Healthy debt levels (< 1.5)
                if debt_to_equity < 1.5:
                    results["fundamental_score"] += 20
            
            # NEW: Add ROE analysis
            roe = fundamentals.get('return_on_equity') if fundamentals else None
            if roe is not None:
                results["return_on_equity"] = roe
                # Good ROE (> 15%)
                if roe > 0.15:
                    results["fundamental_score"] += 20
            
            # NEW: Add P/B analysis
            pb_ratio = fundamentals.get('price_to_book') if fundamentals else None
            if pb_ratio is not None:
                results["price_to_book"] = pb_ratio
                # Value play (P/B < 3)
                if pb_ratio < 3 and pb_ratio > 0:
                    results["fundamental_score"] += 10

            # Get earnings trend data
            try:
                results["earnings_trend"] = "Stable"  # Default value
            except Exception as e:
                self.logger.warning(f"Error fetching earnings data: {e}")
                results["earnings_trend"] = "Data saknas"

            # Determine if the fundamentals pass the criteria
            profitable = results["is_profitable"]

            # Does it have a reasonable P/E ratio?
            reasonable_pe = pe_ratio is None or (pe_ratio is not None and pe_ratio <= self.pe_max and pe_ratio > 0)
            results["reasonable_pe"] = reasonable_pe

            # Check growth rates if available
            has_growth = results["revenue_growth"] is not None and results["revenue_growth"] > 0

            # Enhanced fundamental scoring
            if results["is_profitable"]:
                results["fundamental_score"] += 30
            if results["reasonable_pe"]:
                results["fundamental_score"] += 20
            if has_growth:
                results["fundamental_score"] += 10

            # Pass the fundamental check if profitable and reasonable P/E
            results["fundamental_check"] = profitable and reasonable_pe

            return results

        except Exception as e:
            self.logger.error(f"Error calculating fundamental indicators: {e}")
            return results

    def calculate_tech_score(self, tech_analysis):
        """Calculate a technical score from 0-100 based on technical indicators"""
        # Define the weight of each technical factor
        weights = {
            'above_ma40': 0.25,     # Primary trend
            'above_ma4': 0.15,      # Short-term momentum
            'rsi_above_50': 0.15,   # RSI momentum
            'higher_lows': 0.15,    # Price structure
            'near_52w_high': 0.20,  # Relative strength
            'breakout': 0.10        # Volatility expansion
        }

        # Calculate weighted score
        score = 0
        total_weight = 0

        for factor, weight in weights.items():
            if factor in tech_analysis:
                value = tech_analysis[factor]
                if value is not None:  # Only consider valid values
                    score += weight * (100 if value else 0)
                    total_weight += weight

        # Normalize score if we have valid factors
        if total_weight > 0:
            score = score / total_weight
        else:
            score = 0

        return round(score)

    def batch_analyze(self, tickers, progress_callback=None):
        """
        Analyze multiple stocks and return a list of analysis results.
        Also stores results in the database.
        """
        results = []

        for i, ticker in enumerate(tickers):
            # Update progress
            if progress_callback:
                progress = (i / len(tickers))
                progress_callback(progress, f"Analyzing {ticker}...")

            # Analyze stock
            result = self.analyze_stock(ticker)
            results.append(result)

            # Save to database if analysis was successful
            if "error" not in result or result["error"] is None:
                try:
                    store_analysis_result(ticker, result)
                except Exception as e:
                    self.logger.warning(
                        f"Could not store analysis result for {ticker}: {e}")

            # Small delay to prevent rate limiting
            time.sleep(0.1)

        # Sort by tech score (descending)
        results.sort(key=lambda x: x.get('tech_score', 0)
                     if x.get('error') is None else -1, reverse=True)

        # Final update
        if progress_callback:
            progress_callback(1.0, "Analysis complete!")

        return results

    def plot_analysis(self, analysis):
        """
        Create a plot visualizing the analysis results.
        
        Parameters:
        - analysis: Analysis result dictionary
        
        Returns:
        - Matplotlib figure
        """
        # Check if we have valid historical data
        if "historical_data" not in analysis or analysis["historical_data"] is None or analysis["historical_data"].empty:
            return None

        # Get historical data
        data = analysis["historical_data"]

        # Create figure and subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), height_ratios=[
            3, 1], sharex=True, gridspec_kw={'hspace': 0.05})

        # Plot main price chart with moving averages
        ax1.plot(data.index, data['close'],
                 label='Price', color='black', linewidth=1.5)

        if 'MA4' in data.columns and not data['MA4'].isna().all():
            ax1.plot(
                data.index, data['MA4'], label=f'MA4 (Short)', color='blue', linewidth=1)

        if 'MA40' in data.columns and not data['MA40'].isna().all():
            ax1.plot(
                data.index, data['MA40'], label=f'MA40 (Primary)', color='red', linewidth=1)

        # Add key technical markers
        last_date = data.index[-1]
        last_price = data['close'].iloc[-1]

        # Add buy/sell annotation
        signal_color = 'green' if analysis['buy_signal'] else 'red' if analysis['sell_signal'] else 'orange'
        signal_text = "KÖP" if analysis['buy_signal'] else "SÄLJ" if analysis['sell_signal'] else "HÅLL"

        ax1.annotate(signal_text,
                     xy=(last_date, last_price),
                     xytext=(10, 10),
                     textcoords='offset points',
                     color=signal_color,
                     weight='bold',
                     fontsize=12,
                     bbox=dict(boxstyle="round,pad=0.3", fc=signal_color, alpha=0.2))

        # Set title and labels
        ax1.set_title(
            f"{analysis['name']} ({analysis['ticker']}) - Tech Score: {analysis['tech_score']}/100", fontsize=14)
        ax1.set_ylabel('Price', fontsize=12)
        ax1.legend(loc='upper left')
        ax1.grid(True, alpha=0.3)

        # Plot RSI
        if 'RSI' in data.columns and not data['RSI'].isna().all():
            ax2.plot(data.index, data['RSI'],
                     label='RSI', color='purple', linewidth=1)
            ax2.axhline(y=70, color='red', linestyle='--', alpha=0.5)
            ax2.axhline(y=50, color='black', linestyle='--', alpha=0.5)
            ax2.axhline(y=30, color='green', linestyle='--', alpha=0.5)
            ax2.set_ylim(0, 100)
            ax2.set_ylabel('RSI', fontsize=12)
            ax2.grid(True, alpha=0.3)

        # Format dates on x-axis
        fig.autofmt_xdate()

        # Adjust layout
        plt.tight_layout()

        return fig
