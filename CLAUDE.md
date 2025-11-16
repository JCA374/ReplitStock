# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

# ReplitStock: Automatic Stock Analysis System

## Project Overview

Research-optimized automatic stock analysis system for 352 Swedish stocks (OMXS). Fully automatic weekly analysis pipeline with research-backed parameters.

**Key Characteristics:**
- **352 Swedish stocks** (100 large, 143 mid, 109 small cap)
- **Weekly analysis** (Friday 18:00 CET optimal timing)
- **Research-backed** (2018-2025 academic studies)
- **70/30 strategy** (technical/fundamental)
- **Expected**: 8-12% annual alpha, 0.8-1.2 Sharpe ratio
- **Reports**: HTML, CSV, JSON formats
- **Robust data**: 3-tier fallback with automatic retry
- **No API keys required**: Works with stdlib (urllib)

## Quick Commands

### Essential

```bash
# Quick health check (5 stocks, 30 sec)
./quick_test.sh

# Weekly analysis (352 stocks, 15-20 min first, 5 min cached)
python generate_weekly_report.py

# Diagnose data fetching issues
python diagnose_yahoo_finance.py

# Comprehensive data test (5/5 tests)
python test_yahoo_robust.py

# Database migration
python migrate_database.py
```

### Test Suite

```bash
# Phase tests
python test_phase1.py              # Settings & Universe (20 stocks)
python test_analysis_engine.py     # Technical & Fundamental
python test_report_generation.py   # HTML/CSV/JSON

# Data tests
python test_csv_loading.py         # All 352 stocks
python test_data_sources.py        # Source comparison
python test_yahoo_robust.py        # Robust fetcher (5 tests)
python test_alpha_vantage.py       # Alpha Vantage (optional)
```

### Development

```bash
# Custom stocks
python -c "
from core.stock_analyzer import BatchAnalyzer
from core.settings_manager import get_settings

tickers = ['VOLV-B.ST', 'ERIC-B.ST', 'HM-B.ST']
results = BatchAnalyzer(get_settings().as_dict()).analyze_batch(tickers)
for r in results:
    if r.get('analysis_successful'):
        print(f\"{r['ticker']}: {r['composite_score']:.1f}\")
"

# Single stock
python -c "
from core.stock_analyzer import StockAnalyzer
from core.settings_manager import get_settings
result = StockAnalyzer(get_settings().as_dict()).analyze('VOLV-B.ST')
print(f\"Score: {result['composite_score']:.1f}/100\")
"
```

## Architecture

### Data Fetching (3-Tier Fallback)

```
Request VOLV-B.ST
    ↓
[Layer 1: yfinance] (3 retries, 2s delay)
    ↓ fail
[Layer 2: urllib] (3 retries, 2s delay) ← Built-in, no deps!
    ↓ fail  
[Layer 3: requests] (3 retries, 2s delay)
    ↓
Result or None
```

**Key:** Automatic fallback handles SSL/TLS errors by using urllib (built-in Python).

**Files:**
- `data/yahoo_finance_robust.py` - RobustYahooFetcher (recommended)
- `data/stock_data.py` - StockDataFetcher (current, works)
- `diagnose_yahoo_finance.py` - Diagnostic tool

### Analysis Pipeline

```
CSV Files → UniverseManager → StockAnalyzer
    ↓
Market-Aware Cache (5h price, 24h fund)
    ↓
Robust Fetcher (3-tier + retries)
    ↓
BatchAnalyzer → Filter & Rank
    ↓
Reports (HTML/CSV/JSON)
```

### Core Phases

**Phase 1:** Settings & Configuration
- `analysis_settings.yaml` (master config)
- `core/settings_manager.py` (type-safe loader)
- `core/universe_manager.py` (352 stocks from CSV)

**Phase 2:** Analysis Engine  
- `core/technical_indicators.py` (RSI-7, KAMA, MACD)
- `core/fundamental_metrics.py` (Piotroski, profitability)
- `core/stock_analyzer.py` (single + batch)

