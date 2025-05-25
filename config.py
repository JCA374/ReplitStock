import os

# API configurations
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")
YAHOO_FINANCE_ENABLED = True  # No API key needed for yfinance

# Data source priority
DEFAULT_DATA_SOURCE_PRIORITY = ['database', 'alphavantage', 'yahoo']
PREFERRED_API_SOURCE = 'alphavantage'  # Alpha Vantage as preferred API

# Database configuration
import os
# Use SQLite as reliable fallback when Supabase is unavailable
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



# Performance Monitoring
PERFORMANCE_LOGGING = {
    'enable_timing_logs': True,     # Log detailed timing information
    'enable_memory_tracking': False,  # Track memory usage (adds overhead)
    'log_batch_progress': True,     # Log progress for each batch
    'enable_db_stats': True,        # Log database operation statistics
}

# Add these settings to config.py

# Bulk Scanner Performance Settings
BULK_SCANNER_CONFIG = {
    # API Rate Limiting
    # Number of parallel API workers (3-5 recommended)
    'max_api_workers': 3,
    # Stocks per API batch (conservative for rate limits)
    'api_batch_size': 10,
    'api_batch_delay': 1.0,         # Seconds between API batches
    'single_request_delay': 0.1,    # Seconds between individual API requests

    # Database Performance
    'db_bulk_load_timeout': 30,     # Timeout for bulk database operations
    # Whether to load from multiple DB sources in parallel
    'enable_db_parallel_load': True,

    # Analysis Performance
    'analysis_batch_size': 20,      # Stocks per analysis batch
    'max_analysis_workers': 4,      # Number of parallel analysis workers

    # Memory Management
    'max_stocks_in_memory': 1000,   # Maximum stocks to process at once
    'enable_result_streaming': True,  # Stream results instead of holding all in memory

    # Caching Strategy
    'cache_fetched_data': True,     # Whether to cache API results
    'prioritize_fresh_data': False,  # Whether to prefer API data over cache

    # Error Handling
    'max_api_retries': 2,           # Number of API retry attempts
    'continue_on_api_failure': True,  # Whether to continue scan if some APIs fail
    # Stop scan if error rate exceeds this (30%)
    'error_threshold': 0.3,
}

# Performance Monitoring
PERFORMANCE_LOGGING = {
    'enable_timing_logs': True,     # Log detailed timing information
    'enable_memory_tracking': False,  # Track memory usage (adds overhead)
    'log_batch_progress': True,     # Log progress for each batch
    'enable_db_stats': True,        # Log database operation statistics
}


def get_bulk_scanner_config():
    """Get bulk scanner configuration with environment overrides"""
    import os

    config = BULK_SCANNER_CONFIG.copy()

    # Allow environment variable overrides for key settings
    config['max_api_workers'] = int(
        os.getenv('BULK_MAX_API_WORKERS', config['max_api_workers']))
    config['api_batch_size'] = int(
        os.getenv('BULK_API_BATCH_SIZE', config['api_batch_size']))
    config['analysis_batch_size'] = int(
        os.getenv('BULK_ANALYSIS_BATCH_SIZE', config['analysis_batch_size']))

    return config
