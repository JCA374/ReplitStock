from sqlalchemy import Boolean, Column, Integer, String, Float, BigInteger, Text, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base

# SQLAlchemy Base class for ORM
Base = declarative_base()

class Watchlist(Base):
    __tablename__ = 'watchlist'
    
    id = Column(Integer, primary_key=True)
    ticker = Column(String(20), unique=True)
    name = Column(String(100))
    exchange = Column(String(50))
    sector = Column(String(50))
    added_date = Column(String(20))
    
    def __repr__(self):
        return f"<Watchlist(ticker='{self.ticker}', name='{self.name}')>"

class StockDataCache(Base):
    __tablename__ = 'stock_data_cache'
    
    id = Column(Integer, primary_key=True)
    ticker = Column(String(20))
    timeframe = Column(String(10))
    period = Column(String(10))
    data = Column(Text)  # JSON string of the pandas DataFrame
    timestamp = Column(BigInteger)  # Unix timestamp for cache expiry
    source = Column(String(20))  # Data source (e.g., 'yahoo', 'alpha_vantage')
    
    # Enforce uniqueness for the combination of fields
    __table_args__ = (
        UniqueConstraint('ticker', 'timeframe', 'period', 'source', name='stock_data_cache_unique'),
    )
    
    def __repr__(self):
        return f"<StockDataCache(ticker='{self.ticker}', timeframe='{self.timeframe}', period='{self.period}')>"

class AnalysisResults(Base):
    __tablename__ = 'analysis_results'

    id = Column(Integer, primary_key=True)
    ticker = Column(String(20), nullable=False)
    analysis_date = Column(String(50), nullable=False)
    price = Column(Float)
    tech_score = Column(Integer)
    signal = Column(String(10))
    above_ma40 = Column(Boolean)
    above_ma4 = Column(Boolean)
    rsi_value = Column(Float)
    rsi_above_50 = Column(Boolean)
    near_52w_high = Column(Boolean)
    pe_ratio = Column(Float)
    profit_margin = Column(Float)
    revenue_growth = Column(Float)
    is_profitable = Column(Boolean)
    data_source = Column(String(20))
    last_updated = Column(BigInteger)

    __table_args__ = (
        UniqueConstraint('ticker', 'analysis_date',
                         name='analysis_results_unique'),
    )

    def __repr__(self):
        return f"<AnalysisResults(ticker='{self.ticker}', date='{self.analysis_date}', signal='{self.signal}')>"

class FundamentalsCache(Base):
    __tablename__ = 'fundamentals_cache'
    
    id = Column(Integer, primary_key=True)
    ticker = Column(String(20), unique=True)
    pe_ratio = Column(Float)
    profit_margin = Column(Float)
    revenue_growth = Column(Float)
    earnings_growth = Column(Float)
    book_value = Column(Float)
    market_cap = Column(Float)
    dividend_yield = Column(Float)
    last_updated = Column(BigInteger)  # Unix timestamp for cache expiry
    
    def __repr__(self):
        return f"<FundamentalsCache(ticker='{self.ticker}', pe_ratio={self.pe_ratio})>"

# Enhanced Watchlist Models
class WatchlistCategory(Base):
    __tablename__ = 'watchlist_categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    color = Column(String(7))  # Hex color for UI
    icon = Column(String(20))  # Emoji or icon name
    description = Column(String(200))
    created_date = Column(String(20))
    
    def __repr__(self):
        return f"<WatchlistCategory(name='{self.name}', icon='{self.icon}')>"

class WatchlistItem(Base):
    __tablename__ = 'watchlist_items_v2'
    
    id = Column(Integer, primary_key=True)
    ticker = Column(String(20))
    category_id = Column(Integer)  # Foreign key to categories
    tags = Column(Text)  # JSON array of tags
    notes = Column(Text)  # User notes
    target_price = Column(Float)  # Price alerts
    stop_loss = Column(Float)
    added_date = Column(String(20))
    added_price = Column(Float)  # Track performance
    
    __table_args__ = (
        UniqueConstraint('ticker', 'category_id', name='unique_ticker_category'),
    )
    
    def __repr__(self):
        return f"<WatchlistItem(ticker='{self.ticker}', category_id={self.category_id})>"