**Phase 3:** Report Generation
- `reports/html_generator.py` (professional HTML)
- `reports/csv_json_generators.py` (Excel/API formats)
- `reports/weekly_report.py` (orchestrator)

### Database (SQLite)

**Core Tables:**
- `stock_data_cache` - Price with timestamps
- `fundamentals_cache` - Fundamental data
- `stock_universe` - 352 stocks, market cap tiers
- `analysis_runs` - Track each run
- `daily_rankings` - Top N per tier
- `data_fetch_log` - API usage tracking

## Research-Backed Parameters (Non-Obvious!)

### RSI-7 (Not 14!)
- Traditional: 14 periods (too slow)
- **Our system: 7 periods** with Cardwell method (RSI > 50 = bullish)
- Config: `rsi_period: 7`

### Volume 1.5× Confirmation
- With 1.5× volume: 65% success vs 39% without
- Config: `volume_multiplier: 1.5`

### Gross Profitability > P/E
- Formula: `(Revenue - COGS) / Assets`
- Superior to traditional P/E
- Config: `min_gross_profitability: 0.20`

### Piotroski F-Score ≥ 7
- Eliminates value traps
- Config: `min_piotroski_score: 7`

### KAMA (Not Simple MA)
- Kaufman Adaptive MA reduces false signals 30-40%
- Config: `use_kama: true`

### 70/30 Weighting
- Pure momentum: Sharpe 0.67
- Pure value: Sharpe 0.73
- **Our hybrid: Sharpe ~1.2**
- Config: `technical_weight: 70`

### Weekly Intervals
- Daily rebalancing causes overtrading
- **Friday 18:00 CET optimal**
- Config: `frequency: weekly`

## Critical Files

### `analysis_settings.yaml` (The Brain!)
**500+ lines, master configuration:**
- Market cap tiers, top N (15/20/10)
- Cache durations (5h/24h)
- Research parameters
- Scoring weights
- Report structure

**To change behavior: Edit this file first!**

### CSV Files (Stock Universe)
- `data/csv/updated_large.csv` (100)
- `data/csv/updated_mid.csv` (143)  
- `data/csv/updated_small.csv` (109)

**Column names** (non-obvious):
- Ticker: `yahooticker` (not "Ticker")
- Name: `companyname` (not "Name")

## Market-Aware Caching

**Stockholm Exchange Hours:**
- Open: 09:00-17:30 CET (Mon-Fri)
- Closed: Evenings, weekends, holidays

**Logic:**
1. Market OPEN → 5h cache
2. Market CLOSED → Cache until reopens (no API waste!)
3. Weekend → Uses Friday close
4. Friday 18:00 → Fresh data

**Performance:**
- First run: ~15-20 min (352 calls)
- Cached: <5 min (0-10 calls)
- Hit rate: >95%

**Implementation:** `utils/market_hours.py`

## Common Issues

### SSL/TLS Errors (Most Common!)

**Symptoms:**
```
ERROR: SSL_connect: SSL_ERROR_SYSCALL
ERROR: TLS connect error: invalid library
```

**Fix 1** (recommended):
```bash
pip uninstall -y curl_cffi
pip install --no-cache-dir "curl_cffi>=0.7.0,<0.8.0"
```

**Fix 2** (use robust fetcher):
```python
from data.yahoo_finance_robust import get_stock_data
data = get_stock_data('VOLV-B.ST')  # Auto-fallback to urllib
```

**Fix 3** (remove curl_cffi):
```bash
pip uninstall -y curl_cffi
pip install --force-reinstall yfinance
```

**Verify:**
```bash
python -c "import yfinance; print('✓' if not yfinance.Ticker('VOLV-B.ST').history(period='5d').empty else '✗')"
```

See: `FIX_TLS_ERROR.md`

### No Data

