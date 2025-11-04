# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Stock Analysis Application - A comprehensive stock analysis tool built with Streamlit, focused on Swedish market stocks with advanced screening and analysis capabilities. Uses a dual database system (SQLite + Supabase) with intelligent data management and performance-optimized bulk scanning.

## Essential Commands

### Running the Application
```bash
# Main application (default port 8501)
streamlit run app.py

# On Replit (port 5000)
streamlit run app.py --server.port 5000 --server.address 0.0.0.0
```

### Testing
```bash
# Run all tests
python test/run_tests.py

# Run specific test modules
python -m test.test_data_retrieval
python test/simple_pe_test.py

# Quick P/E ratio debugging
python test/test_pe_debug.py
```

### Database Operations
```bash
# Populate default/sample data
python populate_default_data.py

# Run database migrations
python migrations/add_name_to_watchlist.py

# Migrate watchlists
python scripts/migrate_watchlists.py

# Fix database URLs (if needed)
python fix_database_urls.py
```

### Development Setup
```bash
# Windows
setup-windows.bat

# Linux/Mac
chmod +x setup-linux-mac.sh
./setup-linux-mac.sh

# Manual setup
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## Architecture

### Three-Layer Architecture

1. **Data Layer** (`data/`)
   - **Dual Database System**: SQLite (primary/local) + Supabase (optional cloud)
   - **Database Integration** (`db_integration.py`): Unified interface with automatic fallback
   - **Prioritization**: Attempts Supabase first, falls back to SQLite
   - **Models** (`db_models.py`): SQLAlchemy ORM models for all entities
   - **Stock Data Fetcher** (`stock_data.py`): Multi-source data retrieval (Alpha Vantage, Yahoo Finance)

2. **Analysis Layer** (`analysis/`)
   - **Bulk Scanner** (`bulk_scanner.py`): High-performance bulk analysis engine
   - **Technical Analysis** (`technical.py`): RSI, MACD, moving averages, trend indicators
   - **Fundamental Analysis** (`fundamental.py`): P/E ratios, profit margins, revenue growth
   - **Strategy** (`strategy.py`): Value & Momentum strategy implementation
   - **Scanner** (`scanner.py`): Stock screening with custom criteria

3. **UI Layer** (`ui/`)
   - **Main App** (`app.py`): Streamlit application entry point with tab-based navigation
   - **Batch Analysis** (`batch_analysis.py`): Multi-stock analysis interface
   - **Enhanced Scanner** (`enhanced_scanner.py`): Advanced filtering and screening UI
   - **Company Explorer** (`company_explorer.py`): Search and explore Swedish market companies
   - **Watchlist Management** (`watchlist.py`): Create and manage stock collections

### Services Layer (`services/`)
Business logic components that orchestrate between data and UI:
- **Stock Data Manager**: Centralized data operations
- **Watchlist Manager**: Watchlist CRUD operations
- **Company Explorer**: Company search and filtering

## Critical Performance Patterns

### Bulk Loading (ALWAYS Use This for Multiple Stocks)

**NEVER do this** (slow, multiple DB queries):
```python
# ❌ Individual calls in a loop
results = []
for ticker in tickers:
    data = get_cached_stock_data(ticker)
    result = analyze_stock(ticker)
    results.append(result)
```

**ALWAYS do this** (fast, bulk operations):
```python
# ✅ Use bulk scanner
from analysis.bulk_scanner import optimized_bulk_scan

results = optimized_bulk_scan(
    target_tickers=tickers,
    fetch_missing=True,
    progress_callback=update_progress
)
```

**Why**: Bulk loading reduces database queries by ~95% and API calls by ~70%. See `fix.md` for detailed explanation.

### Database Session Management

**Always use context managers** for database sessions:
```python
from data.db_connection import get_db_session_context

# ✅ Proper session management
with get_db_session_context() as session:
    # Do database operations
    result = session.query(Model).filter(...).all()
