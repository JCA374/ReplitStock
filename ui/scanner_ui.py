# ui/scanner_ui.py - UPDATED with clickable watchlist icons

import streamlit as st
import pandas as pd
import numpy as np
from data.db_manager import get_watchlist, get_all_cached_stocks
from analysis.scanner import scan_stocks
from config import SCANNER_CRITERIA
from data.db_integration import add_to_watchlist
import time


def render_scanner_results_with_icons(results):
    """
    Render scanner results with clickable watchlist icons for each row
    """
    if not results:
        st.info("No results to display")
        return

    st.subheader(f"🔍 Scanner Results ({len(results)} stocks found)")

    # Create a container for each result row with watchlist icon
    for idx, result in enumerate(results):
        with st.container():
            # Create columns for the table layout
            col_icon, col_ticker, col_price, col_signal, col_tech, col_ma40, col_pe = st.columns([
                                                                                                 0.5, 1.5, 1, 1, 1, 1, 1])

            # Watchlist icon column
            with col_icon:
                ticker = result.get('ticker', '')
                if st.button("➕", key=f"scanner_watchlist_{ticker}_{idx}",
                             help=f"Add {ticker} to watchlist"):
                    add_stock_to_watchlist_with_feedback(
                        ticker,
                        result.get('name', ticker)
                    )

            # Ticker and Name
            with col_ticker:
                st.write(f"**{result.get('ticker', 'N/A')}**")
                if result.get('name') and result['name'] != result.get('ticker'):
                    st.caption(result['name'])

            # Price
            with col_price:
                price = result.get('last_price', result.get('price', 0))
                if isinstance(price, (int, float)) and price > 0:
                    st.metric("Price", f"{price:.2f}")
                else:
                    st.write("N/A")

            # Signal with color coding
            with col_signal:
                signal = result.get('value_momentum_signal',
                                    result.get('signal', 'HOLD'))
                if signal in ['BUY', 'KÖP']:
                    st.success(f"🟢 {signal}")
                elif signal in ['SELL', 'SÄLJ']:
                    st.error(f"🔴 {signal}")
                else:
                    st.info(f"🟡 {signal}")

            # Tech Score
            with col_tech:
                tech_score = result.get('tech_score', 0)
                if isinstance(tech_score, (int, float)):
                    st.metric("Tech", f"{tech_score}")
                    st.progress(tech_score / 100)
                else:
                    st.write("N/A")

            # Above MA40 indicator
            with col_ma40:
                above_ma40 = result.get('above_ma40', False)
                if above_ma40:
                    st.success("✓ MA40")
                else:
                    st.error("✗ MA40")

            # P/E Ratio
            with col_pe:
                pe = result.get('pe_ratio', 'N/A')
                if isinstance(pe, (int, float)) and pe > 0:
                    st.metric("P/E", f"{pe:.1f}")
                else:
                    st.write("P/E: N/A")

        # Add a subtle divider
        st.divider()


def add_stock_to_watchlist_with_feedback(ticker, name):
    """
    Add stock to watchlist with immediate user feedback
    """
    try:
        if not ticker:
            st.warning("⚠️ Invalid ticker provided", icon="⚠️")
            return

        # Call add_to_watchlist directly - it manages its own database connections
        success = add_to_watchlist(ticker, name, "", "")

        if success:
            st.success(f"✅ Added {ticker} to watchlist!", icon="✅")
            # Brief pause to show the success message
            time.sleep(0.5)
        else:
            st.warning(f"⚠️ {ticker} is already in your watchlist!", icon="⚠️")

    except Exception as e:
        st.error(f"❌ Failed to add {ticker}: {str(e)}", icon="❌")


