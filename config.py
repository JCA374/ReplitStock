# config.py - OPTIMIZED VERSION with reduced delays

import os

# API configurations
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")
YAHOO_FINANCE_ENABLED = True  # No API key needed for yfinance

# Data source priority
DEFAULT_DATA_SOURCE_PRIORITY = ['database', 'alphavantage', 'yahoo']
PREFERRED_API_SOURCE = 'alphavantage'  # Alpha Vantage as preferred API

# Database configuration
# Use SQLite as reliable fallback when Supabase is unavailable
DB_PATH = "stock_data.db"  # Fallback local database
DATABASE_URL = os.getenv("DATABASE_URL", "")  # Cloud database URL
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")  # Supabase API key

# OPTIMIZED Data refresh settings (in seconds) - More aggressive caching
DATA_REFRESH_INTERVAL = 21600  # 6 hours instead of 4 hours for better caching

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

# OPTIMIZED Cache expiration - More aggressive caching
CACHE_EXPIRATION = 172800  # 48 hours instead of 24 hours

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

# ULTRA-OPTIMIZED Bulk Scanner Performance Settings
BULK_SCANNER_CONFIG = {
    # OPTIMIZED API Rate Limiting - Reduced delays for faster processing
    'max_api_workers': 6,           # Increased from 3 to 6 for faster API calls
    'api_batch_size': 15,           # Increased from 10 to 15 for bigger batches
    'api_batch_delay': 0.5,         # Reduced from 1.0s to 0.5s between batches
    'single_request_delay': 0.05,   # Reduced from 0.1s to 0.05s between requests

    # OPTIMIZED Database Performance
    'db_bulk_load_timeout': 60,     # Increased timeout for large datasets
    'enable_db_parallel_load': True,
    'db_connection_pool_size': 10,  # Connection pooling for faster DB access

    # OPTIMIZED Analysis Performance
    'analysis_batch_size': 30,      # Increased from 20 to 30 for bigger batches
    'max_analysis_workers': 8,      # Increased from 4 to 8 for more parallelism

    # OPTIMIZED Memory Management
    'max_stocks_in_memory': 2000,   # Increased from 1000 to 2000
    'enable_result_streaming': True,
    'enable_memory_optimization': True,  # Enable memory optimization techniques

    # OPTIMIZED Caching Strategy
    'cache_fetched_data': True,
    'prioritize_fresh_data': False,
    'aggressive_caching': True,      # Enable aggressive caching for speed
    'cache_compression': True,       # Compress cached data to save space

    # OPTIMIZED Error Handling
    'max_api_retries': 1,           # Reduced from 2 to 1 for faster failure handling
    'continue_on_api_failure': True,
    'error_threshold': 0.2,         # Reduced from 0.3 to 0.2 for stricter error handling
    'timeout_per_stock': 10,        # 10 second timeout per stock analysis
}

# OPTIMIZED Performance Monitoring
PERFORMANCE_LOGGING = {
    'enable_timing_logs': True,
    'enable_memory_tracking': False,  # Disabled for better performance
    'log_batch_progress': True,
    'enable_db_stats': True,
    'enable_performance_metrics': True,  # Enable performance metrics collection
}

# OPTIMIZED API Delay Settings - Significantly reduced delays
API_DELAYS = {
    # Reduced from 12s to 6s (still respects rate limits)
    'alpha_vantage_delay': 6,
    'yahoo_finance_delay': 0.05,   # Reduced from 1s to 0.05s
    'general_api_delay': 0.02,      # Very small delay for general API calls
    'batch_api_delay': 0.3,         # Delay between API batches
}

# OPTIMIZED Cache Settings for Different Data Types
CACHE_SETTINGS = {
    # 48 hours for fundamentals (changes slowly)
    'fundamentals_cache_hours': 48,
    'price_data_cache_hours': 6,        # 6 hours for price data
    'intraday_cache_hours': 1,          # 1 hour for intraday data
    'technical_indicators_cache_hours': 3,  # 3 hours for technical indicators
    'enable_smart_cache_invalidation': True,  # Smart cache invalidation
}

# ZERO-DELAY UI Settings
UI_SETTINGS = {
    # Remove time.sleep from success messages
    'remove_success_message_delays': True,
    'enable_instant_feedback': True,          # Instant UI feedback
    'optimize_button_responses': True,        # Optimize button response times
    'reduce_rerun_delays': True,              # Reduce st.rerun delays
    'enable_async_ui_updates': False,         # Async UI updates (experimental)
}


def get_optimized_bulk_scanner_config():
    """Get optimized bulk scanner configuration with environment overrides"""
    import os

    config = BULK_SCANNER_CONFIG.copy()

    # Allow environment variable overrides for key settings
    config['max_api_workers'] = int(
        os.getenv('BULK_MAX_API_WORKERS', config['max_api_workers']))
    config['api_batch_size'] = int(
        os.getenv('BULK_API_BATCH_SIZE', config['api_batch_size']))
    config['analysis_batch_size'] = int(
        os.getenv('BULK_ANALYSIS_BATCH_SIZE', config['analysis_batch_size']))
    config['max_analysis_workers'] = int(
        os.getenv('BULK_MAX_ANALYSIS_WORKERS', config['max_analysis_workers']))

    return config


def get_api_delay_config():
    """Get API delay configuration"""
    return API_DELAYS


def get_cache_config():
    """Get cache configuration"""
    return CACHE_SETTINGS


def get_ui_config():
    """Get UI optimization configuration"""
    return UI_SETTINGS
