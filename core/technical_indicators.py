"""
Technical Indicators Calculator - Research-Backed Parameters

Implements evidence-based technical analysis indicators optimized for
Swedish stock market based on 2018-2025 academic research.

Key Features:
- RSI (7-period with Cardwell method)
- KAMA (Kaufman Adaptive Moving Average)
- Volume confirmation (1.5× requirement)
- 52-week high proximity
- MACD, Bollinger Bands, Moving Averages
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """
    Calculate technical indicators for stock price data.

    All indicators use research-backed parameters for optimal performance
    in Swedish stock market conditions.
    """

    def __init__(self, price_data: pd.DataFrame):
        """
        Initialize with price data

        Args:
            price_data: DataFrame with columns [Date, Open, High, Low, Close, Volume]
                       Index should be datetime
        """
        self.data = price_data.copy()
        self.data.index = pd.to_datetime(self.data.index)
        self.data = self.data.sort_index()  # Ensure chronological order

    def calculate_all(self, settings: Dict) -> Dict:
        """
        Calculate all technical indicators based on settings

        Args:
            settings: Analysis settings from SettingsManager

        Returns:
            Dict with all indicator values and scores
        """
        try:
            tech_settings = settings.get('technical', {})

            # Calculate individual indicators
            rsi = self.calculate_rsi(
                period=tech_settings.get('rsi_period', 7)
            )

            ma20 = self.calculate_sma(
                period=tech_settings.get('ma_short', 20)
            )

            ma200 = self.calculate_sma(
                period=tech_settings.get('ma_long', 200)
            )

            # KAMA if enabled, otherwise use SMA
            if tech_settings.get('use_kama', False):
                kama = self.calculate_kama(
                    period=tech_settings.get('kama_period', 10),
                    fast_ema=tech_settings.get('kama_fast_ema', 2),
                    slow_ema=tech_settings.get('kama_slow_ema', 30)
                )
            else:
                kama = ma20  # Fallback to MA20

            macd_line, macd_signal, macd_hist = self.calculate_macd(
                fast=tech_settings.get('macd_fast', 12),
                slow=tech_settings.get('macd_slow', 26),
                signal=tech_settings.get('macd_signal', 9)
            )

            bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(
                period=tech_settings.get('bollinger_period', 20),
                std_dev=tech_settings.get('bollinger_std', 2)
            )

            week52_high, week52_low = self.calculate_52week_high_low()

            volume_confirmed = self.check_volume_confirmation(
                multiplier=tech_settings.get('volume_multiplier', 1.5),
                lookback=tech_settings.get('volume_lookback_days', 20)
            )

            # Get current values
            current_price = self.data['Close'].iloc[-1]
            current_volume = self.data['Volume'].iloc[-1]

            # Calculate distances and percentages
            ma200_distance = ((current_price - ma200) / ma200 * 100) if ma200 else None
            ma20_distance = ((current_price - ma20) / ma20 * 100) if ma20 else None

            high52_proximity = ((current_price / week52_high) * 100) if week52_high else None

            # Check trend conditions
            above_ma200 = current_price > ma200 if ma200 else False
            above_ma20 = current_price > ma20 if ma20 else False

            # RSI Cardwell method: > 50 = bullish
            rsi_bullish = rsi > tech_settings.get('rsi_uptrend_threshold', 50) if rsi else False

            # MACD signal
            macd_bullish = macd_line > macd_signal if (macd_line and macd_signal) else False

            # Price action: check for higher lows (simplified)
            higher_lows = self.check_higher_lows()

            return {
                # Raw indicator values
                'rsi': rsi,
                'ma20': ma20,
                'ma200': ma200,
                'kama': kama,
                'macd_line': macd_line,
                'macd_signal': macd_signal,
                'macd_histogram': macd_hist,
                'bb_upper': bb_upper,
                'bb_middle': bb_middle,
                'bb_lower': bb_lower,
                'week52_high': week52_high,
                'week52_low': week52_low,
                'current_price': current_price,
                'current_volume': current_volume,

                # Calculated metrics
                'ma200_distance_pct': ma200_distance,
                'ma20_distance_pct': ma20_distance,
                'high52_proximity_pct': high52_proximity,

                # Boolean conditions
                'above_ma200': above_ma200,
                'above_ma20': above_ma20,
                'rsi_bullish': rsi_bullish,
                'macd_bullish': macd_bullish,
                'volume_confirmed': volume_confirmed,
                'higher_lows': higher_lows,

                # Status flags
                'data_sufficient': len(self.data) >= 200,
                'calculation_successful': True
            }

        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return {
                'calculation_successful': False,
                'error': str(e)
            }

    def calculate_rsi(self, period: int = 7) -> Optional[float]:
        """
        Calculate RSI (Relative Strength Index)

        Research-backed: 7-period RSI is more responsive than traditional 14-period
        Cardwell method: RSI > 50 indicates bullish momentum

        Args:
            period: RSI period (default 7, research-backed)

        Returns:
            Current RSI value (0-100)
        """
        try:
            if len(self.data) < period + 1:
                return None

            # Calculate price changes
            delta = self.data['Close'].diff()

            # Separate gains and losses
            gains = delta.where(delta > 0, 0)
            losses = -delta.where(delta < 0, 0)

            # Calculate average gains and losses (using EMA for smoothing)
            avg_gains = gains.ewm(span=period, adjust=False).mean()
            avg_losses = losses.ewm(span=period, adjust=False).mean()

            # Calculate RS and RSI
            rs = avg_gains / avg_losses
            rsi = 100 - (100 / (1 + rs))

            return float(rsi.iloc[-1])

        except Exception as e:
            logger.warning(f"RSI calculation failed: {e}")
            return None

    def calculate_sma(self, period: int) -> Optional[float]:
        """
        Calculate Simple Moving Average

        Args:
            period: Number of periods (e.g., 20, 200)

        Returns:
            Current SMA value
        """
        try:
            if len(self.data) < period:
                return None

            sma = self.data['Close'].rolling(window=period).mean()
            return float(sma.iloc[-1])

        except Exception as e:
            logger.warning(f"SMA calculation failed: {e}")
            return None

    def calculate_kama(
        self,
        period: int = 10,
        fast_ema: int = 2,
        slow_ema: int = 30
    ) -> Optional[float]:
        """
        Calculate KAMA (Kaufman Adaptive Moving Average)

        Research: Reduces false signals by 30-40% vs simple moving averages
        Adapts to market volatility (tight in trends, loose in sideways)

        Args:
            period: Efficiency ratio period
            fast_ema: Fast EMA constant
            slow_ema: Slow EMA constant

        Returns:
            Current KAMA value
        """
        try:
            if len(self.data) < period + 1:
                return None

            close = self.data['Close']

            # Calculate Efficiency Ratio (ER)
            change = abs(close - close.shift(period))
            volatility = close.diff().abs().rolling(window=period).sum()
            er = change / volatility

            # Calculate Smoothing Constant (SC)
            fast_sc = 2 / (fast_ema + 1)
            slow_sc = 2 / (slow_ema + 1)
            sc = (er * (fast_sc - slow_sc) + slow_sc) ** 2

            # Calculate KAMA
            kama = pd.Series(index=close.index, dtype=float)
            kama.iloc[period] = close.iloc[period]

            for i in range(period + 1, len(close)):
                kama.iloc[i] = kama.iloc[i-1] + sc.iloc[i] * (close.iloc[i] - kama.iloc[i-1])

            return float(kama.iloc[-1])

        except Exception as e:
            logger.warning(f"KAMA calculation failed: {e}")
            return None

    def calculate_macd(
        self,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """
        Calculate MACD (Moving Average Convergence Divergence)

        Args:
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line period

        Returns:
            Tuple of (macd_line, signal_line, histogram)
        """
        try:
            if len(self.data) < slow:
                return None, None, None

            close = self.data['Close']

            # Calculate EMAs
            ema_fast = close.ewm(span=fast, adjust=False).mean()
            ema_slow = close.ewm(span=slow, adjust=False).mean()

            # MACD line
            macd_line = ema_fast - ema_slow

            # Signal line
            signal_line = macd_line.ewm(span=signal, adjust=False).mean()

            # Histogram
            histogram = macd_line - signal_line

            return (
                float(macd_line.iloc[-1]),
                float(signal_line.iloc[-1]),
                float(histogram.iloc[-1])
            )

        except Exception as e:
            logger.warning(f"MACD calculation failed: {e}")
            return None, None, None

    def calculate_bollinger_bands(
        self,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """
        Calculate Bollinger Bands

        Args:
            period: Moving average period
            std_dev: Number of standard deviations

        Returns:
            Tuple of (upper_band, middle_band, lower_band)
        """
        try:
            if len(self.data) < period:
                return None, None, None

            close = self.data['Close']

            # Middle band (SMA)
            middle_band = close.rolling(window=period).mean()

            # Standard deviation
            std = close.rolling(window=period).std()

            # Upper and lower bands
            upper_band = middle_band + (std * std_dev)
            lower_band = middle_band - (std * std_dev)

            return (
                float(upper_band.iloc[-1]),
                float(middle_band.iloc[-1]),
                float(lower_band.iloc[-1])
            )

        except Exception as e:
            logger.warning(f"Bollinger Bands calculation failed: {e}")
            return None, None, None

    def calculate_52week_high_low(self) -> Tuple[Optional[float], Optional[float]]:
        """
        Calculate 52-week high and low

        Returns:
            Tuple of (high, low)
        """
        try:
            # Use last 252 trading days (approximately 1 year)
            lookback = min(252, len(self.data))

            if lookback < 50:  # Need reasonable amount of data
                return None, None

            recent_data = self.data.tail(lookback)

            week52_high = float(recent_data['High'].max())
            week52_low = float(recent_data['Low'].min())

            return week52_high, week52_low

        except Exception as e:
            logger.warning(f"52-week high/low calculation failed: {e}")
            return None, None

    def check_volume_confirmation(
        self,
        multiplier: float = 1.5,
        lookback: int = 20
    ) -> bool:
        """
        Check volume confirmation

        Research: 1.5× average volume = 65% success vs 39% without

        Args:
            multiplier: Required volume multiplier (default 1.5)
            lookback: Days to calculate average volume

        Returns:
            True if current volume meets requirement
        """
        try:
            if len(self.data) < lookback + 1:
                return False

            # Calculate average volume
            avg_volume = self.data['Volume'].tail(lookback).mean()

            # Current volume
            current_volume = self.data['Volume'].iloc[-1]

            # Check if meets threshold
            return current_volume >= (avg_volume * multiplier)

        except Exception as e:
            logger.warning(f"Volume confirmation check failed: {e}")
            return False

    def check_higher_lows(self, lookback: int = 20) -> bool:
        """
        Check for higher lows pattern (simplified)

        Args:
            lookback: Number of periods to check

        Returns:
            True if pattern detected
        """
        try:
            if len(self.data) < lookback:
                return False

            recent_lows = self.data['Low'].tail(lookback)

            # Find local lows (simplified: every 5 days)
            lows = []
            for i in range(0, len(recent_lows) - 5, 5):
                segment = recent_lows.iloc[i:i+5]
                lows.append(segment.min())

            if len(lows) < 2:
                return False

            # Check if lows are generally increasing
            increasing_count = sum(1 for i in range(1, len(lows)) if lows[i] > lows[i-1])

            return increasing_count >= (len(lows) - 1) * 0.6  # 60% of lows should be higher

        except Exception as e:
            logger.warning(f"Higher lows check failed: {e}")
            return False


def calculate_technical_score(indicators: Dict, settings: Dict) -> Dict:
    """
    Calculate overall technical score based on indicators

    Uses research-backed weighting:
    - MA alignment: 30 points
    - RSI momentum: 20 points
    - Price action: 25 points
    - MACD signal: 15 points
    - Volume trend: 10 points

    Args:
        indicators: Dict from TechnicalIndicators.calculate_all()
        settings: Analysis settings

    Returns:
        Dict with technical score and breakdown
    """
    if not indicators.get('calculation_successful', False):
        return {
            'technical_score': 0,
            'score_breakdown': {},
            'passed_filters': False
        }

    scoring = settings.get('scoring', {})
    tech_components = scoring.get('technical_components', {})

    scores = {}

    # 1. MA Alignment (30 points)
    ma_score = 0
    if indicators.get('above_ma200'):
        ma_score += 20  # Long-term uptrend (most important)
    if indicators.get('above_ma20'):
        ma_score += 10  # Short-term momentum
    scores['ma_alignment'] = ma_score

    # 2. RSI Momentum (20 points)
    rsi = indicators.get('rsi')
    rsi_score = 0
    if rsi:
        if rsi > 50:  # Cardwell method: bullish
            rsi_score += 10
        if 50 <= rsi <= 70:  # Sweet spot: bullish but not overbought
            rsi_score += 10
        elif rsi > 70:  # Overbought warning
            rsi_score += 5
    scores['rsi_momentum'] = rsi_score

    # 3. Price Action (25 points)
    price_score = 0
    high52_prox = indicators.get('high52_proximity_pct')
    if high52_prox:
        if high52_prox >= 90:  # Within 10% of 52-week high
            price_score += 15
        elif high52_prox >= 85:  # Within 15% of 52-week high
            price_score += 10
        elif high52_prox >= 75:
            price_score += 5

    if indicators.get('higher_lows'):
        price_score += 10  # Pattern of strength
    scores['price_action'] = price_score

    # 4. MACD Signal (15 points)
    macd_score = 0
    if indicators.get('macd_bullish'):
        macd_score += 10

    macd_hist = indicators.get('macd_histogram')
    if macd_hist and macd_hist > 0:
        macd_score += 5  # Positive histogram
    scores['macd_signal'] = macd_score

    # 5. Volume Trend (10 points)
    volume_score = 0
    if indicators.get('volume_confirmed'):
        volume_score += 10  # Critical: 1.5× average volume
    scores['volume_trend'] = volume_score

    # Calculate total technical score
    total_score = sum(scores.values())

    # Check if passed minimum filters
    momentum_settings = settings.get('analysis', {}).get('momentum', {})

    passed_filters = True
    filter_results = {}

    if momentum_settings.get('require_above_ma200', False):
        passed = indicators.get('above_ma200', False)
        filter_results['ma200_filter'] = passed
        passed_filters = passed_filters and passed

    if momentum_settings.get('require_above_ma20', False):
        passed = indicators.get('above_ma20', False)
        filter_results['ma20_filter'] = passed
        passed_filters = passed_filters and passed

    if momentum_settings.get('require_rsi_above_50', False):
        passed = indicators.get('rsi_bullish', False)
        filter_results['rsi_filter'] = passed
        passed_filters = passed_filters and passed

    if momentum_settings.get('require_volume_confirmation', False):
        passed = indicators.get('volume_confirmed', False)
        filter_results['volume_filter'] = passed
        passed_filters = passed_filters and passed

    return {
        'technical_score': total_score,
        'score_breakdown': scores,
        'passed_filters': passed_filters,
        'filter_results': filter_results,
        'max_possible_score': 100
    }
