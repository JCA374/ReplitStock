After reviewing the code, I can see you've successfully implemented most of the changes! The core watchlist functionality looks good. However, I found a few remaining issues that need cleanup. Here's a `fix2.md` file:

```markdown
# Watchlist Feature Fix 2 - Cleanup Remaining Issues

## 🎯 Goal
Clean up remaining references to Enhanced Watchlist and ensure full integration.

## 🧹 Cleanup Tasks

### 1. Remove Enhanced Watchlist References in `ui/batch_analysis.py`

**FIND** this section (around line 1000-1100):
```python
# Enhanced bulk add to watchlist
st.subheader("📝 Bulk Add to Enhanced Watchlist")

# Initialize enhanced watchlist manager
if 'enhanced_watchlist_batch' not in st.session_state:
    st.session_state.enhanced_watchlist_batch = EnhancedWatchlistManager()

enhanced_manager = st.session_state.enhanced_watchlist_batch
```

**REPLACE WITH:**
```python
# Bulk add to watchlist
st.subheader("📝 Bulk Add to Watchlist")

# Use the simple watchlist manager
if 'watchlist_manager' not in st.session_state:
    from services.watchlist_manager import SimpleWatchlistManager
    st.session_state.watchlist_manager = SimpleWatchlistManager()

manager = st.session_state.watchlist_manager
```

### 2. Update Bulk Add Logic in `ui/batch_analysis.py`

**FIND** the entire bulk add section that references categories and enhanced features:
```python
# Get categories for selection
categories = enhanced_manager.get_categories()

# Category and tags selection
col1, col2 = st.columns([2, 1])
with col1:
    if categories:
        selected_category = st.selectbox(
            "📁 Select Category for Bulk Add:",
            categories,
            format_func=lambda x: f"{x['icon']} {x['name']} - {x['description']}",
            key="bulk_add_category"
        )
```

**REPLACE WITH** this simpler version:
```python
# Get all watchlists
watchlists = manager.get_all_watchlists()

if watchlists:
    # Watchlist selection for bulk add
    col1, col2 = st.columns([2, 1])
    
    with col1:
        target_watchlist = st.selectbox(
            "📁 Select Watchlist for Bulk Add:",
            options=watchlists,
            format_func=lambda x: f"{x['name']} {'(Default)' if x['is_default'] else ''}",
            key="bulk_add_watchlist"
        )
    
    with col2:
        # Get stocks with BUY signals
        top_buy_signals = pd.DataFrame()
        if "Signal" in filtered_df.columns:
            top_buy_signals = filtered_df[
                (filtered_df["Signal"] == "KÖP") | 
                (filtered_df["Signal"] == "BUY")
            ].head(10)
        
        if not top_buy_signals.empty and target_watchlist:
            if st.button("➕ Add All BUY Signals", type="primary", key="bulk_add_button"):
                added_count = 0
                failed_count = 0
                
                for _, stock in top_buy_signals.iterrows():
                    ticker = stock.get('Ticker', '')
                    if ticker:
                        success = manager.add_stock_to_watchlist(target_watchlist['id'], ticker)
                        if success:
                            added_count += 1
                            st.success(f"✅ Added {ticker}")
                        else:
                            st.info(f"ℹ️ {ticker} already in watchlist")
                    else:
                        failed_count += 1
                
                # Summary
                if added_count > 0:
                    st.success(f"✅ Successfully added {added_count} stocks to '{target_watchlist['name']}'!")
                if failed_count > 0:
                    st.warning(f"⚠️ {failed_count} stocks failed to add")
    
    # Show top buy signals
    if not top_buy_signals.empty:
        st.write("**Top BUY signals available:**")
        for _, stock in top_buy_signals.head(5).iterrows():
            st.write(f"• {stock.get('Ticker', 'N/A')} - Score: {stock.get('Tech Score', 'N/A')}")
else:
    st.warning("No watchlists available. Create one in the Watchlist tab.")
```

### 3. Remove Enhanced Watchlist Import

**In `ui/batch_analysis.py`**, remove this import if it exists:
```python
from services.enhanced_watchlist_manager import EnhancedWatchlistManager
```

### 4. Clean Up Legacy Watchlist References

**REMOVE** this entire section about legacy watchlist fallback:
```python
# Legacy watchlist fallback
if st.checkbox("🔄 Also add to Legacy Watchlist", key="legacy_fallback"):
    st.caption("This will add stocks to the original watchlist for backward compatibility.")
    # ... rest of the legacy code ...
```

### 5. Optional: Add Quick Actions to Batch Analysis Results

**ADD** this helper function at the top of `ui/batch_analysis.py` after the imports:
```python
def add_to_default_watchlist(ticker, name):
    """Quick add to default watchlist"""
    if 'watchlist_manager' not in st.session_state:
        from services.watchlist_manager import SimpleWatchlistManager
        st.session_state.watchlist_manager = SimpleWatchlistManager()
    
    manager = st.session_state.watchlist_manager
    watchlists = manager.get_all_watchlists()
    
    # Find default watchlist
    default_wl = next((w for w in watchlists if w['is_default']), None)
    
    if default_wl:
        return manager.add_stock_to_watchlist(default_wl['id'], ticker)
    return False
```

Then update the `add_stock_to_watchlist_with_feedback` function to use this:
```python
def add_stock_to_watchlist_with_feedback(ticker, name):
    """Add stock to default watchlist with proper feedback"""
    try:
        if not ticker:
            st.error("❌ Invalid ticker provided", icon="❌")
            return False

        success = add_to_default_watchlist(ticker, name)

        if success:
            st.success(f"✅ Added {ticker} to watchlist!", icon="✅")
            return True
        else:
            st.info(f"ℹ️ {ticker} is already in your watchlist!", icon="ℹ️")
            return False

    except Exception as e:
        st.error(f"❌ Failed to add {ticker}: {str(e)}", icon="❌")
        return False
```

### 6. Update Navigation Between Tabs

**In `ui/watchlist.py`**, update the analyze button to properly navigate:
```python
if st.button("📊 Analyze This Watchlist", type="primary", key="analyze_watchlist"):
    # Store watchlist tickers in session state for batch analysis
    tickers = [s['ticker'] for s in stock_details]
    st.session_state['batch_analysis_tickers'] = tickers
    st.session_state['selected_page'] = 'Batch Analysis'
    st.session_state['batch_analysis_mode'] = 'Selected Stocks'  # Add this line
    st.success(f"Ready to analyze {len(tickers)} stocks. Switch to Batch Analysis tab.")
    st.rerun()  # Add this to force navigation
```

## ✅ Summary
These fixes will:
- Remove all Enhanced Watchlist references from batch analysis
- Simplify the bulk add functionality to work with the simple watchlist manager
- Ensure smooth integration between Watchlist and Batch Analysis tabs
- Clean up any legacy code

The result will be a clean, consistent watchlist feature throughout the application.
```

This fix2.md addresses the remaining issues I found:

1. Enhanced Watchlist references in the batch analysis bulk add section
2. Simplifies the bulk add to work with your SimpleWatchlistManager
3. Removes unnecessary legacy watchlist code
4. Improves navigation between tabs
5. Adds a helper function for quick adds to the default watchlist

The main issue was that the batch analysis page still had code trying to use an EnhancedWatchlistManager that no longer exists. This fix replaces it with the SimpleWatchlistManager you've already implemented.