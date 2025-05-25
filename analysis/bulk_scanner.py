"""
High-performance bulk scanner that processes all database data first, then makes batch API calls only for missing data.
"""
import logging
import time
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Callable, Tuple, Any

# Import database connections
from data.db_manager import get_all_fundamentals, get_watchlist, get_cached_stock_data, get_all_cached_stocks
from data.db_integration import cache_stock_data, cache_fundamentals
from analysis.technical import calculate_all_indicators, generate_technical_signals
from analysis.fundamental import analyze_fundamentals
from data.stock_data import StockDataFetcher
from config import BULK_SCANNER_CONFIG, get_bulk_scanner_config

# Import performance monitoring
try:
    from utils.performance_monitor import ScanPerformanceMonitor
    PERF_MONITOR_AVAILABLE = True
except ImportError:
    PERF_MONITOR_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('bulk_scanner')


class BulkDataLoader:
    """
    Efficiently loads data for multiple stocks in bulk operations
    """

    def __init__(self, use_supabase=True, use_sqlite=True):
        self.use_supabase = use_supabase
        self.use_sqlite = use_sqlite
        
        # Cache storage
        self.fundamentals_cache = {}
        self.stock_data_cache = {}
        self.info_cache = {}
        
        # Performance monitoring
        self.perf_monitor = ScanPerformanceMonitor() if PERF_MONITOR_AVAILABLE else None
        
        # API data fetcher
        self.data_fetcher = StockDataFetcher()

    def load_all_database_data(self, tickers: List[str]) -> Tuple[Dict, Dict]:
        """
        Load all available data from databases in bulk operations
        
        Args:
            tickers: List of ticker symbols to load data for
            
        Returns:
            Tuple containing (fundamentals_data, stock_price_data)
        """
        if self.perf_monitor:
            self.perf_monitor.start_scan()
            
        logger.info(f"Loading bulk data for {len(tickers)} stocks from databases")
        
        # Initialize cache dictionaries
        fundamentals_data = {}
        stock_price_data = {}
        
        # Step 1: Load all fundamentals in one query from SQLite
        if self.use_sqlite:
            with self._timing("sqlite_fundamentals_load"):
                sqlite_fundamentals = get_all_fundamentals()
                for f in sqlite_fundamentals:
                    ticker = f.get('ticker')
                    if ticker and ticker in tickers:
                        fundamentals_data[ticker] = f
                        
                logger.info(f"Loaded {len(fundamentals_data)} fundamental records from SQLite")
                
        # Step 2: Load all fundamentals from Supabase if available
        if self.use_supabase:
            try:
                with self._timing("supabase_fundamentals_load"):
                    from data.supabase_client import get_supabase_db
                    supabase_db = get_supabase_db()
                    
                    if supabase_db.is_connected():
                        supabase_fundamentals = supabase_db.get_all_fundamentals()
                        for f in supabase_fundamentals:
                            ticker = f.get('ticker')
                            if ticker and ticker in tickers and ticker not in fundamentals_data:
                                fundamentals_data[ticker] = f
                        
                        logger.info(f"Loaded additional {len(supabase_fundamentals)} fundamental records from Supabase")
            except Exception as e:
                logger.error(f"Error loading Supabase fundamentals: {e}")
        
        # Step 3: Load stock price data from SQLite
        if self.use_sqlite:
            with self._timing("sqlite_price_load"):
                # For each ticker, try to get cached data
                for ticker in tickers:
                    stock_data = get_cached_stock_data(ticker, '1d', '1y', 'yahoo')
                    if stock_data is None or stock_data.empty:
                        stock_data = get_cached_stock_data(ticker, '1d', '1y', 'alphavantage')
                    
                    if stock_data is not None and not stock_data.empty:
                        stock_price_data[ticker] = stock_data
                
                logger.info(f"Loaded {len(stock_price_data)} stock price records from SQLite")
                
        # Step 4: Load stock price data from Supabase if available
        if self.use_supabase:
            try:
                with self._timing("supabase_price_load"):
                    from data.supabase_client import get_supabase_db
                    supabase_db = get_supabase_db()
                    
                    if supabase_db.is_connected():
                        # Only fetch data for tickers not already loaded from SQLite
                        missing_tickers = [t for t in tickers if t not in stock_price_data]
                        
                        for ticker in missing_tickers:
                            stock_data = supabase_db.get_cached_stock_data(ticker, '1d', '1y', 'yahoo')
                            if stock_data is None or stock_data.empty:
                                stock_data = supabase_db.get_cached_stock_data(ticker, '1d', '1y', 'alphavantage')
                            
                            if stock_data is not None and not stock_data.empty:
                                stock_price_data[ticker] = stock_data
                        
                        logger.info(f"Loaded additional stock price data from Supabase, now have {len(stock_price_data)} total")
            except Exception as e:
                logger.error(f"Error loading Supabase stock data: {e}")
        
        # Store in cache
        self.fundamentals_cache = fundamentals_data
        self.stock_data_cache = stock_price_data
        
        # Return the loaded data
        return fundamentals_data, stock_price_data
    
    def fetch_missing_data(self, tickers: List[str], progress_callback=None) -> Tuple[Dict, Dict]:
        """
        Fetch missing data for tickers not found in database
        
        This makes optimized batch API calls for any missing data
        
        Args:
            tickers: List of ticker symbols to check
            progress_callback: Optional callback for progress updates
            
        Returns:
            Tuple containing (new_fundamentals, new_stock_data)
        """
        # Find which tickers are missing data
        missing_fundamentals = [t for t in tickers if t not in self.fundamentals_cache]
        missing_stock_data = [t for t in tickers if t not in self.stock_data_cache]
        
        # Skip if nothing is missing
        if not missing_fundamentals and not missing_stock_data:
            logger.info("No missing data to fetch from APIs")
            return {}, {}
        
        logger.info(f"Fetching missing data for: {len(missing_fundamentals)} fundamentals, {len(missing_stock_data)} price data")
        
        # Get configuration for API fetching
        config = get_bulk_scanner_config()
        max_workers = config['max_api_workers']
        batch_size = config['api_batch_size']
        batch_delay = config['api_batch_delay']
        request_delay = config['single_request_delay']
        
        # New data containers
        new_fundamentals = {}
        new_stock_data = {}
        
        # Track progress
        total_to_fetch = len(missing_fundamentals) + len(missing_stock_data)
        fetched_count = 0
        
        # Step 1: Fetch missing stock data in batches
        if missing_stock_data:
            with self._timing("api_stock_data_fetch"):
                # Process in small batches to avoid rate limits
                batches = [missing_stock_data[i:i + batch_size] for i in range(0, len(missing_stock_data), batch_size)]
                
                for batch_idx, batch in enumerate(batches):
                    # Update progress
                    if progress_callback:
                        progress = fetched_count / total_to_fetch
                        progress_callback(progress, f"Fetching price data batch {batch_idx+1}/{len(batches)}...")
                    
                    # Use thread pool for parallel fetching within batch
                    with ThreadPoolExecutor(max_workers=max_workers) as executor:
                        # Submit all jobs
                        future_to_ticker = {
                            executor.submit(self._fetch_stock_data, ticker): ticker
                            for ticker in batch
                        }
                        
                        # Collect results as they complete
                        for future in as_completed(future_to_ticker):
                            ticker = future_to_ticker[future]
                            try:
                                stock_data = future.result()
                                if stock_data is not None and not stock_data.empty:
                                    new_stock_data[ticker] = stock_data
                                    self.stock_data_cache[ticker] = stock_data
                                    
                                    # Cache the data we just fetched
                                    if config['cache_fetched_data']:
                                        cache_stock_data(ticker, stock_data, '1d', '1y', 'yahoo')
                            except Exception as e:
                                logger.error(f"Error fetching stock data for {ticker}: {e}")
                            
                            fetched_count += 1
                    
                    # Delay between batches to avoid rate limits
                    if batch_idx < len(batches) - 1:
                        time.sleep(batch_delay)
        
        # Step 2: Fetch missing fundamentals in batches
        if missing_fundamentals:
            with self._timing("api_fundamentals_fetch"):
                # Process in small batches to avoid rate limits
                batches = [missing_fundamentals[i:i + batch_size] for i in range(0, len(missing_fundamentals), batch_size)]
                
                for batch_idx, batch in enumerate(batches):
                    # Update progress
                    if progress_callback:
                        progress = fetched_count / total_to_fetch
                        progress_callback(progress, f"Fetching fundamental data batch {batch_idx+1}/{len(batches)}...")
                    
                    # Use thread pool for parallel fetching within batch
                    with ThreadPoolExecutor(max_workers=max_workers) as executor:
                        # Submit all jobs
                        future_to_ticker = {
                            executor.submit(self._fetch_fundamentals, ticker): ticker
                            for ticker in batch
                        }
                        
                        # Collect results as they complete
                        for future in as_completed(future_to_ticker):
                            ticker = future_to_ticker[future]
                            try:
                                fundamentals = future.result()
                                if fundamentals:
                                    new_fundamentals[ticker] = fundamentals
                                    self.fundamentals_cache[ticker] = fundamentals
                                    
                                    # Cache the data we just fetched
                                    if config['cache_fetched_data']:
                                        cache_fundamentals(ticker, fundamentals)
                            except Exception as e:
                                logger.error(f"Error fetching fundamentals for {ticker}: {e}")
                            
                            fetched_count += 1
                    
                    # Delay between batches to avoid rate limits
                    if batch_idx < len(batches) - 1:
                        time.sleep(batch_delay)
        
        # Log results
        logger.info(f"API fetching complete: {len(new_stock_data)} price data, {len(new_fundamentals)} fundamentals")
        
        return new_fundamentals, new_stock_data
    
    def _fetch_stock_data(self, ticker: str) -> Optional[pd.DataFrame]:
        """Helper to fetch stock data for a single ticker"""
        try:
            # Short delay to avoid hitting rate limits
            time.sleep(get_bulk_scanner_config()['single_request_delay'])
            
            # Try Alpha Vantage first (if it's our preferred source)
            stock_data = self.data_fetcher.get_stock_data(ticker, '1d', '1y', attempt_fallback=True)
            return stock_data
        except Exception as e:
            logger.warning(f"Failed to fetch stock data for {ticker}: {e}")
            return None
    
    def _fetch_fundamentals(self, ticker: str) -> Optional[Dict]:
        """Helper to fetch fundamentals for a single ticker"""
        try:
            # Short delay to avoid hitting rate limits
            time.sleep(get_bulk_scanner_config()['single_request_delay'])
            
            fundamentals = self.data_fetcher.get_fundamentals(ticker)
            return fundamentals
        except Exception as e:
            logger.warning(f"Failed to fetch fundamentals for {ticker}: {e}")
            return None
    
    def get_stock_data(self, ticker: str) -> Optional[pd.DataFrame]:
        """Get stock data for a ticker from the cache"""
        return self.stock_data_cache.get(ticker)
    
    def get_fundamentals(self, ticker: str) -> Optional[Dict]:
        """Get fundamentals for a ticker from the cache"""
        return self.fundamentals_cache.get(ticker)
    
    def get_data_coverage_stats(self) -> Dict[str, Any]:
        """Get statistics about data coverage"""
        total_tickers = len(set(list(self.fundamentals_cache.keys()) + list(self.stock_data_cache.keys())))
        
        return {
            'total_unique_tickers': total_tickers,
            'fundamentals_count': len(self.fundamentals_cache),
            'stock_data_count': len(self.stock_data_cache),
            'complete_data_count': len([t for t in self.fundamentals_cache.keys() if t in self.stock_data_cache]),
            'fundamentals_only_count': len([t for t in self.fundamentals_cache.keys() if t not in self.stock_data_cache]),
            'stock_data_only_count': len([t for t in self.stock_data_cache.keys() if t not in self.fundamentals_cache])
        }
    
    def _timing(self, operation_name: str):
        """Context manager for timing operations"""
        if not self.perf_monitor:
            # No-op context manager if no performance monitor
            class NoOpContext:
                def __enter__(self): return self
                def __exit__(self, *args): pass
            return NoOpContext()
        
        return self.perf_monitor.time_operation(operation_name)


