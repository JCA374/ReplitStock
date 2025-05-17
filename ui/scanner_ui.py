import streamlit as st
import pandas as pd
import numpy as np
from data.db_manager import get_watchlist, get_all_cached_stocks
from analysis.scanner import scan_stocks
from config import SCANNER_CRITERIA

def display_scanner():
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
                display_name = SCANNER_CRITERIA.get(criterion, criterion.replace('_', ' ').title())
                
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
    
    # Display results
    if has_results:
        results = st.session_state.scanner_results
        st.subheader(f"Found {len(results)} matches")
        
        # Convert results to DataFrame
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
            boolean_columns = ['above_ma40', 'above_ma4', 'rsi_above_50', 'near_52w_high', 'is_profitable', 'reasonable_pe', 'fundamental_pass']
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
                
        # Rename columns for display
        if strategy_option == "Value & Momentum Strategy":
            # Special column mapping for Value & Momentum Strategy
            column_mapping = {
                'ticker': 'Ticker',
                'last_price': 'Price',
                'tech_score': 'Tech Score',
                'pe_ratio': 'P/E Ratio',
                'profit_margin': 'Profit Margin',
                'revenue_growth': 'Revenue Growth',
                'above_ma40': 'Above MA40',
                'above_ma4': 'Above MA4',
                'rsi_above_50': 'RSI > 50',
                'near_52w_high': 'Near 52w High',
                'is_profitable': 'Profitable',
                'reasonable_pe': 'Good P/E',
                'fundamental_pass': 'Fund. Pass',
                'value_momentum_signal': 'Signal'
            }
            
            # Select columns for Value & Momentum Strategy display
            columns_to_display = [
                'Ticker', 'Price', 'Signal', 'Tech Score', 
                'Above MA40', 'RSI > 50', 'Near 52w High', 'Profitable',
                'P/E Ratio', 'Profit Margin', 'Revenue Growth'
            ]
        else:
            # Regular column mapping for custom criteria
            column_mapping = {
                'ticker': 'Ticker',
                'last_price': 'Price',
                'pe_ratio': 'P/E Ratio',
                'profit_margin': 'Profit Margin',
                'revenue_growth': 'Revenue Growth',
                'technical_signal': 'Technical',
                'signal_strength': 'Signal Strength',
                'fundamental_status': 'Fundamentals'
            }
            
            # Select columns for regular display
            columns_to_display = [
                'Ticker', 'Price', 'Technical', 'Signal Strength', 
                'Fundamentals', 'P/E Ratio', 'Profit Margin', 'Revenue Growth'
            ]
        
        display_df = display_df.rename(columns=column_mapping)
        
        # Filter to columns that actually exist in the dataframe
        display_df = display_df[[col for col in columns_to_display if col in display_df.columns]]
        
        # Capitalize status text
        if 'Technical' in display_df:
            display_df['Technical'] = display_df['Technical'].str.capitalize()
        
        if 'Fundamentals' in display_df:
            display_df['Fundamentals'] = display_df['Fundamentals'].str.capitalize()
        
        # Display the results
        st.dataframe(display_df, hide_index=True, use_container_width=True)
        
        # Download button for results
        csv = display_df.to_csv(index=False)
        st.download_button(
            label="Download Results as CSV",
            data=csv,
            file_name="stock_scanner_results.csv",
            mime="text/csv"
        )
        
    elif run_scanner and not has_results:
        st.info("No stocks match the selected criteria. Try adjusting your criteria.")
        
    elif not has_results:
        # Show instructions and example image
        st.info("Configure your scan criteria using the sidebar, then click 'Run Scanner'")
        
        # Use a more reliable image source
        st.image("https://images.pexels.com/photos/6770610/pexels-photo-6770610.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750", 
                caption="Stock Scanner helps you find stocks matching your criteria")
        
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
        st.markdown("- **Price vs. SMA**: Find stocks trading above or below their Simple Moving Averages")
        st.markdown("- **RSI Condition**: Identify overbought or oversold stocks based on Relative Strength Index")
        st.markdown("- **MACD Signal**: Detect stocks with MACD bullish or bearish crossovers")
        st.markdown("- **Price Level**: Find stocks trading near their 52-week highs or lows")
        
        # Fundamental criteria
        st.markdown("**Fundamental Criteria**")
        st.markdown("- **P/E Ratio**: Filter stocks by their Price-to-Earnings ratio")
        st.markdown("- **Profit Margin**: Find stocks with profit margins above a minimum threshold")
        st.markdown("- **Revenue Growth**: Identify stocks with strong revenue growth")