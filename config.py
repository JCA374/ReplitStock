import os

# API configurations
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")
YAHOO_FINANCE_ENABLED = True  # No API key needed for yfinance

# Database configuration
import os
DB_PATH = "stock_data.db"  # Fallback local database
DATABASE_URL = os.getenv("DATABASE_URL", "")  # Cloud database URL
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")  # Supabase API key

# Data refresh settings (in seconds)
DATA_REFRESH_INTERVAL = 14400  # 4 hours

# Technical analysis parameters
DEFAULT_SHORT_WINDOW = 20
DEFAULT_MEDIUM_WINDOW = 50
DEFAULT_LONG_WINDOW = 200
DEFAULT_RSI_PERIOD = 14
DEFAULT_MACD_FAST = 12
DEFAULT_MACD_SLOW = 26
DEFAULT_MACD_SIGNAL = 9

# Fundamental analysis thresholds
PE_LOW_THRESHOLD = 15
PE_HIGH_THRESHOLD = 30
PROFIT_MARGIN_THRESHOLD = 0.10  # 10%
REVENUE_GROWTH_THRESHOLD = 0.05  # 5%

# Timeframes for analysis
TIMEFRAMES = {
    'Daily': '1d',
    'Weekly': '1wk',
    'Monthly': '1mo'
}

# Period options
PERIOD_OPTIONS = {
    '1 Month': '1mo',
    '3 Months': '3mo',
    '6 Months': '6mo',
    'YTD': 'ytd',
    '1 Year': '1y',
    '2 Years': '2y',
    '5 Years': '5y',
    'Max': 'max'
}

# Stockholm exchange prefix
STOCKHOLM_EXCHANGE_SUFFIX = ".ST"

# Cache expiration in seconds
CACHE_EXPIRATION = 86400  # 24 hours

# Scanner criteria options
SCANNER_CRITERIA = {
    'pe_below': 'P/E Below',
    'pe_above': 'P/E Above',
    'profit_margin_above': 'Profit Margin Above',
    'revenue_growth_above': 'Revenue Growth Above',
    'price_above_sma': 'Price Above SMA',
    'price_below_sma': 'Price Below SMA',
    'rsi_overbought': 'RSI Overbought',
    'rsi_oversold': 'RSI Oversold',
    'macd_bullish': 'MACD Bullish',
    'macd_bearish': 'MACD Bearish',
    'price_near_52w_high': 'Price Near 52-Week High',
    'price_near_52w_low': 'Price Near 52-Week Low'
}
