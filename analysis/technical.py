import pandas as pd
import numpy as np
from config import (
    DEFAULT_SHORT_WINDOW,
    DEFAULT_MEDIUM_WINDOW,
    DEFAULT_LONG_WINDOW,
    DEFAULT_RSI_PERIOD,
    DEFAULT_MACD_FAST,
    DEFAULT_MACD_SLOW,
    DEFAULT_MACD_SIGNAL
)

def calculate_sma(data, window):
    """Calculate Simple Moving Average."""
    return data['close'].rolling(window=window).mean()

def calculate_ema(data, window):
    """Calculate Exponential Moving Average."""
    return data['close'].ewm(span=window, adjust=False).mean()

def calculate_rsi(data, period=DEFAULT_RSI_PERIOD):
    """Calculate Relative Strength Index."""
    delta = data['close'].diff()
    
    # Get gains and losses
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    # Calculate average gain and loss
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    # Calculate RS
    rs = avg_gain / avg_loss
    
    # Calculate RSI
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def calculate_macd(data, fast_period=DEFAULT_MACD_FAST, slow_period=DEFAULT_MACD_SLOW, signal_period=DEFAULT_MACD_SIGNAL):
    """Calculate MACD (Moving Average Convergence Divergence)."""
    # Calculate the fast and slow EMAs
    ema_fast = data['close'].ewm(span=fast_period, adjust=False).mean()
    ema_slow = data['close'].ewm(span=slow_period, adjust=False).mean()
    
    # Calculate MACD line
    macd_line = ema_fast - ema_slow
    
    # Calculate signal line
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    
    # Calculate histogram
    histogram = macd_line - signal_line
    
    return pd.DataFrame({
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram
    })

def calculate_bollinger_bands(data, window=20, num_std=2):
    """Calculate Bollinger Bands."""
    sma = data['close'].rolling(window=window).mean()
    std = data['close'].rolling(window=window).std()
    
    upper_band = sma + (std * num_std)
    lower_band = sma - (std * num_std)
    
    return pd.DataFrame({
        'middle': sma,
        'upper': upper_band,
        'lower': lower_band
    })

def detect_price_pattern(data):
    """Detect basic price patterns."""
    # Look at recent data
    recent_data = data.iloc[-60:] if len(data) > 60 else data
    
    # Calculate 52-week high and low
    year_data = data.iloc[-252:] if len(data) > 252 else data
    high_52w = year_data['high'].max()
    low_52w = year_data['low'].min()
    
    # Current price
    current_price = data['close'].iloc[-1]
    
    # Calculate proximity to 52-week high/low
    proximity_to_high = (current_price - low_52w) / (high_52w - low_52w) if (high_52w - low_52w) > 0 else 0
    
    # Check for higher lows pattern (uptrend)
    lows = recent_data['low'].rolling(window=10).min()
    higher_lows = lows.is_monotonic_increasing
    
    # Check for lower highs pattern (downtrend)
    highs = recent_data['high'].rolling(window=10).max()
    lower_highs = highs.is_monotonic_decreasing
    
    # Check if near 52-week high or low
    near_high = current_price >= high_52w * 0.95
    near_low = current_price <= low_52w * 1.05
    
    # Identify the pattern
    pattern = {
        'higher_lows': higher_lows,
        'lower_highs': lower_highs,
        'near_52w_high': near_high,
        'near_52w_low': near_low,
        'proximity_to_high': proximity_to_high
    }
    
    return pattern

def detect_breakout(data, window=20):
    """Detect price breakouts."""
    # Calculate recent volatility
    volatility = data['close'].pct_change().std() * np.sqrt(252)
    
    # Calculate upper and lower channel
    upper_channel = data['high'].rolling(window=window).max()
    lower_channel = data['low'].rolling(window=window).min()
    
    # Current price
    current_price = data['close'].iloc[-1]
    prev_price = data['close'].iloc[-2] if len(data) > 1 else current_price
    
    # Previous upper and lower channel values
    prev_upper = upper_channel.iloc[-2] if len(upper_channel) > 1 else upper_channel.iloc[-1]
    prev_lower = lower_channel.iloc[-2] if len(lower_channel) > 1 else lower_channel.iloc[-1]
    
    # Check for breakouts
    breakout_up = current_price > prev_upper and prev_price <= prev_upper
    breakout_down = current_price < prev_lower and prev_price >= prev_lower
    
    # Significant volume increase?
    avg_volume = data['volume'].rolling(window=window).mean().iloc[-1]
    current_volume = data['volume'].iloc[-1]
    volume_surge = current_volume > avg_volume * 1.5 if not pd.isna(avg_volume) and avg_volume > 0 else False
    
    # Breakout strength based on volatility
    if breakout_up or breakout_down:
        channel_width = (prev_upper - prev_lower) / prev_lower
        strength = channel_width / volatility if volatility > 0 else 0
    else:
        strength = 0
    
    return {
        'breakout_up': breakout_up,
        'breakout_down': breakout_down,
        'volume_surge': volume_surge,
        'strength': strength
    }

