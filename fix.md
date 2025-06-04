After reviewing your code thoroughly, I can see you have a sophisticated stock analysis application with multiple components. Here's my analysis and improvement plan:

## Current State Analysis

Your app has:
1. **Navigation**: Sidebar-based with 3 main pages (Single Stock, Batch Analysis, Watchlist)
2. **Development Section**: Hidden in an expander with additional tools
3. **Database Status**: Shows in sidebar
4. **Batch Analysis Settings**: Appear in sidebar when on that page
5. **Complex session state management**: For preserving data between page changes

## Issues I've Identified:

1. **Navigation Confusion**: Important features like Enhanced Scanner and Company Explorer are hidden in "Development" section
2. **Sidebar Overload**: Too much functionality in the sidebar makes it cluttered
3. **Context Switching**: Users need to constantly look between sidebar and main content
4. **Hidden Features**: Valuable tools are not discoverable

## Improvement Plan

Here's a detailed markdown file for the UI improvements:

```markdown
# Stock Analysis App - UI Improvement Plan

## Goal
Improve usability by reorganizing the interface to be more intuitive and less cluttered, while maintaining all existing functionality.

## Phase 1: Navigation Restructure

### 1.1 Replace Sidebar Navigation with Tab-Based Navigation
**Current Code to Remove** (app.py, lines ~122-134):
```python
# Sidebar for navigation
st.sidebar.title("Navigation")

# Main pages
page = st.sidebar.radio(
    "Select a page:",
    ["Single Stock Analysis", "Batch Analysis", "Watchlist"]
)
```

**Replace With**:
```python
# Main navigation tabs at the top of the page
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Single Stock", 
    "📈 Batch Analysis", 
    "📋 Watchlist",
    "🔍 Stock Explorer",
    "🚀 Scanner",
    "🗄️ Database"
])

with tab1:
    render_analysis_tab()
    
with tab2:
    display_batch_analysis()
    
with tab3:
    display_watchlist()
    
with tab4:
    display_company_explorer()
    
with tab5:
    render_enhanced_scanner_ui()
    
with tab6:
    display_database_viewer()
```

### 1.2 Remove Development Section
**Remove** (app.py, lines ~213-223):
```python
# Development section at the bottom with expander
st.sidebar.markdown("---")
with st.sidebar.expander("Development", expanded=False):
    dev_pages = ["Enhanced Stock Scanner", "Company Explorer",
                 "Database Viewer"]
    for dev_page in dev_pages:
        if st.button(dev_page, key=f"dev_{dev_page}", use_container_width=True):
            page = dev_page
            st.session_state.selected_page = dev_page
```

## Phase 2: Sidebar Simplification

### 2.1 Move Database Status to Header
**Current Code to Remove** (app.py, display_database_status function):
Remove the entire `display_database_status()` function and its call.

**Add to Header Section** (after line ~96):
```python
# Header section with status indicator
col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    st.title("Stock Analysis Tool")
    st.markdown("Analyze stocks using both fundamental (value) and technical (momentum) factors.")

with col2:
    if connection_type == "postgresql":
        st.success("✅ Supabase Connected")
    else:
        st.info("💾 Local Database")

with col3:
    # Quick stats
    watchlist_count = len(get_watchlist())
    st.metric("Watchlist", watchlist_count)
```

### 2.2 Keep Only Essential Items in Sidebar
The sidebar should only contain:
- App logo/branding
- User settings (if any)
- Help/Documentation links
- Version info

**New Sidebar Content**:
```python
# Simplified sidebar
st.sidebar.title("📈 Stock Analyzer")
st.sidebar.markdown("---")

# Quick actions
st.sidebar.subheader("Quick Actions")
if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# Help section
with st.sidebar.expander("ℹ️ Help"):
    st.markdown("""
    - **Single Stock**: Analyze individual stocks
    - **Batch Analysis**: Analyze multiple stocks
    - **Watchlist**: Manage your stock lists
    - **Explorer**: Search for stocks
    - **Scanner**: Find stocks by criteria
    """)