class BulkStockAnalyzer:
    """
    Analyzes stocks in bulk using preloaded data
    """
    
    def __init__(self, data_loader: BulkDataLoader):
        self.data_loader = data_loader
        
        # Performance monitoring
        self.perf_monitor = ScanPerformanceMonitor() if PERF_MONITOR_AVAILABLE else None
    
    def analyze_stocks_in_bulk(self, tickers: List[str], progress_callback=None) -> List[Dict]:
        """
        Analyze multiple stocks in parallel using preloaded data
        
        Args:
            tickers: List of ticker symbols to analyze
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of analysis results for each stock
        """
        if not tickers:
            return []
        
        if self.perf_monitor:
            self.perf_monitor.start_scan()
        
        logger.info(f"Starting bulk analysis of {len(tickers)} stocks")
        
        # Get configuration
        config = get_bulk_scanner_config()
        max_workers = config['max_analysis_workers']
        batch_size = config['analysis_batch_size']
        
        # Results container
        results = []
        
        # Process in batches for better memory management and progress tracking
        batches = [tickers[i:i + batch_size] for i in range(0, len(tickers), batch_size)]
        
        for batch_idx, batch_tickers in enumerate(batches):
            # Update progress
            if progress_callback:
                progress = batch_idx / len(batches)
                progress_callback(progress, f"Analyzing batch {batch_idx+1}/{len(batches)}...")
            
            # Process this batch in parallel
            batch_results = self._process_batch_parallel(batch_tickers, max_workers)
            results.extend(batch_results)
        
        # Sort by tech score
        results.sort(key=lambda x: x.get('tech_score', 0), reverse=True)
        
        logger.info(f"Bulk analysis complete for {len(tickers)} stocks")
        
        # Final progress update
        if progress_callback:
            progress_callback(1.0, f"Analysis complete!")
        
        return results
    
    def _process_batch_parallel(self, batch_tickers: List[str], max_workers: int) -> List[Dict]:
        """Process a batch of tickers in parallel"""
        results = []
        
        with self._timing("parallel_analysis"):
            # Use ThreadPoolExecutor for parallelization
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all jobs
                future_to_ticker = {
                    executor.submit(self._analyze_single_stock, ticker): ticker
                    for ticker in batch_tickers
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_ticker):
                    ticker = future_to_ticker[future]
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        logger.error(f"Error analyzing {ticker}: {e}")
                        results.append({
                            "ticker": ticker,
                            "error": str(e),
                            "error_message": f"Analysis failed: {str(e)}"
                        })
        
        return results
    
    def _analyze_single_stock(self, ticker: str) -> Dict:
        """Analyze a single stock using preloaded data"""
        try:
            with self._timing(f"analyze_{ticker}"):
                # Get preloaded data
                stock_data = self.data_loader.get_stock_data(ticker)
                fundamentals = self.data_loader.get_fundamentals(ticker)
                
                # Return error if no stock data available
                if stock_data is None or stock_data.empty:
                    return {
                        "ticker": ticker,
                        "error": "No stock data available",
                        "error_message": f"No data found for {ticker}"
                    }
                
                # Calculate technical indicators
                indicators = calculate_all_indicators(stock_data)
                signals = generate_technical_signals(indicators)
                
                # Analyze fundamentals
                fundamental_analysis = analyze_fundamentals(fundamentals or {})
                
                # Calculate current price
                current_price = stock_data['close'].iloc[-1] if not stock_data.empty else 0
                
                # Get technical score
                tech_score = signals.get('tech_score', 0)
                
                # Value & Momentum Strategy logic
                fundamental_pass = fundamental_analysis['overall'].get('value_momentum_pass', False)
                
                if tech_score >= 70 and fundamental_pass:
                    value_momentum_signal = "BUY"
                elif tech_score < 40 or not signals.get('above_ma40', False):
                    value_momentum_signal = "SELL"
                else:
                    value_momentum_signal = "HOLD"
                
                # Create comprehensive result
                result = {
                    'ticker': ticker,
                    'last_price': current_price,
                    'pe_ratio': fundamentals.get('pe_ratio') if fundamentals else None,
                    'profit_margin': fundamentals.get('profit_margin') if fundamentals else None,
                    'revenue_growth': fundamentals.get('revenue_growth') if fundamentals else None,
                    'tech_score': tech_score,
                    'above_ma40': signals.get('above_ma40', False),
                    'above_ma4': signals.get('above_ma4', False),
                    'rsi_above_50': signals.get('rsi_above_50', False),
                    'near_52w_high': signals.get('near_52w_high', False),
                    'is_profitable': fundamental_analysis['overall'].get('is_profitable', False),
                    'reasonable_pe': fundamental_analysis['overall'].get('reasonable_pe', True),
                    'fundamental_pass': fundamental_pass,
                    'value_momentum_signal': value_momentum_signal,
                    'data_source': "database"  # Since we're using preloaded data
                }
                
                return result
        except Exception as e:
            logger.error(f"Error analyzing {ticker}: {e}")
            return {
                "ticker": ticker,
                "error": str(e),
                "error_message": f"Analysis failed: {str(e)}"
            }
    
    def _timing(self, operation_name: str):
        """Context manager for timing operations"""
        if not self.perf_monitor:
            # No-op context manager if no performance monitor
            class NoOpContext:
                def __enter__(self): return self
                def __exit__(self, *args): pass
            return NoOpContext()
        
        return self.perf_monitor.time_operation(operation_name)


