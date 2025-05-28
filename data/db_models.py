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