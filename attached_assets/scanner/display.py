# scanner/display.py
import streamlit as st
import pandas as pd
from data.stock_data import StockDataFetcher
from analysis.technical import calculate_all_indicators, generate_technical_signals

def process_technical_indicators(ticker, period="1y", interval="1wk"):
    """
    Process and return the technical indicators for a single stock
    
    Args:
        ticker (str): Stock ticker symbol
        period (str): Time period (1mo, 3mo, 6mo, 1y, etc.)
        interval (str): Time interval (1d, 1wk, etc.)
        
    Returns:
        dict: Dictionary of technical indicators and their values
    """
    try:
        # Get stock data
        data_fetcher = StockDataFetcher()
        stock_data = data_fetcher.get_stock_data(ticker, timeframe=interval, period=period)
        
        if stock_data is None or stock_data.empty:
            return None
            
        # Calculate technical indicators
        indicators = calculate_all_indicators(stock_data)
        
        # Generate signals from indicators
        signals = generate_technical_signals(indicators)
        
        # Extract the latest values for display
        latest_price = stock_data['close'].iloc[-1] if not stock_data.empty else None
        
        # Get specific indicator values
        result = {
            'ticker': ticker,
            'last_price': latest_price,
            'tech_score': signals.get('tech_score', 0),
            'signal': signals.get('overall_signal', 'NEUTRAL'),
            'strength': f"{signals.get('tech_score', 0)}%",
            'rsi': indicators.get('rsi', pd.Series()).iloc[-1] if 'rsi' in indicators and not indicators['rsi'].empty else None,
            'sma_short': indicators.get('sma_short', pd.Series()).iloc[-1] if 'sma_short' in indicators and not indicators['sma_short'].empty else None,
            'sma_medium': indicators.get('sma_medium', pd.Series()).iloc[-1] if 'sma_medium' in indicators and not indicators['sma_medium'].empty else None,
            'sma_long': indicators.get('sma_long', pd.Series()).iloc[-1] if 'sma_long' in indicators and not indicators['sma_long'].empty else None,
            'vs_sma_short': "Above" if latest_price > result['sma_short'] if result['sma_short'] else False else "Below" if result['sma_short'] else "N/A",
            'vs_sma_medium': "Above" if latest_price > result['sma_medium'] if result['sma_medium'] else False else "Below" if result['sma_medium'] else "N/A",
            'vs_sma_long': "Above" if latest_price > result['sma_long'] if result['sma_long'] else False else "Below" if result['sma_long'] else "N/A",
            'macd_signal': "Bullish" if signals.get('macd_bullish_cross', False) else "Bearish" if signals.get('macd_bearish_cross', False) else "Neutral",
            'near_52w_high': "Yes" if signals.get('near_52w_high', False) else "No",
            'breakout': "Yes" if signals.get('breakout_up', False) else "No"
        }
        
        return result
    except Exception as e:
        print(f"Error processing technical indicators for {ticker}: {e}")
        return None

def create_technical_indicators_df(results):
    """
    Create a DataFrame with technical indicators from scan results
    
    Args:
        results (list): List of scan result dictionaries
        
    Returns:
        pd.DataFrame: DataFrame with technical indicators
    """
    if not results:
        return pd.DataFrame()
        
    # Extract technical indicators
    tech_data = []
    for result in results:
        ticker = result.get('Ticker')
        
        # Process technical indicators for this ticker
        tech_indicators = process_technical_indicators(ticker)
        
        if tech_indicators:
            tech_data.append({
                'Ticker': ticker,
                'Tech Score': tech_indicators['tech_score'],
                'Signal': tech_indicators['signal'],
                'Strength': tech_indicators['strength'],
                'RSI': f"{tech_indicators['rsi']:.2f}" if tech_indicators['rsi'] is not None else "N/A",
                'vs SMA20': tech_indicators['vs_sma_short'],
                'vs SMA50': tech_indicators['vs_sma_medium'],
                'vs SMA200': tech_indicators['vs_sma_long'],
                'MACD': tech_indicators['macd_signal'],
                'Near 52w High': tech_indicators['near_52w_high'],
                'Breakout': tech_indicators['breakout']
            })
    
    return pd.DataFrame(tech_data)