def optimized_bulk_scan(target_tickers: List[str], fetch_missing: bool = True, 
                       max_api_workers: int = 3, progress_callback: Optional[Callable] = None,
                       stream_results: bool = False, store_metrics: bool = True) -> List[Dict]:
    """
    Run an optimized bulk scan of stocks
    
    This function:
    1. Loads all available data from databases in bulk operations
    2. Optionally fetches missing data from APIs in batches
    3. Analyzes stocks in parallel using the preloaded data
    
    Args:
        target_tickers: List of ticker symbols to analyze
        fetch_missing: Whether to fetch missing data from APIs
        max_api_workers: Number of workers for API fetching
        progress_callback: Optional callback for progress updates
        stream_results: If True, yields results as they become available
                       instead of returning all at once (better memory usage)
        store_metrics: Whether to store performance metrics in session state
                      (for Streamlit UI integration)
        
    Returns:
        List of analysis results for each stock or a generator if stream_results=True
    """
    # Override config with passed parameters
    config = get_bulk_scanner_config()
    config['max_api_workers'] = max_api_workers
    
    # Get streaming preference from config if not explicitly set
    if stream_results is None:
        stream_results = config.get('enable_result_streaming', False)
    
    # Check if we can process all these stocks at once or need to batch them
    max_stocks = config.get('max_stocks_in_memory', 1000)
    if len(target_tickers) > max_stocks and not stream_results:
        logger.warning(f"Requested analysis of {len(target_tickers)} stocks exceeds max_stocks_in_memory "
                      f"({max_stocks}). Switching to streaming mode.")
        stream_results = True
    
    # Initialize the data loader with performance monitoring
    data_loader = BulkDataLoader(use_supabase=True, use_sqlite=True)
    
    # Create performance monitors
    data_loader_monitor = None
    analyzer_monitor = None
    
    if PERF_MONITOR_AVAILABLE:
        data_loader_monitor = ScanPerformanceMonitor()
        analyzer_monitor = ScanPerformanceMonitor()
        
        # Replace the data loader's monitor
        data_loader.perf_monitor = data_loader_monitor
        
        # Store in session state for UI access if requested
        if store_metrics:
            try:
                import streamlit as st
                st.session_state.scan_performance_monitor = data_loader_monitor
            except ImportError:
                # Not running in Streamlit
                pass
    
    # Start progress tracking
    if progress_callback:
        progress_callback(0.05, "Loading data from databases...")
    
    # Step 1: Load all data from databases in bulk
    data_loader.load_all_database_data(target_tickers)
    
    # Step 2: Fetch missing data if requested
    if fetch_missing:
        if progress_callback:
            progress_callback(0.2, "Fetching missing data from APIs...")
        
        data_loader.fetch_missing_data(target_tickers, progress_callback)
    
    # Log data coverage statistics
    coverage = data_loader.get_data_coverage_stats()
    logger.info(f"Data coverage: {coverage['complete_data_count']}/{len(target_tickers)} stocks have complete data")
    
    # Step 3: Analyze stocks in parallel using preloaded data
    if progress_callback:
        progress_callback(0.6, "Analyzing stocks in parallel...")
    
    # Create analyzer with performance monitoring
    analyzer = BulkStockAnalyzer(data_loader)
    
    # Set the analyzer's performance monitor if available
    if analyzer_monitor:
        analyzer.perf_monitor = analyzer_monitor
    
    # Choose between streaming or bulk processing based on parameter
    if stream_results:
        # Break tickers into smaller batches for better memory management
        batch_size = config.get('analysis_batch_size', 20)
        batches = [target_tickers[i:i + batch_size] for i in range(0, len(target_tickers), batch_size)]
        
        all_results = []
        batch_count = len(batches)
        
        # Process each batch and yield results
        for i, batch in enumerate(batches):
            if progress_callback:
                batch_progress = 0.6 + (0.4 * (i / batch_count))
                progress_callback(batch_progress, f"Processing batch {i+1}/{batch_count}...")
            
            batch_results = analyzer.analyze_stocks_in_bulk(batch, progress_callback)
            all_results.extend(batch_results)
            
            # Sort intermediary results by tech score
            all_results.sort(key=lambda x: x.get('tech_score', 0), reverse=True)
        
        # Return the sorted combined results
        if data_loader_monitor and analyzer_monitor and PERF_MONITOR_AVAILABLE:
            # Calculate combined stats for performance metrics
            data_loader_monitor.print_summary()
            analyzer_monitor.print_summary()
            
        return all_results
    else:
        # Standard bulk processing (all at once)
        results = analyzer.analyze_stocks_in_bulk(target_tickers, progress_callback)
        
        if data_loader_monitor and analyzer_monitor and PERF_MONITOR_AVAILABLE:
            # Calculate combined stats for performance metrics
            data_loader_monitor.print_summary()
            analyzer_monitor.print_summary()
            
            # Combine metrics for API stats if available
            try:
                combined_metrics = data_loader_monitor.get_performance_summary()
                analysis_metrics = analyzer_monitor.get_performance_summary()
                
                # Add analysis timings to the combined metrics
                if 'operation_timings' in combined_metrics and 'operation_timings' in analysis_metrics:
                    combined_metrics['operation_timings'].update(analysis_metrics['operation_timings'])
                
                # Update the session state monitor with combined metrics
                if store_metrics:
                    try:
                        import streamlit as st
                        if 'scan_performance_monitor' in st.session_state:
                            # Get the monitor from session state
                            monitor = st.session_state.scan_performance_monitor
                            # Update its metrics
                            monitor.timings.update(combined_metrics.get('operation_timings', {}))
                    except:
                        pass
            except Exception as e:
                logger.warning(f"Could not combine performance metrics: {e}")
        
        return results