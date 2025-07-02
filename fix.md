I'll search for the technical_spec.md file to understand the project overview and plan, then review the batch scanning logic.Now let me search for the batch scanning logic to review it:Let me continue searching for more batch scanning logic:Based on my review of the technical_spec.md and the batch scanning logic, I'll provide a thorough analysis and recommendations for improvements.

## Current State Analysis

The batch scanning logic is **well-implemented** and follows best practices for both technical and fundamental analysis. Here's what's currently working well:

### ✅ Strong Points:

1. **Efficient Data Flow**:
   - Database-first approach (SQLite → Supabase → APIs)
   - Bulk loading of all data in 1-2 queries
   - Proper caching with TTL management

2. **Performance Optimizations**:
   - Parallel processing with ThreadPoolExecutor
   - Batch API calls with proper rate limiting
   - Memory-efficient processing of large datasets

3. **Technical Analysis** (well-implemented):
   - RSI, MACD, Moving Averages
   - 52-week high/low detection
   - Volume analysis
   - Price pattern recognition

4. **Fundamental Analysis** (solid approach):
   - P/E ratio validation
   - Profit margin analysis
   - Revenue growth tracking
   - Profitability checks

## Code to Remove/Replace

Based on the technical spec, here are the specific changes needed:

### 1. **Update Import Statements** (CRITICAL)

**Remove this code** from `app.py`:
```python
# OLD - REMOVE THIS
from tabs.strategy import ValueMomentumStrategy
from tabs.enhanced_scanner_tab import render_enhanced_scanner_ui
```

**Replace with**:
```python
# NEW - ADD THIS
from analysis.strategy import ValueMomentumStrategy
from ui.enhanced_scanner import render_enhanced_scanner_ui
```

### 2. **Update any other files with old imports**

Check these files and update imports if they exist:
- `ui/batch_analysis.py`
- `analysis/bulk_scanner.py`
- Any other files importing from `tabs/`

## Improvements for Batch Scanning Logic

While the current implementation is good, here are some improvements that could enhance it further:

### 1. **Enhanced Technical Indicators**

**Add to** `analysis/technical.py`:
```python
def calculate_bollinger_bands(prices, window=20, num_std=2):
    """Calculate Bollinger Bands for volatility analysis"""
    sma = prices.rolling(window=window).mean()
    std = prices.rolling(window=window).std()
    upper_band = sma + (std * num_std)
    lower_band = sma - (std * num_std)
    return upper_band, sma, lower_band

def calculate_volume_profile(volume, prices, bins=10):
    """Calculate volume profile for support/resistance levels"""
    price_bins = pd.cut(prices, bins=bins)
    volume_profile = volume.groupby(price_bins).sum()
    return volume_profile
```

### 2. **Improved Fundamental Scoring**

**Add to** `analysis/strategy.py` in the `_calculate_fundamental_indicators` method:
```python
# Add these additional checks for better fundamental analysis
def _calculate_fundamental_indicators(self, fundamentals):
    """Enhanced fundamental analysis with additional metrics"""
    results = {
        "pe_ratio": None,
        "profit_margin": None, 
        "revenue_growth": None,
        "is_profitable": False,
        "reasonable_pe": True,
        "fundamental_check": False,
        # NEW METRICS
        "debt_to_equity": None,
        "return_on_equity": None,
        "price_to_book": None,
        "fundamental_score": 0
    }
    
    try:
        # Existing code...
        
        # NEW: Add debt analysis
        debt_to_equity = fundamentals.get('debt_to_equity')
        if debt_to_equity is not None:
            results["debt_to_equity"] = debt_to_equity
            # Healthy debt levels (< 1.5)
            if debt_to_equity < 1.5:
                results["fundamental_score"] += 20
        
        # NEW: Add ROE analysis
        roe = fundamentals.get('return_on_equity')
        if roe is not None:
            results["return_on_equity"] = roe
            # Good ROE (> 15%)
            if roe > 0.15:
                results["fundamental_score"] += 20
        
        # NEW: Add P/B analysis
        pb_ratio = fundamentals.get('price_to_book')
        if pb_ratio is not None:
            results["price_to_book"] = pb_ratio
            # Value play (P/B < 3)
            if pb_ratio < 3 and pb_ratio > 0:
                results["fundamental_score"] += 10
        
        # Existing scoring...
        if results["is_profitable"]:
            results["fundamental_score"] += 30
        if results["reasonable_pe"]:
            results["fundamental_score"] += 20
            
        return results
```

### 3. **Batch Processing Optimization**

**Update** `analysis/bulk_scanner.py` for better error handling:
```python
def _analyze_all_stocks(self, all_stock_data, progress_callback=None):
    """Enhanced batch processing with retry logic"""
    results = []
    tickers = list(all_stock_data.keys())
    
    if not tickers:
        return results
    
    # Initialize fetcher with retry capability
    from data.stock_data import StockDataFetcher
    fresh_fetcher = StockDataFetcher()
    
    # Track failed tickers for retry
    failed_tickers = []
    
    # First pass - process all tickers
    for ticker in tickers:
        try:
            # Existing processing logic...
            result = self._process_single_stock(ticker, all_stock_data, fresh_fetcher)
            results.append(result)
        except Exception as e:
            logger.warning(f"First pass failed for {ticker}: {e}")
            failed_tickers.append(ticker)
    
    # Retry failed tickers once
    if failed_tickers:
        logger.info(f"Retrying {len(failed_tickers)} failed tickers...")
        for ticker in failed_tickers:
            try:
                # Use Yahoo as fallback for retry
                result = self._process_single_stock(ticker, all_stock_data, fresh_fetcher, use_yahoo=True)
                results.append(result)
            except Exception as e:
                logger.error(f"Retry also failed for {ticker}: {e}")
                # Add minimal result to avoid missing stocks
                results.append(self._create_error_result(ticker, str(e)))
    
    return results
```

### 4. **Performance Monitoring**

**Add to** `analysis/bulk_scanner.py`:
```python
class PerformanceMonitor:
    """Track and log performance metrics"""
    
    def __init__(self):
        self.metrics = {
            'api_calls': 0,
            'cache_hits': 0,
            'processing_times': [],
            'error_count': 0
        }
    
    def log_api_call(self, source):
        self.metrics['api_calls'] += 1
        logger.info(f"API call #{self.metrics['api_calls']} to {source}")
    
    def log_cache_hit(self):
        self.metrics['cache_hits'] += 1
    
    def get_summary(self):
        """Get performance summary"""
        total_requests = self.metrics['api_calls'] + self.metrics['cache_hits']
        cache_rate = (self.metrics['cache_hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'cache_hit_rate': f"{cache_rate:.1f}%",
            'total_api_calls': self.metrics['api_calls'],
            'error_rate': f"{(self.metrics['error_count'] / total_requests * 100):.1f}%" if total_requests > 0 else "0%"
        }
```

## Summary

The current batch scanning implementation is **good enough** for production use. It follows best practices for:
- Database-first data access
- Efficient bulk operations
- Proper error handling
- Rate limit management

The suggested improvements are **optional enhancements** that would:
1. Add more sophisticated technical indicators
2. Provide richer fundamental analysis
3. Improve error recovery
4. Add performance monitoring

**Immediate action required**: Only update the import statements as specified in the technical spec.

The core logic is solid and performant. Focus on using the existing system effectively rather than major rewrites.