class WatchlistAlert(Base):
    __tablename__ = 'watchlist_alerts'
    
    id = Column(Integer, primary_key=True)
    ticker = Column(String(20))
    alert_type = Column(String(20))  # 'price_above', 'price_below', 'tech_signal'
    threshold = Column(Float)
    message = Column(String(200))
    is_active = Column(Boolean, default=True)
    created_date = Column(String(20))
    triggered_date = Column(String(20))
    
    def __repr__(self):
        return f"<WatchlistAlert(ticker='{self.ticker}', type='{self.alert_type}', threshold={self.threshold})>"

class WatchlistCollection(Base):
    __tablename__ = 'watchlist_collections'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True)
    description = Column(String(200))
    created_date = Column(String(20))
    is_default = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<WatchlistCollection(name='{self.name}')>"

class WatchlistMembership(Base):
    __tablename__ = 'watchlist_memberships'
    
    id = Column(Integer, primary_key=True)
    collection_id = Column(Integer)
    ticker = Column(String(20))
    name = Column(String(200), nullable=True)  # Add company name field
    added_date = Column(String(20))
    
    __table_args__ = (
        UniqueConstraint('collection_id', 'ticker', name='unique_collection_ticker'),
    )
    
    def __repr__(self):
        return f"<WatchlistMembership(collection_id={self.collection_id}, ticker='{self.ticker}')>"


# ============================================================================
# NEW MODELS FOR AUTOMATIC ANALYSIS SYSTEM
# ============================================================================

class StockUniverse(Base):
    """
    Complete universe of Swedish stocks for automatic analysis.
    Tracks all 355 stocks with current market cap categorization.
    """
    __tablename__ = 'stock_universe'

    id = Column(Integer, primary_key=True)
    ticker = Column(String(20), unique=True, nullable=False)
    name = Column(String(100))
    sector = Column(String(50))
    industry = Column(String(50))

    # Market cap data (updated from fundamentals)
    market_cap = Column(Float)                  # Current market cap in SEK
    market_cap_tier = Column(String(20))        # 'large_cap', 'mid_cap', 'small_cap'
    csv_category = Column(String(20))           # Original category from CSV file

    # Trading metrics
    avg_volume_30d = Column(Float)              # 30-day average volume
    avg_value_sek_30d = Column(Float)           # 30-day average value traded in SEK

    # Metadata
    last_updated = Column(BigInteger)           # When this record was last updated
    is_active = Column(Boolean, default=True)   # Is stock currently active/trading
    delisting_date = Column(String(20))         # Date when delisted (if applicable)
    notes = Column(Text)                        # Admin notes

    def __repr__(self):
        return f"<StockUniverse(ticker='{self.ticker}', tier='{self.market_cap_tier}', cap={self.market_cap})>"


class AnalysisRun(Base):
    """
    Tracks each automatic analysis run.
    Stores metadata about the run for monitoring and debugging.
    """
    __tablename__ = 'analysis_runs'

    id = Column(Integer, primary_key=True)
    run_date = Column(String(20), nullable=False)       # Date of analysis (YYYY-MM-DD)
    run_timestamp = Column(BigInteger, nullable=False)  # Unix timestamp of start time

    # Run statistics
    universe_size = Column(Integer)                     # Total stocks in universe
    stocks_analyzed = Column(Integer)                   # Successfully analyzed
    stocks_with_data = Column(Integer)                  # Had valid data
    stocks_passed_filter = Column(Integer)              # Passed all filters
    stocks_failed = Column(Integer)                     # Failed to analyze

    # Timing
    duration_seconds = Column(Float)                    # Total runtime
    data_collection_seconds = Column(Float)             # Time spent fetching data
    analysis_seconds = Column(Float)                    # Time spent analyzing

    # Configuration snapshot
    settings_snapshot = Column(Text)                    # JSON of settings used

    # Status
    status = Column(String(20))                         # 'running', 'completed', 'failed', 'partial'
    error_message = Column(Text)                        # Error details if failed

    # Results summary
    large_cap_count = Column(Integer)                   # Stocks in large cap tier
    mid_cap_count = Column(Integer)                     # Stocks in mid cap tier
    small_cap_count = Column(Integer)                   # Stocks in small cap tier

    def __repr__(self):
        return f"<AnalysisRun(id={self.id}, date='{self.run_date}', status='{self.status}')>"


