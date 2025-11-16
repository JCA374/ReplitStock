# ReplitStock - Clean Project Structure

## Core Workflow
```
Download Data → Technical Analysis → Fundamental Analysis → Generate Report → Save to SQLite
```

## File Structure

### Entry Point
- **generate_weekly_report.py** - Main script to run complete analysis

### Core Analysis (`core/`)
- **stock_analyzer.py** - Main analysis engine (single + batch)
- **technical_indicators.py** - RSI-7, KAMA, MACD, Volume
- **fundamental_metrics.py** - Piotroski F-Score, profitability
- **settings_manager.py** - Loads analysis_settings.yaml
- **universe_manager.py** - Manages 352 Swedish stocks from CSV

### Data Fetching (`data/`)
- **stock_data.py** - Stock data fetcher (Yahoo Finance)
- **yahoo_finance_robust.py** - Robust 3-tier fallback fetcher
- **db_manager.py** - SQLite database operations (CLEANED - SQLite only)
- **db_models.py** - SQLAlchemy ORM models

### Reports (`reports/`)
- **weekly_report.py** - Report orchestrator
- **html_generator.py** - HTML report generation
- **csv_json_generators.py** - CSV and JSON reports
- **report_generator.py** - Base report class

### Utilities (`utils/`)
- **market_hours.py** - Stockholm Exchange hours logic

### Configuration
- **analysis_settings.yaml** - Main configuration (500+ lines)
- **config.py** - Database paths and settings
- **migrate_database.py** - Database migration tool

### Stock Universe (`data/csv/`)
- **updated_large.csv** - 100 large cap stocks
- **updated_mid.csv** - 143 mid cap stocks
- **updated_small.csv** - 109 small cap stocks

### Tests (Essential Only)
- **test_short_report.py** - Complete system validation
- **test_yahoo_robust.py** - Data fetching tests
- **test_phase1.py** - Settings & universe tests
- **test_analysis_engine.py** - Analysis engine tests
- **test_report_generation.py** - Report generation tests
- **diagnose_yahoo_finance.py** - Data fetching diagnostic tool

### Database (SQLite)
**Location:** `stock_analysis.db`

**Tables:**
- `stock_data_cache` - Price data with timestamps
- `fundamentals_cache` - Fundamental data
- `stock_universe` - 352 stocks, market cap tiers
- `analysis_runs` - Analysis run tracking
- `daily_rankings` - Top N stocks per tier
- `data_fetch_log` - API usage tracking
- `watchlist` - User watchlist

## Removed Files (Cleanup)
- ❌ Supabase files (3 files, ~50KB)
- ❌ Demo data (2 files)
- ❌ Unused utilities (3 files)
- ❌ Redundant tests (4 files)
- ❌ Old migrations (1 file)

**Total removed:** 14 files, ~4000 lines of code

## Quick Start

```bash
# Run complete analysis (352 stocks)
python generate_weekly_report.py

# Run quick test (8 stocks)
python test_short_report.py

# Diagnose data fetching
python diagnose_yahoo_finance.py
```

## System Features

### Data Fetching
- 3-tier fallback: yfinance → urllib → requests
- Automatic retry with exponential backoff
- Market-aware caching (5h price, 24h fundamentals)

### Analysis
- **Technical:** RSI-7 (Cardwell), KAMA, MACD, Volume 1.5×
- **Fundamental:** Piotroski F-Score ≥7, Gross Profitability >20%
- **Weighting:** 70% technical, 30% fundamental

### Reports
- **HTML:** Professional report with charts
- **CSV:** Excel-compatible rankings
- **JSON:** API-friendly format

### Database
- **SQLite only** (no external dependencies)
- Automatic caching and expiration
- Market hours awareness

## Configuration

All parameters in `analysis_settings.yaml`:
- Market cap tiers (Large/Mid/Small)
- Top N stocks per tier (15/20/10)
- Cache durations (5h/24h)
- Technical indicators (RSI-7, KAMA)
- Fundamental filters (Piotroski ≥7)
- Scoring weights (70/30)

## Performance

- **First run:** ~15-20 minutes (352 stocks, no cache)
- **With cache:** ~5 minutes (95% cache hit rate)
- **Test mode:** ~30 seconds (8 stocks)

---

**Status:** Clean, focused, production-ready
**Lines of Code:** ~3000 (down from ~7000)
**Focus:** Download → Analyze → Report → SQLite
