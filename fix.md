# Company Name Display Fix

## Problem
The batch scanner shows "No company name" for stocks like ALIG.ST and AXFO.ST because the CSV files contain "Yahoo Finance" as the company name instead of actual company names.

## Solution Options

### Option 1: Bulk Scanner Integration (RECOMMENDED)
**Best for performance and consistency**

#### Advantages:
- ✅ Fetches company names during analysis phase
- ✅ Caches results for the entire session
- ✅ Consistent data across all analysis results
- ✅ Follows the database-first pattern from technical spec
- ✅ No additional API calls during display

#### Implementation:

**Step 1: Add company name fetching to `analysis/bulk_scanner.py`**

Add this method to the `BulkStockScanner` class:
```python
def _get_company_name(self, ticker):
    """Get company name from API with session caching"""
    try:
        # Initialize cache if needed
        if 'company_names_cache' not in st.session_state:
            st.session_state.company_names_cache = {}
        
        # Return cached name if available
        if ticker in st.session_state.company_names_cache:
            return st.session_state.company_names_cache[ticker]
        
        # Fetch from API
        import yfinance as yf
        ticker_obj = yf.Ticker(ticker)
        info = ticker_obj.info
        company_name = (info.get('longName') or 
                       info.get('shortName') or 
                       info.get('companyName'))
        
        if company_name and company_name != ticker:
            # Cache and return the result
            st.session_state.company_names_cache[ticker] = company_name
            return company_name
        else:
            st.session_state.company_names_cache[ticker] = ticker
            return ticker
            
    except Exception as e:
        logger.warning(f"Could not fetch company name for {ticker}: {e}")
        st.session_state.company_names_cache[ticker] = ticker
        return ticker
```

**Step 2: Update result creation in `_analyze_all_stocks` method**

Find this section (around line 200):
```python
results.append({
    'ticker': ticker,
    'name': ticker,  # OLD LINE
    'last_price': 0,
    # ... rest of result
})
```

Replace `'name': ticker,` with:
```python
'name': self._get_company_name(ticker),
```

Also update successful analysis results:
```python
result = {
    'ticker': ticker,
    'name': self._get_company_name(ticker),  # ADD THIS
    'last_price': latest_price,
    # ... rest of result
}
```

**Step 3: Add import at top of file**
```python
import streamlit as st
```

---

### Option 2: Display-Time Fetching
**Quick fix with some performance impact**

#### Advantages:
- ✅ Minimal code changes
- ✅ Works immediately
- ❌ Slower display (API calls during rendering)
- ❌ Not cached between scans

#### Implementation:

**In `ui/batch_analysis.py`, find the display section (around line 600):**

Replace this:
```python
if name != 'N/A' and name != ticker and name.strip():
    display_name = name[:25] + "..." if len(name) > 25 else name
    st.markdown(f'<a href="{google_search_url}" target="_blank" class="batch-link"><strong>{clean_ticker}</strong><br><small>{display_name}</small></a>', unsafe_allow_html=True)
else:
    st.markdown(f'<a href="{google_search_url}" target="_blank" class="batch-link"><strong>{clean_ticker}</strong><br><small>No company name</small></a>', unsafe_allow_html=True)
```

With this:
```python
# Get company name from API if not already available
if name == 'N/A' or name == ticker or name.strip() == '' or name == 'Yahoo Finance':
    try:
        import yfinance as yf
        ticker_obj = yf.Ticker(clean_ticker)
        info = ticker_obj.info
        api_name = info.get('longName') or info.get('shortName') or info.get('companyName')
        if api_name and api_name != clean_ticker:
            name = api_name
    except:
        name = None

# Display with company name if available
if name and name != 'N/A' and name != ticker and name.strip() and name != 'Yahoo Finance':
    display_name = name[:25] + "..." if len(name) > 25 else name
    st.markdown(f'<a href="{google_search_url}" target="_blank" class="batch-link"><strong>{clean_ticker}</strong><br><small>{display_name}</small></a>', unsafe_allow_html=True)
else:
    st.markdown(f'<a href="{google_search_url}" target="_blank" class="batch-link"><strong>{clean_ticker}</strong></a>', unsafe_allow_html=True)
```

---

### Option 3: Database Integration (FUTURE-PROOF)
**Most aligned with technical specification**

#### Advantages:
- ✅ Follows database-first pattern
- ✅ Permanent caching across sessions
- ✅ Best performance after initial fetch
- ❌ More complex implementation
- ❌ Requires database schema update

#### Implementation:

**Step 1: Add company name to database models in `data/db_models.py`**
```python
class CompanyInfo(Base):
    __tablename__ = 'company_info'
    
    ticker = Column(String, primary_key=True)
    company_name = Column(String)
    sector = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow)
```

**Step 2: Add database functions to `data/db_integration.py`**
```python
def get_company_name(ticker):
    """Get company name from database or API"""
    # Check database first
    cached_name = get_cached_company_name(ticker)
    if cached_name:
        return cached_name
    
    # Fetch from API and store
    name = fetch_company_name_from_api(ticker)
    if name:
        store_company_name(ticker, name)
    return name
```

**Step 3: Use in bulk scanner**
```python
from data.db_integration import get_company_name

# In results creation:
'name': get_company_name(ticker),
```

---

## Recommendation: Option 1 (Bulk Scanner Integration)

**I recommend Option 1** because:

1. **Performance**: Company names are fetched once during analysis, not during every display
2. **Consistency**: All analysis results will have proper company names
3. **Caching**: Session-level caching prevents repeated API calls
4. **Alignment**: Follows the technical spec's pattern of fetching data during analysis
5. **Simplicity**: Minimal code changes with maximum benefit

### Expected Results After Fix:
- ALIG.ST will show "Aligera Fastigheter" 
- AXFO.ST will show "Axfood"
- All other stocks will show proper company names
- Names are cached for fast subsequent displays
- No "No company name" messages

### Testing Steps:
1. Apply Option 1 changes
2. Run a batch scan on Mid Cap stocks
3. Verify ALIG.ST and AXFO.ST show proper company names
4. Check that names persist when switching between result views
5. Confirm no performance degradation during display

This solution maintains the app's performance while providing the rich company name display you want, and it's fully aligned with your technical specification.