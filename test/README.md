# Test Suite for Stock Analysis App

This test suite is designed to diagnose data retrieval issues, particularly the P/E ratio problem you're experiencing.

## 📁 File Structure

```
test/
├── test_data_retrieval.py  # Comprehensive data retrieval test
├── test_pe_debug.py        # Focused P/E ratio debugging
├── run_tests.py           # Test runner script
└── README.md              # This file
```

## 🚀 Quick Start

### Option 1: Run All Tests
```bash
# From your project root directory
cd test
python run_tests.py
```

### Option 2: Run Specific Tests
```bash
# From your project root directory
python -m test.test_data_retrieval
python -m test.test_pe_debug
```

### Option 3: Run Individual Components
```bash
# Test P/E specifically
python test/test_pe_debug.py

# Test all data retrieval
python test/test_data_retrieval.py
```

## 🔍 What the Tests Do

### `test_data_retrieval.py` - Comprehensive Test
- ✅ Tests API configuration (Alpha Vantage, Yahoo Finance)
- 📈 Tests stock data fetching for multiple tickers
- 💰 **Tests P/E ratio retrieval (CRITICAL for your issue)**
- 🗄️ Tests database connectivity and cached data
- 💾 Tests caching mechanisms
- 📊 Generates detailed JSON report

### `test_pe_debug.py` - P/E Focus Test
- 🎯 **Specifically targets P/E ratio issues**
- 🔄 Compares Yahoo Finance vs Alpha Vantage vs Your App
- 💡 Generates fix recommendations
- 🚨 Identifies exactly where P/E retrieval fails

### `run_tests.py` - Test Runner
- 🔧 Sets up test environment
- ⚡ Runs quick P/E test first
- 📋 Provides summary of all results

## 📊 Expected Output

### If P/E Retrieval is Working:
```
✅ AAPL P/E Ratio: 28.5
✅ MSFT P/E Ratio: 32.1
🎯 P/E SUCCESS RATE: 4/4 (100.0%)
```

### If P/E Retrieval is Broken:
```
❌ AAPL P/E Ratio: None
❌ MSFT P/E Ratio: None  
🚨 CRITICAL ISSUE: Low P/E data availability!
💡 Recommended Actions:
   1. Check Alpha Vantage API endpoint configuration
   2. Verify API response parsing logic
```

## 🔧 Common Issues & Solutions

### Issue 1: "Import Error" 
**Problem**: Can't import your app modules
**Solution**: 
```bash
# Make sure you run from project root, not from test/ directory
cd /path/to/your/project  # Go to root where app.py is located
python test/run_tests.py
```

### Issue 2: "No P/E data from any source"
**Problem**: All P/E tests return None/N/A
**Solutions**:
1. Check network connectivity
2. Verify API keys in `.streamlit/secrets.toml`
3. Check if you've hit API rate limits
4. Try different ticker symbols

### Issue 3: "Yahoo works but app doesn't"
**Problem**: Direct Yahoo Finance returns P/E but your app doesn't
**Solution**: Fix in `data/stock_data.py`:
```python
# In get_fundamentals() method, ensure P/E is extracted:
pe_ratio = info.get('trailingPE') or info.get('forwardPE')
if pe_ratio is not None:
    fundamentals['pe_ratio'] = float(pe_ratio)
```

## 📋 Test Results Files

Tests automatically save detailed results:
- `test_results_YYYYMMDD_HHMMSS.json` - Detailed JSON results
- Console output with color-coded status indicators

## 🎯 Interpreting Results

### Critical Success Metrics:
1. **P/E Success Rate**: Should be >70% for major US stocks
2. **API Connectivity**: Both Yahoo Finance and Alpha Vantage should work
3. **Database Operations**: Should connect and cache data successfully

### Red Flags:
- ❌ P/E Success Rate: 0% = Critical issue in data retrieval
- ❌ All API tests fail = Network/configuration issue  
- ❌ Database tests fail = Database connection issue

## 🚨 Troubleshooting Your Specific Issue

Based on your description ("analyses successful but no P/E values"), the most likely causes are:

### 1. **Data Retrieval Issue** (Most Likely)
Your `get_fundamentals()` function isn't extracting P/E from the API response correctly.

**Test**: Run `python test/test_pe_debug.py` and look for:
```
📊 Yahoo Finance Direct: 28.5  ✅ (API has data)
📊 App Function: None          ❌ (App doesn't extract it)
```

### 2. **Display Logic Issue**
The P/E data is retrieved but filtered out during display.

**Test**: Look for test output showing:
```
✅ Fundamentals Retrieved: P/E = 28.5
❌ P/E displayed in batch results: N/A
```

### 3. **Caching Issue**  
Old cached data without P/E values is being used.

**Test**: Look for cache test results and clear cache if needed.

## 🔧 Quick Fixes to Try

### Fix 1: Update P/E Extraction
Edit `data/stock_data.py` in the `get_fundamentals()` method:
```python
# Find this section and make sure P/E is properly extracted
pe_ratio = info.get('trailingPE') or info.get('forwardPE')
fundamentals['pe_ratio'] = pe_ratio  # Make sure this line exists
```

### Fix 2: Clear Cache
```python
# If cached data is the issue, clear it:
# In your database, delete old fundamentals_cache entries
```

### Fix 3: Check Display Logic
Look in `helpers.py` or your results formatting code for:
```python
# Make sure P/E values aren't being filtered out
if pe_ratio is not None:  # Don't filter out zero or negative P/E
    display_pe = f"{pe_ratio:.2f}"
```

## 📞 Need Help?

If tests are still unclear, run the debug test and share the output:
```bash
python test/test_pe_debug.py > pe_debug_output.txt
```

The output will show exactly where the P/E retrieval is failing.