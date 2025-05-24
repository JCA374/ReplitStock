from datetime import datetime
import time
import logging

# Import database managers
from data.db_manager import (
    get_db_session, add_to_watchlist as add_to_sqlite_watchlist,
    remove_from_watchlist as remove_from_sqlite_watchlist,
    get_watchlist as get_sqlite_watchlist,
    cache_stock_data as cache_stock_data_sqlite,
    get_cached_stock_data as get_cached_stock_data_sqlite,
    cache_fundamentals as cache_fundamentals_sqlite,
    get_cached_fundamentals as get_cached_fundamentals_sqlite,
    get_all_cached_stocks as get_all_cached_stocks_sqlite,
    get_all_fundamentals as get_all_fundamentals_sqlite,
    initialize_database
)
from data.supabase_client import get_supabase_db

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Make sure SQLite database is initialized properly
initialize_database()

# Use Supabase if it's properly connected
supabase_db = get_supabase_db()
USE_SUPABASE = supabase_db.is_connected()  # Enable Supabase if connected


def add_to_watchlist(ticker, name, exchange="", sector=""):
    """Add a ticker to the watchlist with database prioritization."""
    logger.info(f"Adding {ticker} to watchlist")

    # Try Supabase first if connected
    if USE_SUPABASE:
        try:
            success = supabase_db.add_to_watchlist(
                ticker, name, exchange, sector)
            if success:
                logger.info(f"Added {ticker} to Supabase watchlist")
                return True
        except Exception as e:
            logger.warning(f"Supabase add failed for {ticker}: {e}")

    # Fall back to SQLite
    try:
        success = add_to_sqlite_watchlist(ticker, name, exchange, sector)
        if success:
            logger.info(f"Added {ticker} to SQLite watchlist")
        return success
    except Exception as e:
        logger.error(f"SQLite add failed for {ticker}: {e}")
        return False


def store_analysis_result(ticker, analysis_data):
    """Store analysis result in the database with prioritization."""
    current_timestamp = int(time.time())

    # Format the analysis data for storage
    analysis_record = {
        'ticker': ticker,
        'analysis_date': analysis_data.get('date', datetime.now().strftime("%Y-%m-%d")),
        'price': analysis_data.get('price'),
        'tech_score': analysis_data.get('tech_score'),
        'signal': 'BUY' if analysis_data.get('buy_signal') else 'SELL' if analysis_data.get('sell_signal') else 'HOLD',
        'above_ma40': analysis_data.get('above_ma40'),
        'above_ma4': analysis_data.get('above_ma4'),
        'rsi_value': analysis_data.get('rsi'),
        'rsi_above_50': analysis_data.get('rsi_above_50'),
        'near_52w_high': analysis_data.get('near_52w_high'),
        'pe_ratio': analysis_data.get('pe_ratio'),
        'profit_margin': analysis_data.get('profit_margin'),
        'revenue_growth': analysis_data.get('revenue_growth'),
        'is_profitable': analysis_data.get('is_profitable'),
        'data_source': analysis_data.get('data_source', 'unknown'),
        'last_updated': current_timestamp
    }

    # Try Supabase first if connected
    if USE_SUPABASE:
        try:
            success = supabase_db.store_analysis_result(
                ticker, analysis_record)
            if success:
                logger.info(f"Stored analysis result for {ticker} in Supabase")
                return True
        except Exception as e:
            logger.warning(f"Supabase store failed for {ticker}: {e}")

    # Fall back to SQLite
    try:
        from data.db_models import AnalysisResults
        session = get_db_session()
        try:
            # Check if record exists
            existing = session.query(AnalysisResults).filter(
                AnalysisResults.ticker == ticker,
                AnalysisResults.analysis_date == analysis_record['analysis_date']
            ).first()

            if existing:
                # Update existing record
                for key, value in analysis_record.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
            else:
                # Create new record
                new_record = AnalysisResults(**analysis_record)
                session.add(new_record)

            session.commit()
            logger.info(f"Stored analysis result for {ticker} in SQLite")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"SQLite store failed for {ticker}: {e}")
            return False
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Error storing analysis result for {ticker}: {e}")
        return False