# Footer
st.sidebar.markdown("---")
st.sidebar.caption(f"v1.0 | DB: {connection_type}")
```

## Phase 3: Tab-Specific Improvements

### 3.1 Batch Analysis Tab
**Move settings from sidebar to main content**:

In `ui/batch_analysis.py`, replace the sidebar settings section with:
```python
def display_batch_analysis():
    st.header("Batch Analysis")
    st.write("Analyze multiple stocks at once using database cache first, then API fallback.")
    
    # Settings in main content area
    with st.expander("⚙️ Analysis Settings", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            analysis_mode = st.radio(
                "Analysis Mode:",
                ["All Watchlist Stocks", "Selected Watchlist", "All Small Cap",
                 "All Mid Cap", "All Large Cap", "Selected Stocks"],
                key="batch_analysis_mode"
            )
        
        with col2:
            # Additional settings here
            st.info("📊 Data Priority: Cache → Alpha Vantage → Yahoo Finance")
```

### 3.2 Single Stock Analysis Tab
**Improve layout** in `tabs/analysis_tab.py`:
```python
def render_analysis_tab():
    # Create two columns for better organization
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("Single Stock Analysis")
        
        # Quick analysis box
        with st.container():
            st.subheader("🔍 Quick Analysis")
            
            # Tabs for different input methods
            input_tab1, input_tab2 = st.tabs(["📝 Manual Entry", "📋 From Watchlist"])
            
            with input_tab1:
                # Manual ticker form
                ...
            
            with input_tab2:
                # Watchlist selection
                ...
    
    with col2:
        # Recent analyses or quick stats
        st.subheader("📊 Recent Analyses")
        # Show last 5 analyzed stocks from session state
```

### 3.3 Enhanced Scanner Tab
**Make controls more accessible**:
```python
def render_enhanced_scanner_ui():
    st.header("📊 Enhanced Stock Scanner")
    
    # Main controls at top, not in sidebar
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        selected_universe = st.selectbox(
            "🌍 Stock Universe",
            ["OMXS30", "S&P 500 Top 30", "Watchlist", "All Database Stocks"],
            help="Choose which set of stocks to scan"
        )
    
    with col2:
        limit_stocks = st.checkbox("Limit to 20", value=False)
    
    with col3:
        if st.button("🚀 Start Scan", type="primary", use_container_width=True):
            start_enhanced_scan(...)
```

## Phase 4: Session State Simplification

### 4.1 Remove Complex Page State Management
**Remove**:
```python
# Store the selected page in session state if needed
if 'selected_page' not in st.session_state:
    st.session_state.selected_page = page
else:
    st.session_state.selected_page = page
```

Since we're using tabs, Streamlit handles the state automatically.

### 4.2 Simplify Preservation Logic
Keep only essential state preservation:
```python
# Initialize core components once
if 'strategy' not in st.session_state:
    st.session_state.strategy = ValueMomentumStrategy()
    st.session_state.watchlist_manager = SimpleWatchlistManager()
    st.session_state.company_explorer = CompanyExplorer(create_db_storage())
```

## Phase 5: Visual Improvements

### 5.1 Add Welcome Dashboard
When no analysis is active, show a dashboard:
```python
def show_welcome_dashboard():
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📊 Stocks in Database", len(get_all_cached_stocks()))
    
    with col2:
        st.metric("📋 Watchlist Items", len(get_watchlist()))
    
    with col3:
        st.metric("📈 Recent Analyses", len(st.session_state.get('recent_analyses', [])))
    
    # Quick actions
    st.subheader("🚀 Quick Start")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Analyze OMXS30", use_container_width=True):
            st.session_state.quick_action = "analyze_omxs30"
    
    with col2:
        if st.button("Scan Watchlist", use_container_width=True):
            st.session_state.quick_action = "scan_watchlist"
    
    with col3:
        if st.button("Find New Stocks", use_container_width=True):
            st.session_state.quick_action = "explore_stocks"
```

## Implementation Priority

1. **High Priority** (Do First):
   - Convert to tab navigation
   - Move batch analysis settings to main content
   - Simplify sidebar

2. **Medium Priority**:
   - Improve single stock analysis layout
   - Add welcome dashboard
   - Enhance scanner UI

3. **Low Priority**:
   - Visual polish
   - Additional quick actions
   - Performance optimizations

## Benefits

1. **Improved Discoverability**: All features visible in main navigation
2. **Reduced Cognitive Load**: Less sidebar switching
3. **Better Context**: Settings near their related content
4. **Cleaner Interface**: More space for actual content
5. **Modern UX**: Tab-based navigation is more intuitive

## Migration Notes

- All existing functionality is preserved
- Session state for critical data remains
- Database connections unchanged
- No changes to core analysis logic
```

This plan will significantly improve the usability of your application while maintaining all functionality. The key changes are:

1. **Tab-based navigation** instead of sidebar radio buttons
2. **Settings moved to context** where they're used
3. **Hidden features made visible** in main navigation
4. **Simplified sidebar** with only global actions
5. **Better visual hierarchy** with proper spacing and grouping

Would you like me to elaborate on any specific part of this plan or help with the implementation of any particular section?