class DailyRanking(Base):
    """
    Stores ranked analysis results for each run.
    Links to AnalysisRun and provides rankings within market cap tiers.
    """
    __tablename__ = 'daily_rankings'

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, nullable=False)            # Foreign key to analysis_runs

    # Stock identification
    ticker = Column(String(20), nullable=False)
    rank_date = Column(String(20), nullable=False)      # Date of ranking

    # Market cap categorization
    market_cap_tier = Column(String(20))                # 'large_cap', 'mid_cap', 'small_cap'
    rank_in_tier = Column(Integer)                      # Rank within tier (1 = best)
    rank_overall = Column(Integer)                      # Rank across all stocks

    # Scores
    composite_score = Column(Float)                     # Final composite score (0-100+)
    tech_score = Column(Integer)                        # Technical score (0-100)
    fundamental_score = Column(Float)                   # Fundamental score (0-100)
    signal = Column(String(10))                         # 'BUY', 'HOLD', 'SELL'

    # Price data
    price = Column(Float)
    market_cap = Column(Float)
    volume = Column(Float)

    # Key technical indicators (for quick filtering)
    above_ma200 = Column(Boolean)
    above_ma20 = Column(Boolean)
    rsi_value = Column(Float)
    rsi_above_50 = Column(Boolean)
    macd_value = Column(Float)
    macd_bullish = Column(Boolean)
    near_52w_high = Column(Boolean)
    proximity_to_52w_high = Column(Float)               # 0.0 to 1.0

    # Key fundamental metrics (for quick filtering)
    pe_ratio = Column(Float)
    profit_margin = Column(Float)
    revenue_growth = Column(Float)
    earnings_growth = Column(Float)
    is_profitable = Column(Boolean)

    # Metadata
    data_freshness_hours = Column(Float)                # How old is the data (hours)
    analysis_timestamp = Column(BigInteger)             # When was this analyzed

    __table_args__ = (
        UniqueConstraint('run_id', 'ticker', name='unique_run_ticker'),
    )

    def __repr__(self):
        return f"<DailyRanking(ticker='{self.ticker}', tier='{self.market_cap_tier}', rank={self.rank_in_tier}, score={self.composite_score:.1f})>"


class DataFetchLog(Base):
    """
    Logs all data fetch attempts for monitoring API usage and cache efficiency.
    Helps identify problematic tickers and optimize caching strategy.
    """
    __tablename__ = 'data_fetch_log'

    id = Column(Integer, primary_key=True)
    ticker = Column(String(20), nullable=False)
    fetch_timestamp = Column(BigInteger, nullable=False)
    data_type = Column(String(20))                      # 'price_data', 'fundamentals', 'market_cap'

    # Fetch result
    success = Column(Boolean)
    cache_hit = Column(Boolean)                         # Was data from cache?
    source = Column(String(20))                         # 'cache', 'yahoo', 'alpha_vantage', 'demo'

    # Performance
    fetch_duration_ms = Column(Float)                   # Time taken to fetch

    # Error details
    error_type = Column(String(50))
    error_message = Column(Text)

    # Data quality
    data_age_hours = Column(Float)                      # Age of cached data (if cache hit)
    data_points = Column(Integer)                       # Number of data points returned

    def __repr__(self):
        return f"<DataFetchLog(ticker='{self.ticker}', type='{self.data_type}', success={self.success}, cache_hit={self.cache_hit})>"