def get_analysis_results(ticker=None, days=30):
    """Get stored analysis results with database prioritization."""
    current_time = int(time.time())
    cutoff_time = current_time - (days * 86400)  # Convert days to seconds

    # Try Supabase first if connected
    if USE_SUPABASE:
        try:
            results = supabase_db.get_analysis_results(ticker, cutoff_time)
            if results:
                logger.info(
                    f"Retrieved analysis results for {ticker} from Supabase")
                return results
        except Exception as e:
            logger.warning(f"Supabase get analysis results failed: {e}")

    # Fall back to SQLite
    try:
        from data.db_models import AnalysisResults
        session = get_db_session()
        try:
            query = session.query(AnalysisResults).filter(
                AnalysisResults.last_updated >= cutoff_time
            )

            if ticker:
                query = query.filter(AnalysisResults.ticker == ticker)

            query = query.order_by(AnalysisResults.last_updated.desc())

            results = query.all()
            logger.info(
                f"Retrieved {len(results)} analysis results from SQLite")
            return [
                {
                    'ticker': r.ticker,
                    'analysis_date': r.analysis_date,
                    'price': r.price,
                    'tech_score': r.tech_score,
                    'signal': r.signal,
                    'above_ma40': r.above_ma40,
                    'above_ma4': r.above_ma4,
                    'rsi_value': r.rsi_value,
                    'rsi_above_50': r.rsi_above_50,
                    'near_52w_high': r.near_52w_high,
                    'pe_ratio': r.pe_ratio,
                    'profit_margin': r.profit_margin,
                    'revenue_growth': r.revenue_growth,
                    'is_profitable': r.is_profitable,
                    'data_source': r.data_source,
                    'last_updated': r.last_updated
                }
                for r in results
            ]
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Error getting analysis results: {e}")
        return []


def remove_from_watchlist(ticker):
    """Remove a ticker from the watchlist with database prioritization."""
    logger.info(f"Removing {ticker} from watchlist")

    # Try Supabase first if connected
    if USE_SUPABASE:
        try:
            supabase_db.remove_from_watchlist(ticker)
            logger.info(f"Removed {ticker} from Supabase watchlist")
        except Exception as e:
            logger.warning(f"Supabase remove failed for {ticker}: {e}")

    # Also remove from SQLite for consistency
    try:
        remove_from_sqlite_watchlist(ticker)
        logger.info(f"Removed {ticker} from SQLite watchlist")
    except Exception as e:
        logger.warning(f"SQLite remove failed for {ticker}: {e}")


def get_watchlist():
    """Get all tickers in the watchlist with database prioritization."""
    # Try Supabase first if connected
    if USE_SUPABASE:
        try:
            watchlist = supabase_db.get_watchlist()
            if watchlist:
                logger.info(
                    f"Retrieved watchlist from Supabase ({len(watchlist)} items)")
                return watchlist
        except Exception as e:
            logger.warning(f"Supabase get watchlist failed: {e}")

    # Fall back to SQLite
    try:
        watchlist = get_sqlite_watchlist()
        logger.info(
            f"Retrieved watchlist from SQLite ({len(watchlist)} items)")
        return watchlist
    except Exception as e:
        logger.error(f"SQLite get watchlist failed: {e}")
        return []


def cache_stock_data(ticker, timeframe, period, data, source):
    """Cache stock data to reduce API calls with database prioritization."""
    logger.info(f"Caching stock data for {ticker} from {source}")

    # Try Supabase first if connected
    if USE_SUPABASE:
        try:
            supabase_db.cache_stock_data(
                ticker, timeframe, period, data, source)
            logger.info(f"Cached {ticker} data in Supabase")
        except Exception as e:
            logger.warning(f"Supabase cache failed for {ticker}: {e}")

    # Also cache in SQLite for local performance
    try:
        cache_stock_data_sqlite(ticker, timeframe, period, data, source)
        logger.info(f"Cached {ticker} data in SQLite")
    except Exception as e:
        logger.warning(f"SQLite cache failed for {ticker}: {e}")


def get_cached_stock_data(ticker, timeframe, period, source):
    """Retrieve cached stock data with database prioritization."""
    # Try Supabase first if connected
    if USE_SUPABASE:
        try:
            data = supabase_db.get_cached_stock_data(
                ticker, timeframe, period, source)
            if data is not None and not data.empty:
                logger.info(
                    f"Retrieved cached data for {ticker} from Supabase")
                return data
        except Exception as e:
            logger.warning(
                f"Supabase get cached data failed for {ticker}: {e}")

    # Fall back to SQLite
    try:
        data = get_cached_stock_data_sqlite(ticker, timeframe, period, source)
        if data is not None and not data.empty:
            logger.info(f"Retrieved cached data for {ticker} from SQLite")
        return data
    except Exception as e:
        logger.warning(f"SQLite get cached data failed for {ticker}: {e}")
        return None


def cache_fundamentals(ticker, fundamentals_data):
    """Cache fundamental data with database prioritization."""
    logger.info(f"Caching fundamentals for {ticker}")

    # Try Supabase first if connected
    if USE_SUPABASE:
        try:
            supabase_db.cache_fundamentals(ticker, fundamentals_data)
            logger.info(f"Cached fundamentals for {ticker} in Supabase")
        except Exception as e:
            logger.warning(
                f"Supabase cache fundamentals failed for {ticker}: {e}")

    # Also cache in SQLite for local performance
    try:
        cache_fundamentals_sqlite(ticker, fundamentals_data)
        logger.info(f"Cached fundamentals for {ticker} in SQLite")
    except Exception as e:
        logger.warning(f"SQLite cache fundamentals failed for {ticker}: {e}")


