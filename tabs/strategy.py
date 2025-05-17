import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
import time
import json
import os
from datetime import datetime, timedelta
import logging

# Import the Stock Data Manager
from services.stock_data_manager import StockDataManager


class ValueMomentumStrategy:
    def __init__(self):
        """Initialize the Value Momentum Strategy"""
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

        # Initialize data manager when needed
        self.data_manager = None

        # Set up logging
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger('ValueMomentumStrategy')

    def _ensure_data_manager(self):
        """Ensure the data manager is initialized"""
        if self.data_manager is None:
            # Access the database storage from session state
            db_storage = st.session_state.get('db_storage')
            if db_storage is None:
                raise RuntimeError(
                    "Database storage not initialized in session state")
            self.data_manager = StockDataManager(db_storage)
        return self.data_manager

    def _fetch_info(self, ticker):
        """Fetches ticker info using the data manager"""
        data_manager = self._ensure_data_manager()
        return data_manager.fetch_ticker_info(ticker)

    def _fetch_history(self, stock, period="1y", interval="1wk"):
        """Fetches history using the data manager"""
        data_manager = self._ensure_data_manager()
        return data_manager.fetch_history(stock, period=period, interval=interval)
    
    # Improved RSI calculation from the new code
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
        if 'Low' not in data.columns or data.empty:
            return pd.Series(np.zeros(len(data)))

        highs_lows = pd.DataFrame()
        highs_lows['min'] = data['Low'].rolling(
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
        Analyze a single stock according to Value & Momentum strategy.
        
        Parameters:
        - ticker: Stock ticker symbol
        
        Returns:
        - Dictionary with analysis results
        """
        result = {"ticker": ticker, "error": None, "error_message": None}
        try:
            # Get stock data using our centralized service
            stock, info = self._fetch_info(ticker)

            # Track data source
            data_source = "local"  # Default to local if it's coming from the database
            if 'source' in info and isinstance(info['source'], str):
                data_source = info['source'].lower()

            # Handle missing name
            try:
                name = info.get('shortName', info.get('longName', ticker))
            except:
                name = ticker

            # Get historical data (weekly) using our centralized service
            hist = self._fetch_history(stock, period="1y", interval="1wk")

            if hist is None or hist.empty:
                return {
                    "ticker": ticker,
                    "error": "No data available",
                    "error_message": f"Fel vid analys: ingen historik för {ticker}"
                }

            # Calculate current price
            price = hist['Close'].iloc[-1]

            # Calculate technical indicators
            tech_analysis = self._calculate_technical_indicators(hist)

            # Calculate fundamental indicators
            fund_analysis = self._calculate_fundamental_indicators(stock, info)

            # Calculate signal
            tech_score = self._calculate_tech_score(tech_analysis)
            fund_check = fund_analysis['fundamental_check']

            # Determine overall signal
            buy_signal = tech_score >= 70 and fund_check
            sell_signal = tech_score < 40 or not tech_analysis['above_ma40']

            # Process historical data to add indicators
            processed_hist = hist.copy()
            # Add moving averages
            processed_hist['MA4'] = processed_hist['Close'].rolling(
                window=self.ma_short).mean()
            processed_hist['MA40'] = processed_hist['Close'].rolling(
                window=self.ma_long).mean()
            # Add RSI
            processed_hist['RSI'] = self.calculate_rsi(
                processed_hist['Close'].values, window=self.rsi_period)
            # Add other indicators as needed for charting

            # Create results dictionary
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
                "historical_data": processed_hist,  # Use the processed data with indicators
                # Add the latest RSI value directly
                "rsi": tech_analysis.get('rsi', None),
                # Add data source information
                "data_source": data_source
            }

            # Combine technical and fundamental indicators into result
            result.update(tech_analysis)
            result.update(fund_analysis)

            return result

        except Exception as e:
            err = str(e)
            logging.error(f"Error analyzing {ticker}: {err}")
            return {
                "ticker": ticker,
                "error": err,
                "error_message": f"Fel vid analys: {err}"
            }

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
        data['MA4'] = data['Close'].rolling(window=self.ma_short).mean()
        data['MA40'] = data['Close'].rolling(window=self.ma_long).mean()

        # Calculate RSI with our improved function
        data['RSI'] = self.calculate_rsi(
            data['Close'].values, window=self.rsi_period)

        # Calculate higher lows (using new function)
        data['higher_lows'] = self._calculate_higher_lows(data)

        # 52-week highest level
        data['52w_high'] = data['High'].rolling(window=52).max()
        # Within 2% of highest level
        data['at_52w_high'] = (
            data['Close'] >= data['52w_high'] * self.near_high_threshold)

        # Consolidation phase breakout (simple implementation)
        data['volatility'] = data['Close'].pct_change().rolling(window=12).std()
        data['breakout'] = (data['volatility'].shift(4) < data['volatility']) & (
            data['Close'] > data['Close'].shift(4))

        # Get the latest data point
        latest = data.iloc[-1]

        # Return technical indicators as a dictionary
        return {
            "above_ma40": latest['Close'] > latest['MA40'] if not np.isnan(latest['MA40']) else False,
            "above_ma4": latest['Close'] > latest['MA4'] if not np.isnan(latest['MA4']) else False,
            "rsi_above_50": latest['RSI'] > self.rsi_threshold if not np.isnan(latest['RSI']) else False,
            # Add actual RSI value
            "rsi": float(latest['RSI']) if not np.isnan(latest['RSI']) else None,
            "higher_lows": bool(latest['higher_lows']),
            "near_52w_high": bool(latest['at_52w_high']),
            "breakout": bool(latest['breakout'])
        }

    def _calculate_fundamental_indicators(self, stock, info):
        """Calculate fundamental indicators from stock info"""
        # Initialize results dictionary with default values
        results = {
            "is_profitable": False,
            "pe_ratio": None,
            "revenue_growth": None,
            "profit_margin": None,
            "earnings_trend": "Okänd",
            "fundamental_check": False
        }

        try:
            # Check if company is profitable
            net_income = info.get('netIncomeToCommon')
            results["is_profitable"] = net_income is not None and net_income > 0

            # Get P/E ratio
            results["pe_ratio"] = info.get(
                'trailingPE') or info.get('forwardPE')

            # Get revenue growth
            revenue_growth = info.get('revenueGrowth')
            if revenue_growth is not None and pd.notna(revenue_growth):
                results["revenue_growth"] = revenue_growth

            # Get profit margin
            profit_margin = info.get('profitMargins')
            if profit_margin is not None and pd.notna(profit_margin):
                results["profit_margin"] = profit_margin

            # Get earnings trend data
            try:
                from data.stock_data import StockDataFetcher
                
                # Initialize the data fetcher
                fetcher = StockDataFetcher()
                
                # Get earnings data - this will need to be implemented
                # For now, set a default value
                results["earnings_trend"] = "Stabil"
            except Exception as e:
                self.logger.warning(f"Error fetching earnings data: {e}")
                results["earnings_trend"] = "Data saknas"

            # Determine if the fundamentals pass the criteria
            # Is the company profitable?
            profitable = results["is_profitable"]

            # Does it have a reasonable P/E ratio?
            pe_ratio = results["pe_ratio"]
            reasonable_pe = pe_ratio is None or (
                pe_ratio is not None and pe_ratio <= self.pe_max and pe_ratio > 0)

            # Check growth rates if available
            has_growth = results["revenue_growth"] is not None and results["revenue_growth"] > 0

            # Pass the fundamental check if profitable and reasonable P/E
            results["fundamental_check"] = profitable and reasonable_pe

            return results

        except Exception as e:
            self.logger.error(f"Error calculating fundamental indicators: {e}")
            return results
        
    def _calculate_tech_score(self, tech_analysis):
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
        
        Parameters:
        - tickers: List of stock ticker symbols
        - progress_callback: Function to call with progress updates (0-1.0 and text)
        
        Returns:
        - List of analysis result dictionaries
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
        
        # Sort by tech score (descending)
        results.sort(key=lambda x: x.get('tech_score', 0) if x.get('error') is None else -1, reverse=True)
        
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
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), height_ratios=[3, 1], sharex=True, gridspec_kw={'hspace': 0.05})
        
        # Plot main price chart with moving averages
        ax1.plot(data.index, data['Close'], label='Price', color='black', linewidth=1.5)
        
        if 'MA4' in data.columns:
            ax1.plot(data.index, data['MA4'], label=f'MA{self.ma_short} (Short)', color='blue', linewidth=1)
            
        if 'MA40' in data.columns:
            ax1.plot(data.index, data['MA40'], label=f'MA{self.ma_long} (Primary)', color='red', linewidth=1)
        
        # Add key technical markers
        last_date = data.index[-1]
        last_price = data['Close'].iloc[-1]
        
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
        ax1.set_title(f"{analysis['name']} ({analysis['ticker']}) - Tech Score: {analysis['tech_score']}/100", fontsize=14)
        ax1.set_ylabel('Price', fontsize=12)
        ax1.legend(loc='upper left')
        ax1.grid(True, alpha=0.3)
        
        # Plot RSI
        if 'RSI' in data.columns:
            ax2.plot(data.index, data['RSI'], label='RSI', color='purple', linewidth=1)
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