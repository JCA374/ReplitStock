1. Streamline Scanner Selection (Priority: HIGH)
Current Code Location: render_scanner_selection() function
Suggested Changes:

Combine stock universe and watchlist selection into a single dropdown
Remove manual ticker entry (users can use watchlist for custom lists)
Convert scan options to a single "Advanced Options" expander

Code to REMOVE:
python# Lines 85-97: Remove manual ticker entry section
if stock_universe == "Manual Entry":
    manual_tickers = st.text_area(...)
Code to REPLACE (lines 31-84):
pythondef render_scanner_selection():
    """Simplified scanner selection interface"""

    # Single dropdown for stock selection
    col1, col2 = st.columns([3, 1])

    with col1:
        # Build options list dynamically
        options = []

        # Add watchlist options
        if 'watchlist_manager' in st.session_state:
            manager = st.session_state.watchlist_manager
            watchlists = manager.get_all_watchlists()
            for wl in watchlists:
                options.append(f"Watchlist: {wl['name']} ({len(wl.get('stocks', []))} stocks)")

        # Add market cap options
        options.extend([
            "All Watchlists Combined",
            "Small Cap Stocks (108)",
            "Mid Cap Stocks (143)", 
            "Large Cap Stocks (100)",
            "All Stocks (351)"
        ])

        selection = st.selectbox(
            "📈 Select stocks to scan:",
            options=options,
            index=0 if options else None
        )

    # Advanced options in expander
    with st.expander("⚙️ Advanced Options"):
        show_errors = st.checkbox("Show failed analyses", value=False)
        auto_add_buys = st.checkbox("Auto-add BUY signals to default watchlist", value=False)

    # Single scan button
    with col2:
        should_scan = st.button("🚀 Scan", type="primary", use_container_width=True)

    return should_scan, selection, show_errors, auto_add_buys