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
        ["Watchlist Only", "All Available Stocks"],
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
    
    # Technical Criteria
    st.sidebar.markdown("**Technical Criteria**")
    
    # Price vs. SMA
    price_sma_option = st.sidebar.selectbox(
        "Price vs. SMA:",
        ["None", "Price Above SMA", "Price Below SMA"],
        key="scanner_price_sma"
    )
    
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
    
    # Run Scanner button
    if st.sidebar.button("Run Scanner"):
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
            
            # Display results
            if results:
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
                
                # Rename columns for display
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
                
                display_df = display_df.rename(columns=column_mapping)
                
                # Select columns to display
                columns_to_display = [
                    'Ticker', 'Price', 'Technical', 'Signal Strength', 
                    'Fundamentals', 'P/E Ratio', 'Profit Margin', 'Revenue Growth'
                ]
                
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
            else:
                st.info("No stocks match the selected criteria. Try adjusting your criteria.")
    else:
        # Show instructions and example image
        st.info("Configure your scan criteria using the sidebar, then click 'Run Scanner'")
        
        # Example image
        st.image("https://pixabay.com/get/g17b2df581a46700f967a126ece31122f04b28850686d0bf1f1722432c1a2acc7bfc9f5ab3f539f95192aee39c2ea2e6927b3da8f62ddfc5b5b5f91c2d05d46fc_1280.jpg", 
                caption="Stock Scanner helps you find stocks matching your criteria")
        
        # Explanation of criteria
        st.subheader("Available Criteria")
        
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
