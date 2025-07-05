# Stock Analysis App - Developer Reference

## ✅ **File Structure Cleaned Up (2025-01-20)**
- `tabs/strategy.py` → `analysis/strategy.py`
- `tabs/enhanced_scanner_tab.py` → `ui/enhanced_scanner.py`

**⚠️ Update imports in `app.py`:**
```python
# OLD
from tabs.strategy import ValueMomentumStrategy
from tabs.enhanced_scanner_tab import render_enhanced_scanner_ui

# NEW  
from analysis.strategy import ValueMomentumStrategy
from ui.enhanced_scanner import render_enhanced_scanner_ui
```

**⚠️ Also check these files for import updates:**
- `ui/batch_analysis.py` (if it imports strategy)
- `analysis/bulk_scanner.py` (if it imports strategy)
- Any other files importing from old `tabs/` location

## 🎯 Core Data Flow (NEVER BREAK THIS)

```python
# ALWAYS follow this order:
1. SQLite Cache (fastest)
2. Supabase Cache (if connected) 
3. Alpha Vantage API (preferred)
4. Yahoo Finance API (fallback)
5. Cache results in both DBs
```

## 🔧 Key Functions - DO NOT MODIFY

### Database Integration (`data/db_integration.py`)
```python
def get_cached_stock_data(ticker, timeframe, period, source):
    """WORKING - Don't touch core logic"""
    
def store_stock_data(ticker, timeframe, period, data, source):
    """WORKING - Stores to both DBs"""
    
def get_fundamentals_data(ticker):
    """WORKING - 48hr cache, expensive API calls"""
```

### Bulk Scanner (`analysis/bulk_scanner.py`)
```python
def bulk_load_all_data(self, target_tickers):
    """WORKING - Loads ALL data in 1-2 queries"""
    
def process_stocks_in_batches(self, stocks_data):
    """WORKING - Parallel processing with workers"""
```

### Strategy Management (`analysis/strategy.py`)
```python
class ValueMomentumStrategy:
    """WORKING - Core strategy implementation"""
    
def analyze_stock(ticker):
    """WORKING - Single stock analysis with DB-first approach"""
```

### Enhanced Scanner (`ui/enhanced_scanner.py`)
```python
def render_enhanced_scanner_ui():
    """WORKING - Optimized bulk scanning UI"""
    
def start_enhanced_scan(scanner, universe_file, limit_stocks, batch_size):
    """WORKING - Uses bulk_scanner.py for performance"""
```

### API Management (`data/stock_data.py`)
```python
def get_stock_data_alphavantage(ticker, timeframe="1d", period="1y"):
    """WORKING - Rate limited, 12sec delays"""
    
def get_stock_data_yahoo(ticker, timeframe="1d", period="1y"):
    """WORKING - Fallback API"""
```

## 🚨 Critical Rules

### ✅ DO
- Check database BEFORE API calls
- Use `bulk_scanner.py` for >10 stocks
- Cache ALL API results immediately
- Handle errors with fallbacks
- Use existing session state

### ❌ DON'T
- Skip database cache checks
- Make individual API calls in loops
- Modify core data structures
- Remove error handling
- Ignore rate limits

## 📊 Data Structures (KEEP THESE)

### Analysis Result
```python
{
    "ticker": "AAPL",
    "price": 150.25,
    "tech_score": 75,
    "signal": "BUY",
    "above_ma40": True,
    "pe_ratio": 25.4,
    "data_source": "alphavantage"
}
```

### Session State (PRESERVE)
```python
st.session_state = {
    'strategy': ValueMomentumStrategy(),
    'watchlist_manager': WatchlistManager(),
    'db_storage': DatabaseStorage(),
    'scan_results': []
}
```

## ⚡ Performance Patterns

### For Single Stock
```python
# Use existing pattern from scanner.py
data = get_cached_stock_data(ticker, "1d", "1y", "alphavantage")
if data is None:
    data = get_stock_data_alphavantage(ticker)
    store_stock_data(ticker, "1d", "1y", data, "alphavantage")
```