def display_scanner():
    """Enhanced scanner display with clickable watchlist icons"""
    st.header("Stock Scanner")
    st.write("Scan stocks based on technical and fundamental criteria")

    # Sidebar for scanner configuration
    st.sidebar.header("Scanner Settings")

    # Select scan scope
    scan_scope = st.sidebar.radio(
        "Scan Scope:",
        ["All Available Stocks", "Watchlist Only"],
        key="scanner_scope"
    )

    # Get available stocks for information
    watchlist = get_watchlist()
    all_stocks = get_all_cached_stocks()

    # Show available stocks count
    if scan_scope == "Watchlist Only":
        st.sidebar.info(f"Watchlist contains {len(watchlist)} stocks")
    else:
        st.sidebar.info(f"Database contains {len(all_stocks)} stocks")

    # Criteria selection
    st.sidebar.subheader("Select Criteria")

    # Dictionary to store selected criteria
    selected_criteria = {}

    # Strategy Selection
    st.sidebar.markdown("**Strategy Selection**")

    strategy_option = st.sidebar.radio(
        "Scanner Mode:",
        ["Value & Momentum Strategy", "Custom Criteria"],
        key="scanner_strategy"
    )

    if strategy_option == "Value & Momentum Strategy":
        # Use the Value & Momentum Strategy
        selected_criteria["strategy"] = "value_momentum"

    # Technical Criteria
    st.sidebar.markdown("**Technical Criteria**")

    # SMA Conditions
    price_sma_option = st.sidebar.selectbox(
        "Price vs. SMA:",
        ["None", "Price Above SMA", "Price Below SMA"],
        key="scanner_price_sma"
    )

    # Only show these options for custom criteria mode
    if strategy_option != "Value & Momentum Strategy":
        if price_sma_option != "None":
            sma_period = st.sidebar.selectbox(
                "SMA Period:",
                [20, 50, 200],
                key="scanner_sma_period"
            )

            if price_sma_option == "Price Above SMA":
                selected_criteria["price_above_sma"] = sma_period
            else:
                selected_criteria["price_below_sma"] = sma_period

    # Only show custom criteria if not using Value & Momentum Strategy
    if strategy_option != "Value & Momentum Strategy":
        # RSI Conditions
        rsi_option = st.sidebar.selectbox(
            "RSI Condition:",
            ["None", "Overbought (RSI > 70)", "Oversold (RSI < 30)"],
            key="scanner_rsi"
        )

        if rsi_option == "Overbought (RSI > 70)":
            selected_criteria["rsi_overbought"] = True
        elif rsi_option == "Oversold (RSI < 30)":
            selected_criteria["rsi_oversold"] = True

        # MACD Signals
        macd_option = st.sidebar.selectbox(
            "MACD Signal:",
            ["None", "Bullish Cross", "Bearish Cross"],
            key="scanner_macd"
        )

        if macd_option == "Bullish Cross":
            selected_criteria["macd_bullish"] = True
        elif macd_option == "Bearish Cross":
            selected_criteria["macd_bearish"] = True

        # Price near 52-week high/low
        price_level_option = st.sidebar.selectbox(
            "Price Level:",
            ["None", "Near 52-Week High", "Near 52-Week Low"],
            key="scanner_price_level"
        )

        if price_level_option == "Near 52-Week High":
            selected_criteria["price_near_52w_high"] = True
        elif price_level_option == "Near 52-Week Low":
            selected_criteria["price_near_52w_low"] = True

        # Fundamental Criteria
        st.sidebar.markdown("**Fundamental Criteria**")

        # P/E Ratio
        pe_option = st.sidebar.selectbox(
            "P/E Ratio:",
            ["None", "Below Value", "Above Value"],
            key="scanner_pe"
        )

        if pe_option == "Below Value":
            pe_value = st.sidebar.slider(
                "P/E Below:",
                min_value=1.0,
                max_value=30.0,
                value=15.0,
                step=0.5,
                key="scanner_pe_below"
            )
            selected_criteria["pe_below"] = pe_value
        elif pe_option == "Above Value":
            pe_value = st.sidebar.slider(
                "P/E Above:",
                min_value=1.0,
                max_value=50.0,
                value=20.0,
                step=0.5,
                key="scanner_pe_above"
            )
            selected_criteria["pe_above"] = pe_value

        # Profit Margin
        profit_margin_option = st.sidebar.checkbox(
            "Minimum Profit Margin",
            key="scanner_profit_margin_check"
        )

        if profit_margin_option:
            profit_margin_value = st.sidebar.slider(
                "Profit Margin Above (%):",
                min_value=0.0,
                max_value=30.0,
                value=10.0,
                step=0.5,
                key="scanner_profit_margin"
            )
            selected_criteria["profit_margin_above"] = profit_margin_value / 100

        # Revenue Growth
        revenue_growth_option = st.sidebar.checkbox(
            "Minimum Revenue Growth",
            key="scanner_revenue_growth_check"
        )

        if revenue_growth_option:
            revenue_growth_value = st.sidebar.slider(
                "Revenue Growth Above (%):",
                min_value=0.0,
                max_value=50.0,
                value=5.0,
                step=0.5,
                key="scanner_revenue_growth"
            )
            selected_criteria["revenue_growth_above"] = revenue_growth_value / 100

    # Auto-run on first load for Value & Momentum Strategy
    if 'scanner_auto_run' not in st.session_state and strategy_option == "Value & Momentum Strategy":
        # Set auto-run flag to avoid running again
        st.session_state.scanner_auto_run = True

        # Execute scan with Value & Momentum Strategy
        with st.spinner("Running Value & Momentum Strategy scan..."):
            only_watchlist = scan_scope == "Watchlist Only"
            results = scan_stocks(selected_criteria, only_watchlist)

            if results:
                # Store results in session state
                st.session_state.scanner_results = results

    # Run Scanner button
    run_scanner = st.sidebar.button("Run Scanner")

    # Checking if scanner results exist
    has_results = False
    if hasattr(st.session_state, 'scanner_results') and st.session_state.scanner_results:
        has_results = True

    # Run scanner logic
    if run_scanner:
        if not selected_criteria:
            st.warning("Please select at least one criterion")
        else:
            # Show criteria summary
            st.subheader("Scanning with the following criteria:")

            criteria_list = []

            for criterion, value in selected_criteria.items():
                display_name = SCANNER_CRITERIA.get(
                    criterion, criterion.replace('_', ' ').title())

                if isinstance(value, bool):
                    criteria_list.append(f"- {display_name}")
                else:
                    criteria_list.append(f"- {display_name}: {value}")

            for item in criteria_list:
                st.write(item)

            # Run the scanner with progress indicator
            with st.spinner("Scanning stocks..."):
                only_watchlist = scan_scope == "Watchlist Only"
                results = scan_stocks(selected_criteria, only_watchlist)

                if results:
                    st.session_state.scanner_results = results
                    has_results = True

    # Display results with clickable icons
    if has_results:
        results = st.session_state.scanner_results
        st.success(f"✅ Found {len(results)} matching stocks")

        # NEW: Render results with clickable watchlist icons
        render_scanner_results_with_icons(results)

        # Traditional dataframe view as backup
        with st.expander("📊 Traditional Table View", expanded=False):
            # Convert results to DataFrame for traditional view
            results_df = pd.DataFrame(results)

            # Format columns for display
            display_df = results_df.copy()

            # Format numeric columns
            if 'pe_ratio' in display_df:
                display_df['pe_ratio'] = display_df['pe_ratio'].apply(
                    lambda x: f"{x:.2f}" if pd.notna(x) else "N/A"
                )

            if 'profit_margin' in display_df:
                display_df['profit_margin'] = display_df['profit_margin'].apply(
                    lambda x: f"{x:.2%}" if pd.notna(x) else "N/A"
                )

            if 'revenue_growth' in display_df:
                display_df['revenue_growth'] = display_df['revenue_growth'].apply(
                    lambda x: f"{x:.2%}" if pd.notna(x) else "N/A"
                )

            if 'last_price' in display_df:
                display_df['last_price'] = display_df['last_price'].apply(
                    lambda x: f"{x:.2f}" if pd.notna(x) else "N/A"
                )

            if 'signal_strength' in display_df:
                display_df['signal_strength'] = display_df['signal_strength'].apply(
                    lambda x: f"{x*100:.1f}%" if pd.notna(x) else "N/A"
                )

            # Value & Momentum Strategy specific formatting
            if strategy_option == "Value & Momentum Strategy":
                # Format Tech Score as percentage
                if 'tech_score' in display_df:
                    display_df['tech_score'] = display_df['tech_score'].apply(
                        lambda x: f"{x:.0f}/100" if pd.notna(x) else "N/A"
                    )

                # Format boolean columns with symbols for better readability
                boolean_columns = ['above_ma40', 'above_ma4', 'rsi_above_50',
                                   'near_52w_high', 'is_profitable', 'reasonable_pe', 'fundamental_pass']
                for col in boolean_columns:
                    if col in display_df:
                        display_df[col] = display_df[col].apply(
                            lambda x: "✓" if x is True else "✗" if x is False else "—"
                        )

                # Format the Value & Momentum Signal with color highlighting
                if 'value_momentum_signal' in display_df:
                    display_df['value_momentum_signal'] = display_df['value_momentum_signal'].apply(
                        lambda x: x.upper() if pd.notna(x) else "N/A"
                    )

            # Display the dataframe
            st.dataframe(display_df, use_container_width=True, hide_index=True)

        # Download button for results
        if not results_df.empty:
            csv = results_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Results as CSV",
                data=csv,
                file_name="stock_scanner_results.csv",
                mime="text/csv"
            )

    elif run_scanner and not has_results:
        st.info("No stocks match the selected criteria. Try adjusting your criteria.")

    elif not has_results:
        # Show instructions and example image
        st.info(
            "Configure your scan criteria using the sidebar, then click 'Run Scanner'")

        # Explanation of scanner modes
        st.subheader("Scanner Modes")

        # Value & Momentum Strategy
        st.markdown("**Value & Momentum Strategy**")
        st.markdown("""
        This strategy combines technical momentum with fundamental quality to find stocks that are both trending up 
        and fundamentally sound. The approach avoids both "value traps" (cheap stocks getting cheaper) 
        and momentum chasing without fundamental backing.
        
        **Key components:**
        1. **Primary Trend**: Uses the 40-week moving average (MA40) as the primary trend indicator
        2. **Short-Term Momentum**: Uses the 4-week moving average (MA4) for recent price action
        3. **RSI Momentum**: Measures the strength of the price movement (RSI > 50 is bullish)
        4. **Price Patterns**: Checks for higher lows and proximity to 52-week high
        5. **Fundamental Quality**: Verifies the company is profitable with reasonable valuation
        
        **Signal Generation:**
        - **BUY**: Tech Score ≥ 70 AND passes fundamental check
        - **SELL**: Tech Score < 40 OR below MA40 (primary trend negative)
        - **HOLD**: Everything in between
        """)

        # Custom Criteria mode
        st.subheader("Custom Criteria Mode")

        # Technical criteria
        st.markdown("**Technical Criteria**")
        st.markdown(
            "- **Price vs. SMA**: Find stocks trading above or below their Simple Moving Averages")
        st.markdown(
            "- **RSI Condition**: Identify overbought or oversold stocks based on Relative Strength Index")
        st.markdown(
            "- **MACD Signal**: Detect stocks with MACD bullish or bearish crossovers")
        st.markdown(
            "- **Price Level**: Find stocks trading near their 52-week highs or lows")

        # Fundamental criteria
        st.markdown("**Fundamental Criteria**")
        st.markdown(
            "- **P/E Ratio**: Filter stocks by their Price-to-Earnings ratio")
        st.markdown(
            "- **Profit Margin**: Find stocks with profit margins above a minimum threshold")
        st.markdown(
            "- **Revenue Growth**: Identify stocks with strong revenue growth")