def get_cached_fundamentals(ticker):
    """Retrieve cached fundamental data with database prioritization."""
    # Try Supabase first if connected
    if USE_SUPABASE:
        try:
            data = supabase_db.get_cached_fundamentals(ticker)
            if data is not None:
                logger.info(
                    f"Retrieved cached fundamentals for {ticker} from Supabase")
                return data
        except Exception as e:
            logger.warning(
                f"Supabase get cached fundamentals failed for {ticker}: {e}")

    # Fall back to SQLite
    try:
        data = get_cached_fundamentals_sqlite(ticker)
        if data is not None:
            logger.info(
                f"Retrieved cached fundamentals for {ticker} from SQLite")
        return data
    except Exception as e:
        logger.warning(
            f"SQLite get cached fundamentals failed for {ticker}: {e}")
        return None


def get_all_cached_stocks():
    """Get all unique stock tickers in the cache with database prioritization."""
    all_stocks = set()

    # Try Supabase first if connected
    if USE_SUPABASE:
        try:
            stocks = supabase_db.get_all_cached_stocks()
            if stocks:
                all_stocks.update(stocks)
                logger.info(
                    f"Retrieved {len(stocks)} stocks from Supabase cache")
        except Exception as e:
            logger.warning(f"Supabase get all cached stocks failed: {e}")

    # Also get from SQLite
    try:
        stocks = get_all_cached_stocks_sqlite()
        if stocks:
            all_stocks.update(stocks)
            logger.info(f"Retrieved {len(stocks)} stocks from SQLite cache")
    except Exception as e:
        logger.warning(f"SQLite get all cached stocks failed: {e}")

    result = list(all_stocks)
    logger.info(f"Total unique stocks in cache: {len(result)}")
    return result


def get_all_fundamentals():
    """Get fundamental data for all stocks with database prioritization."""
    all_fundamentals = {}

    # Try SQLite first for fundamentals (often more complete)
    try:
        sqlite_fundamentals = get_all_fundamentals_sqlite()
        for f in sqlite_fundamentals:
            ticker = f.get('ticker')
            if ticker:
                all_fundamentals[ticker] = f
        logger.info(
            f"Retrieved {len(sqlite_fundamentals)} fundamentals from SQLite")
    except Exception as e:
        logger.warning(f"SQLite get all fundamentals failed: {e}")

    # Try Supabase if connected (will overwrite SQLite data if available)
    if USE_SUPABASE:
        try:
            supabase_fundamentals = supabase_db.get_all_fundamentals()
            for f in supabase_fundamentals:
                ticker = f.get('ticker')
                if ticker:
                    all_fundamentals[ticker] = f
            logger.info(
                f"Retrieved {len(supabase_fundamentals)} fundamentals from Supabase")
        except Exception as e:
            logger.warning(f"Supabase get all fundamentals failed: {e}")

    result = list(all_fundamentals.values())
    logger.info(f"Total unique fundamentals: {len(result)}")
    return result


def create_supabase_tables():
    """Initialize the Supabase tables."""
    if USE_SUPABASE:
        try:
            # This will check and inform about any missing tables
            supabase_db._create_tables_if_not_exist()
            logger.info("Supabase tables initialized")
        except Exception as e:
            logger.error(f"Failed to create Supabase tables: {e}")


def get_database_status():
    """Get the status of both database connections."""
    status = {
        'supabase_connected': False,
        'sqlite_available': False,
        'primary_db': 'sqlite'
    }

    # Check Supabase
    if USE_SUPABASE:
        try:
            status['supabase_connected'] = supabase_db.is_connected()
            if status['supabase_connected']:
                status['primary_db'] = 'supabase'
        except:
            status['supabase_connected'] = False

    # Check SQLite
    try:
        session = get_db_session()
        session.close()
        status['sqlite_available'] = True
    except:
        status['sqlite_available'] = False

    return status

# For debugging and monitoring


def log_database_stats():
    """Log current database statistics."""
    try:
        watchlist_count = len(get_watchlist())
        cached_stocks_count = len(get_all_cached_stocks())
        fundamentals_count = len(get_all_fundamentals())

        logger.info(
            f"Database stats - Watchlist: {watchlist_count}, Cached stocks: {cached_stocks_count}, Fundamentals: {fundamentals_count}")

        status = get_database_status()
        logger.info(f"Database status: {status}")

    except Exception as e:
        logger.error(f"Error logging database stats: {e}")