**Check ticker:**
```python
'VOLV-B.ST'  # ✓ Correct
'VOLVB.ST'   # ✗ Missing dash
'VOLV-B'     # ✗ Missing .ST
```

**Diagnose:**
```bash
python diagnose_yahoo_finance.py
```

### Column Errors

**Auto-handled:** `TechnicalIndicators.__init__()` normalizes uppercase/lowercase.

### Rate Limiting

- First 352-stock run takes time
- Use test mode (20 stocks): `test_phase1.py`
- Check: `data_fetch_log` table

## Development

### Test vs Production

**Test** (20 stocks):
```python
test_tickers = all_tickers[:20]  # In test files
```

**Production** (352 stocks):
```python
from core.stock_analyzer import BatchAnalyzer
results = BatchAnalyzer(settings.as_dict()).analyze_all_stocks()
```

### Add Filters

1. Edit `analysis_settings.yaml`:
```yaml
analysis:
  technical:
    new_param: value
```

2. Implement in `core/technical_indicators.py`

3. Auto-loads from YAML (no code changes)

### Change Top N

Edit `analysis_settings.yaml`:
```yaml
market_caps:
  large_cap:
    top_n: 15  # Change here
```

## Production Usage

```python
from core.stock_analyzer import BatchAnalyzer
from core.settings_manager import get_settings
from reports.weekly_report import WeeklyReportOrchestrator

settings = get_settings()
analyzer = BatchAnalyzer(settings.as_dict())
results = analyzer.analyze_all_stocks()

orchestrator = WeeklyReportOrchestrator(settings.as_dict())
files = orchestrator.generate_weekly_report(results)
```

Or:
```bash
python generate_weekly_report.py
```

## Implementation Details

### Robust Data Fetching

```python
from data.yahoo_finance_robust import RobustYahooFetcher

fetcher = RobustYahooFetcher(max_retries=3, retry_delay=2.0)
data = fetcher.get_historical_data('VOLV-B.ST', period='1y')
fundamentals = fetcher.get_fundamentals('VOLV-B.ST')
```

**Features:**
- 3 retries per method
- Configurable delays
- Returns None on fail (no crash)
- Comprehensive logging

### Column Normalization

Auto-handles case differences:
```python
# In TechnicalIndicators.__init__()
# Converts: 'Close'/'close'/'CLOSE' → 'Close'
```

## Documentation

| File | Purpose |
|------|---------|
| `CLAUDE.md` | This file - Claude Code onboarding |
| `README.md` | User documentation |
| `YAHOO_FINANCE_BEST_PRACTICES.md` | Data fetching guide |
| `FIX_TLS_ERROR.md` | SSL/TLS solutions |
| `TRANSFORMATION_PLAN.md` | Research methodology |

## Quick Reference

**Key Files:**
1. `generate_weekly_report.py` - Entry point
2. `analysis_settings.yaml` - Configuration
3. `core/stock_analyzer.py` - Analysis
4. `data/yahoo_finance_robust.py` - Data fetching
5. `reports/weekly_report.py` - Reports

**Quick Test:**
```bash
./quick_test.sh  # 30 sec
```

**Diagnostics:**
```bash
python diagnose_yahoo_finance.py  # Test all methods
python test_yahoo_robust.py       # 5/5 test suite
```

**Common Pattern:**
```python
from core.settings_manager import get_settings
from core.stock_analyzer import BatchAnalyzer
from reports.weekly_report import WeeklyReportOrchestrator

settings = get_settings()
results = BatchAnalyzer(settings.as_dict()).analyze_batch(['VOLV-B.ST'])
files = WeeklyReportOrchestrator(settings.as_dict()).generate_weekly_report(results)
```

---

**Last Updated:** 2025-11-16

**Status:**
- ✅ Phases 1-3 Complete
- ✅ Robust 3-tier data fetching
- ✅ 5/5 tests passing
- ✅ Market-aware caching
- ✅ Production-ready for 352 stocks