# Session automatically closed
```

### Caching Strategy

The application uses aggressive caching configured in `config.py`:
- **Fundamentals**: 48 hours cache (changes slowly)
- **Price data**: 6 hours cache
- **Technical indicators**: 3 hours cache
- **Intraday data**: 1 hour cache

When modifying data retrieval:
1. Check cache first via `get_cached_stock_data()` or `get_cached_fundamentals()`
2. Store retrieved data using `cache_stock_data()` or `cache_fundamentals()`
3. Respect cache expiration settings in `config.CACHE_SETTINGS`

## Key Configuration (`config.py`)

All major settings are centralized in `config.py`:

- **API Configuration**: Alpha Vantage, Yahoo Finance settings
- **Database Paths**: SQLite and Supabase connection strings
- **Technical Analysis Parameters**: MA windows, RSI periods, MACD settings
- **Bulk Scanner Config** (`BULK_SCANNER_CONFIG`): Performance tuning for bulk operations
- **API Delays** (`API_DELAYS`): Rate limiting to prevent API throttling
- **Cache Settings** (`CACHE_SETTINGS`): Cache durations per data type
- **UI Settings** (`UI_SETTINGS`): UI optimization flags

**Environment variables** (`.env` or Streamlit secrets):
```env
ALPHA_VANTAGE_API_KEY=your_key
SUPABASE_URL=your_url
SUPABASE_KEY=your_key
```

## Important Patterns & Gotchas

### 1. Database Prioritization
The system uses SQLite for **watchlist operations exclusively** but attempts Supabase first for other data:
- Watchlists → SQLite only (reliable, local)
- Stock data cache → Supabase with SQLite fallback
- Analysis results → Both databases if available

### 2. Data Source Priority
Default: `['database', 'alphavantage', 'yahoo']`
- Always check cache first
- Prefer Alpha Vantage for comprehensive data
- Fall back to Yahoo Finance (no API key needed)

### 3. Bulk Scanner Architecture
`BulkDatabaseLoader` → `fetch_missing_data()` → `_process_batch_parallel()`
1. Load ALL data from databases in bulk (2 queries vs N queries)
2. Identify missing tickers
3. Fetch missing data via batch API calls
4. Analyze in parallel batches
5. Stream results to avoid memory issues

### 4. Swedish Stock Ticker Format
Swedish stocks use `.ST` suffix:
```python
STOCKHOLM_EXCHANGE_SUFFIX = ".ST"
ticker = "AAPL.ST"  # Apple on Stockholm exchange
```

### 5. Analysis Results Storage
When storing analysis results, use the proper format defined in `db_integration.store_analysis_result()`:
- Signal must be: 'BUY', 'SELL', or 'HOLD'
- Include `data_source` to track where data came from
- Store timestamp as Unix epoch: `int(time.time())`

### 6. Performance Monitoring
The `PerformanceMonitor` class tracks:
- API calls and cache hit rates
- Processing times
- Error rates

Enable via `config.PERFORMANCE_LOGGING` settings.

### 7. UI Updates in Streamlit
Use progress callbacks for long-running operations:
```python
def update_progress(percentage, message):
    progress_bar.progress(percentage)
    status_text.text(message)

results = optimized_bulk_scan(
    target_tickers=tickers,
    progress_callback=update_progress
)
```

## Common Development Tasks

### Adding a New Technical Indicator
1. Add calculation function to `analysis/technical.py`
2. Include in `calculate_all_indicators()` return dict
3. Update `generate_technical_signals()` if it affects scoring
4. Add UI display in relevant UI components

### Adding a New Scanner Criteria
1. Define in `config.SCANNER_CRITERIA` dict
2. Implement filter logic in `analysis/scanner.py`
3. Add UI control in `ui/enhanced_scanner.py`
4. Test with bulk scanner to ensure performance

### Database Schema Changes
1. Update SQLAlchemy models in `data/db_models.py`
2. Create migration script in `migrations/`
3. Test on fresh database: delete `stock_data.db` and restart
4. Document in migration guide if affects existing data

### Troubleshooting P/E Ratio Issues
Common issue: P/E values showing as None or N/A
1. Run `python test/test_pe_debug.py` to diagnose
2. Check `data/stock_data.py` → `get_fundamentals()` method
3. Verify extraction: `info.get('trailingPE') or info.get('forwardPE')`
4. Clear cache if old data is cached: check database viewer

## Files Not to Modify Directly

- `stock_data.db`: SQLite database (auto-generated)
- `__pycache__/`: Python cache directories
- `.streamlit/secrets.toml`: Local secrets (use `.env` template)

## Testing Strategy

- **Quick tests**: Use `test/simple_pe_test.py` for rapid P/E debugging
- **Comprehensive tests**: Run `test/run_tests.py` for full test suite
- **Performance tests**: Check `utils/performance_monitor.py` output
- Test with sample data first: `populate_default_data.py` creates test data

## Performance Optimization Checklist

When adding new features that process multiple stocks:
- [ ] Use `optimized_bulk_scan()` instead of loops
- [ ] Use database context managers for sessions
- [ ] Cache results appropriately
- [ ] Add progress callbacks for UI feedback
- [ ] Consider memory usage for large datasets (enable streaming)
- [ ] Test with 100+ stocks to verify performance
