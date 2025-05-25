# Code Cleanup Plan

## 🗑️ Files to Remove

### 1. Duplicate Scanner Files
- **`ui/enhanced_scanner_ui.py`** - Remove (superseded by `tabs/enhanced_scanner_tab.py`)
- **`analysis/optimized_scanner.py`** - Remove (functionality merged into `analysis/scanner.py`)

### 2. Utility Files with Minimal Usage
- **`utils/pe_data_helper.py`** - Remove (simple functionality can be inline)
- **`utils/supabase_connection.py`** - Remove (functionality in `data/db_connection.py`)
- **`ui/scanner_fix.py`** - Remove (development/debugging tool)

### 3. Development Files
- **`ui/fix_indicators.py`** - Remove (if exists, development tool)
- **`migrations/create_analysis_results_table.sql`** - Remove (handled by SQLAlchemy)
- **`supabase_tables.sql`** - Remove (handled by SQLAlchemy)

### 4. CSV Processing (Optional)
- **`csv/updated_mid.csv`** - Keep but move to `data/` folder
- **`csv/updated_small.csv`** - Keep but move to `data/` folder  
- **`csv/updated_large.csv`** - Keep but move to `data/` folder

## 📁 Files to Consolidate

### 1. Merge Company Search Functionality
**Remove:** `ui/company_search.py`
**Keep:** `ui/company_explorer.py` and `services/company_explorer.py`

### 2. Merge Search History
**Remove:** `ui/search_history.py`
**Integrate into:** `services/company_explorer.py`

### 3. Database Management
**Keep:** `data/db_connection.py` (main database handler)
**Keep:** `data/db_integration.py` (high-level interface)
**Keep:** `data/db_manager.py` (SQLAlchemy operations)
**Remove:** Any database duplicates

## 🔧 Code Consolidation Changes

### Update `analysis/scanner.py`
Remove duplicate functions and keep only the optimized versions:

```python
# Remove legacy_value_momentum_scan() - use optimized version
# Remove duplicate EnhancedScanner class if exists
# Keep only the high-performance parallel processing code
```

### Update `config.py`
Remove unused configuration options:

```python
# Remove scanner performance settings that aren't used
# Remove duplicate database configurations
# Consolidate API settings
```

### Update imports in `app.py`
```python
# Remove imports for deleted files
from ui.enhanced_scanner_ui import display_enhanced_scanner  # REMOVE
from analysis.optimized_scanner import scan_stocks  # REMOVE

# Keep only:
from tabs.enhanced_scanner_tab import render_enhanced_scanner_ui
from analysis.scanner import scan_stocks
```

## 📋 Cleanup Steps

### Step 1: Remove Files
Delete these files from your project:
- `ui/enhanced_scanner_ui.py`
- `analysis/optimized_scanner.py`
- `utils/pe_data_helper.py`
- `utils/supabase_connection.py`
- `ui/scanner_fix.py`
- `ui/company_search.py`
- `ui/search_history.py`
- `migrations/create_analysis_results_table.sql`
- `supabase_tables.sql`

### Step 2: Move Files
```bash
mkdir -p data/csv
mv csv/updated_*.csv data/csv/
```

### Step 3: Update References
Update any remaining references to deleted files in:
- `app.py`
- Any import statements
- Configuration files

### Step 4: Consolidate Functions
Merge duplicate functionality into the remaining files.

## 💾 File Structure After Cleanup

```
├── app.py                          # Main application
├── config.py                       # Configuration (cleaned)
├── helpers.py                      # Utility functions
├── requirements.txt                # Dependencies
├── .replit                         # Replit config
├── .gitignore                      # Git ignore
├── data/
│   ├── csv/                        # Moved from root
│   │   ├── updated_large.csv
│   │   ├── updated_mid.csv
│   │   └── updated_small.csv
│   ├── company_data/               # Company data
│   ├── db_connection.py            # Database connection
│   ├── db_integration.py           # High-level DB interface
│   ├── db_manager.py               # SQLAlchemy operations
│   ├── db_models.py                # Database models
│   ├── stock_data.py               # Stock data fetcher
│   └── supabase_client.py          # Supabase client
├── analysis/
│   ├── fundamental.py              # Fundamental analysis
│   ├── scanner.py                  # Optimized scanner (consolidated)
│   └── technical.py                # Technical analysis
├── services/
│   ├── company_explorer.py         # Company exploration (enhanced)
│   ├── stock_data_manager.py       # Stock data management
│   └── watchlist_manager.py        # Watchlist management
├── tabs/
│   ├── analysis_tab.py             # Stock analysis tab
│   ├── enhanced_scanner_tab.py     # Scanner tab
│   └── strategy.py                 # Trading strategy
├── ui/
│   ├── batch_analysis.py           # Batch analysis
│   ├── company_explorer.py         # Company explorer UI
│   ├── database_viewer.py          # Database viewer
│   ├── single_stock.py             # Single stock analysis
│   └── watchlist.py                # Watchlist management
└── utils/
    ├── __init__.py                 # Package init
    └── ticker_mapping.py           # Ticker utilities
```

## 🎯 Benefits of Cleanup

1. **Reduced Complexity**: Fewer files to maintain
2. **No Duplication**: Single source of truth for each feature
3. **Better Performance**: Optimized scanner code only
4. **Easier Debugging**: Clear file responsibilities
5. **Simpler Deployment**: Fewer dependencies to track

## ⚠️ Before Cleanup

1. **Backup your data**: Export any important watchlists/settings
2. **Test current functionality**: Ensure everything works before cleanup
3. **Check for custom modifications**: Look for any custom code in files to be deleted

Would you like me to provide the specific updated code for the consolidated files?