def calculate_52week_high_proximity(data):
    """
    Calculate the 52-week high and proximity of current price to it.
    
    Args:
        data (pd.DataFrame): DataFrame with OHLC price data
        
    Returns:
        tuple: (52-week high value, proximity ratio [0-1])
    """
    if data.empty or len(data) < 20:  # Need some reasonable amount of data
        return 0, 1.0
    
    try:
        # Use up to 252 trading days (approximately one year)
        lookback = min(252, len(data))
        year_data = data[-lookback:].copy()
        
        # Find 52-week high and current price
        high_52w = year_data['high'].max()
        current_price = data['close'].iloc[-1]
        
        # Calculate proximity (0 = at high, 1 = far below)
        proximity = (high_52w - current_price) / high_52w if high_52w > 0 else 1.0
        
        return high_52w, max(0, min(1, proximity))  # Ensure value is between 0-1
        
    except Exception as e:
        print(f"Error calculating 52-week high: {e}")
        return 0, 1.0

def calculate_all_indicators(data):
    """Calculate all technical indicators for a dataset."""
    if data.empty:
        return {}
    
    # Ensure we have enough data
    if len(data) < DEFAULT_LONG_WINDOW:
        return {}
    
    try:
        # Store original data for reference
        result = {'original_data': data}
        
        # Standard technical indicators
        result['sma_short'] = calculate_sma(data, DEFAULT_SHORT_WINDOW)
        result['sma_medium'] = calculate_sma(data, DEFAULT_MEDIUM_WINDOW)
        result['sma_long'] = calculate_sma(data, DEFAULT_LONG_WINDOW)
        
        # Calculate EMAs
        result['ema_short'] = calculate_ema(data, DEFAULT_SHORT_WINDOW)
        result['ema_medium'] = calculate_ema(data, DEFAULT_MEDIUM_WINDOW)
        result['ema_long'] = calculate_ema(data, DEFAULT_LONG_WINDOW)
        
        # Value & Momentum Strategy specific indicators
        # MA4 (4-week moving average) for short-term momentum
        result['ma4'] = calculate_sma(data, 20)  # Assuming 20 trading days = ~4 weeks
        
        # MA40 (40-week moving average) for primary trend
        result['ma40'] = calculate_sma(data, 200)  # Assuming 200 trading days = ~40 weeks
        
        # Calculate RSI
        result['rsi'] = calculate_rsi(data)
        
        # Calculate MACD
        macd_data = calculate_macd(data)
        result['macd'] = macd_data['macd']
        result['macd_signal'] = macd_data['signal']
        result['macd_histogram'] = macd_data['histogram']
        
        # Calculate Bollinger Bands
        bollinger = calculate_bollinger_bands(data)
        result['bollinger_middle'] = bollinger['middle']
        result['bollinger_upper'] = bollinger['upper']
        result['bollinger_lower'] = bollinger['lower']
        
        # Price patterns and breakouts
        result['price_pattern'] = detect_price_pattern(data)
        result['breakout'] = detect_breakout(data)
        
        # Calculate 52-week high proximity
        high_52w, proximity = calculate_52week_high_proximity(data)
        result['52w_high'] = high_52w
        result['52w_high_proximity'] = proximity
        result['near_52w_high'] = proximity < 0.10  # Within 10% of 52-week high
        
        return result
    
    except Exception as e:
        print(f"Error calculating indicators: {e}")
        return {}