### For Multiple Stocks (>10)
```python
# Use bulk_scanner.py - it's optimized
scanner = BulkStockScanner()
results = scanner.scan_stocks(tickers, strategy)
```

## 🗃️ File Responsibilities (DON'T CHANGE)

```
data/
├── db_integration.py     # UNIFIED DB interface - WORKING
├── stock_data.py        # API calls - WORKING  
├── supabase_client.py   # Cloud DB - WORKING

analysis/
├── bulk_scanner.py      # Bulk operations - OPTIMIZED
├── scanner.py          # Single stock - WORKING
├── strategy.py         # Value/Momentum strategy - WORKING

ui/
├── batch_analysis.py    # Bulk UI - WORKING
├── watchlist.py        # Watchlist UI - WORKING
├── enhanced_scanner.py  # Enhanced scanner UI - WORKING
```

## 🔧 Configuration (TESTED VALUES)

### Cache Expiration
```python
CACHE_EXPIRATION = {
    'fundamentals': 172800,  # 48 hours (expensive)
    'daily_prices': 21600,   # 6 hours
    'intraday': 7200        # 2 hours
}
```

### Rate Limits (TUNED)
```python
ALPHA_VANTAGE_DELAY = 12  # seconds between calls
YAHOO_DELAY = 1          # second between calls
API_BATCH_SIZE = 10      # stocks per batch
```

### Bulk Processing (OPTIMIZED)
```python
MAX_API_WORKERS = 3      # Don't increase - rate limits
ANALYSIS_BATCH_SIZE = 20 # Optimal for memory
MAX_ANALYSIS_WORKERS = 4 # CPU cores
```

## 🐛 Error Handling Patterns

### Database Error
```python
try:
    data = get_cached_stock_data(ticker, ...)
except Exception as e:
    logger.error(f"DB error for {ticker}: {e}")
    # Continue with API call - don't crash
```

### API Error
```python
try:
    data = get_stock_data_alphavantage(ticker)
except Exception as e:
    logger.warning(f"Alpha Vantage failed: {e}")
    data = get_stock_data_yahoo(ticker)  # Fallback
```

## 🚀 Quick Development Guide

### Adding New Analysis
1. Add to `analysis/scanner.py` for single stocks
2. Add to `analysis/bulk_scanner.py` for bulk operations  
3. Update `analysis/strategy.py` for strategy changes
4. Keep database-first pattern
5. Test with >50 stocks for performance

### Adding New UI Component
1. Add to `ui/` folder (like `ui/enhanced_scanner.py`)
2. Use existing session state structure
3. Handle loading states properly
4. Show progress for bulk operations
5. Cache results in session state

### Debugging Performance
1. Check logs for API call frequency
2. Monitor database query counts
3. Use bulk scanner for >10 stocks
4. Profile memory usage with large datasets

## 📈 Performance Benchmarks (CURRENT)

- **10 stocks**: <30 seconds (mostly cached)
- **50 stocks**: 1-3 minutes (some API calls)
- **100+ stocks**: Use bulk scanner, 3-8 minutes
- **Database queries**: <1 second for bulk loads
- **API success rate**: >95% with fallbacks

## 🔄 Common Code Patterns

### Check Cache First
```python
# ALWAYS start with this pattern
cached_data = get_cached_stock_data(ticker, timeframe, period, source)
if cached_data is not None and not is_data_stale(cached_data):
    return cached_data
```

### Batch API Calls
```python
# For multiple stocks - use existing bulk_scanner pattern
for batch in batches_of_10(tickers):
    # 12 second delay between batches for Alpha Vantage
    time.sleep(ALPHA_VANTAGE_DELAY)
    process_batch(batch)
```

### Store Results
```python
# ALWAYS cache successful API calls
if api_data is not None:
    store_stock_data(ticker, timeframe, period, api_data, source)
```

---

## 🎯 CURRENT STATUS

### ✅ WORKING (Don't touch)
- Database caching system
- API fallback mechanism  
- Bulk scanner optimization
- Error handling framework
- Core UI components
- **File structure cleanup** ✅

### 🚧 IN PROGRESS
- Enhanced scanner UI (ui/enhanced_scanner.py)
- Performance monitoring
- Additional strategies