def generate_technical_signals(indicators):
    """Generate trading signals based on technical indicators."""
    if not indicators:
        return {}
    
    signals = {}
    
    # Get latest values
    try:
        # Use the price_pattern if available, otherwise try to get from original data
        if 'price_pattern' in indicators and indicators['price_pattern'] and 'current_price' in indicators['price_pattern']:
            latest_price = indicators['price_pattern'].get('current_price', 0)
        elif 'original_data' in indicators and not indicators['original_data'].empty:
            latest_price = indicators['original_data']['close'].iloc[-1]
        else:
            latest_price = 0
            
        latest_sma_short = indicators['sma_short'].iloc[-1] if ('sma_short' in indicators and not indicators['sma_short'].empty) else 0
        latest_sma_medium = indicators['sma_medium'].iloc[-1] if ('sma_medium' in indicators and not indicators['sma_medium'].empty) else 0
        latest_sma_long = indicators['sma_long'].iloc[-1] if ('sma_long' in indicators and not indicators['sma_long'].empty) else 0
        latest_rsi = indicators['rsi'].iloc[-1] if ('rsi' in indicators and not indicators['rsi'].empty) else 0
        latest_macd = indicators['macd'].iloc[-1] if ('macd' in indicators and not indicators['macd'].empty) else 0
        latest_macd_signal = indicators['macd_signal'].iloc[-1] if ('macd_signal' in indicators and not indicators['macd_signal'].empty) else 0
        
        # Price vs. Moving Averages
        signals['price_above_sma_short'] = latest_price > latest_sma_short if latest_sma_short > 0 else None
        signals['price_above_sma_medium'] = latest_price > latest_sma_medium if latest_sma_medium > 0 else None
        signals['price_above_sma_long'] = latest_price > latest_sma_long if latest_sma_long > 0 else None
        
        # Moving Average Cross
        signals['sma_short_above_medium'] = latest_sma_short > latest_sma_medium if (latest_sma_short > 0 and latest_sma_medium > 0) else None
        signals['sma_short_above_long'] = latest_sma_short > latest_sma_long if (latest_sma_short > 0 and latest_sma_long > 0) else None
        
        # RSI Signals
        if latest_rsi is not None and not pd.isna(latest_rsi):
            signals['rsi_overbought'] = latest_rsi > 70
            signals['rsi_oversold'] = latest_rsi < 30
            signals['rsi_value'] = latest_rsi
        else:
            signals['rsi_overbought'] = None
            signals['rsi_oversold'] = None
            signals['rsi_value'] = None
        
        # MACD Signals
        if latest_macd is not None and latest_macd_signal is not None and not pd.isna(latest_macd) and not pd.isna(latest_macd_signal):
            signals['macd_bullish_cross'] = (latest_macd > latest_macd_signal)
            signals['macd_bearish_cross'] = (latest_macd < latest_macd_signal)
        else:
            signals['macd_bullish_cross'] = None
            signals['macd_bearish_cross'] = None
        
        # Price Patterns
        if 'price_pattern' in indicators:
            pattern = indicators['price_pattern']
            signals['higher_lows'] = pattern.get('higher_lows', None)
            signals['lower_highs'] = pattern.get('lower_highs', None)
            signals['near_52w_high'] = pattern.get('near_52w_high', None)
            signals['near_52w_low'] = pattern.get('near_52w_low', None)
        
        # Breakouts
        if 'breakout' in indicators:
            breakout = indicators['breakout']
            signals['breakout_up'] = breakout.get('breakout_up', None)
            signals['breakout_down'] = breakout.get('breakout_down', None)
            signals['volume_surge'] = breakout.get('volume_surge', None)
        
        # Overall signal
        bullish_signals = sum([1 for signal in [
            signals.get('price_above_sma_short', False),
            signals.get('price_above_sma_medium', False),
            signals.get('price_above_sma_long', False),
            signals.get('sma_short_above_medium', False),
            signals.get('sma_short_above_long', False),
            signals.get('rsi_oversold', False),
            signals.get('macd_bullish_cross', False),
            signals.get('higher_lows', False),
            signals.get('near_52w_high', False),
            signals.get('breakout_up', False),
            signals.get('volume_surge', False)
        ] if signal])
        
        bearish_signals = sum([1 for signal in [
            not signals.get('price_above_sma_short', True),
            not signals.get('price_above_sma_medium', True),
            not signals.get('price_above_sma_long', True),
            not signals.get('sma_short_above_medium', True),
            not signals.get('sma_short_above_long', True),
            signals.get('rsi_overbought', False),
            signals.get('macd_bearish_cross', False),
            signals.get('lower_highs', False),
            signals.get('near_52w_low', False),
            signals.get('breakout_down', False)
        ] if signal])
        
        # Calculate overall strength
        total_signals = 11  # Total number of signals we're checking
        bullish_strength = bullish_signals / total_signals if total_signals > 0 else 0
        bearish_strength = bearish_signals / total_signals if total_signals > 0 else 0
        
        signals['overall_signal'] = 'bullish' if bullish_strength > bearish_strength else 'bearish'
        signals['signal_strength'] = max(bullish_strength, bearish_strength)
        
        return signals
    
    except Exception as e:
        print(f"Error generating signals: {e}")
        return {}
