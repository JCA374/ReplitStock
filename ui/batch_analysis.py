import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data.stock_data import StockDataFetcher
from data.db_manager import get_watchlist
from analysis.technical import calculate_all_indicators, generate_technical_signals
from analysis.fundamental import analyze_fundamentals
from utils.ticker_mapping import normalize_ticker
from config import TIMEFRAMES, PERIOD_OPTIONS
from helpers import create_results_table

def display_batch_analysis():
    st.header("Batch Analysis")
    st.write("Analyze multiple stocks at once to compare their technical and fundamental indicators.")
    
    # Access the shared strategy object from session state
    strategy = st.session_state.strategy
    
    # Get watchlist for quick selection
    watchlist = get_watchlist()
    watchlist_tickers = [item['ticker'] for item in watchlist]
    
    # Input methods for batch analysis
    st.sidebar.header("Batch Analysis Settings")
    
    analysis_mode = st.sidebar.radio(
        "Analysis Mode:",
        ["All Watchlist Stocks", "All Small Cap", "All Mid Cap", "All Large Cap", "Selected Stocks"],
        key="batch_analysis_mode"
    )
    
    selected_tickers = []
    
    if analysis_mode == "All Watchlist Stocks":
        if not watchlist:
            st.warning("Your watchlist is empty. Please add stocks to your watchlist or use another mode.")
        else:
            selected_tickers = watchlist_tickers
            st.success(f"Analyzing all {len(selected_tickers)} stocks in your watchlist")
    elif analysis_mode == "All Small Cap":
        try:
            small_cap_df = pd.read_csv('csv/updated_small.csv')
            small_cap_tickers = small_cap_df['YahooTicker'].tolist()
            selected_tickers = small_cap_tickers
            st.success(f"Analyzing all {len(selected_tickers)} stocks from Small Cap list")
        except Exception as e:
            st.error(f"Failed to load Small Cap CSV file: {str(e)}")
    elif analysis_mode == "All Mid Cap":
        try:
            mid_cap_df = pd.read_csv('csv/updated_mid.csv')
            mid_cap_tickers = mid_cap_df['YahooTicker'].tolist()
            selected_tickers = mid_cap_tickers
            st.success(f"Analyzing all {len(selected_tickers)} stocks from Mid Cap list")
        except Exception as e:
            st.error(f"Failed to load Mid Cap CSV file: {str(e)}")
    elif analysis_mode == "All Large Cap":
        try:
            large_cap_df = pd.read_csv('csv/updated_large.csv')
            large_cap_tickers = large_cap_df['YahooTicker'].tolist()
            selected_tickers = large_cap_tickers
            st.success(f"Analyzing all {len(selected_tickers)} stocks from Large Cap list")
        except Exception as e:
            st.error(f"Failed to load Large Cap CSV file: {str(e)}")
    else:  # Selected Stocks mode
        input_method = st.radio(
            "Select stocks from:",
            ["Watchlist", "Small Cap CSV", "Mid Cap CSV", "Large Cap CSV", "Manual Entry"],
            key="batch_input_method"
        )
        
        if input_method == "Watchlist":
            if not watchlist:
                st.warning("Your watchlist is empty. Please add stocks to your watchlist or use another option.")
            else:
                selected_tickers = st.multiselect(
                    "Select stocks from your watchlist:",
                    options=watchlist_tickers,
                    key="batch_watchlist_select"
                )
        elif input_method == "Small Cap CSV":
            # Load small cap tickers from CSV
            try:
                small_cap_df = pd.read_csv('csv/updated_small.csv')
                small_cap_tickers = small_cap_df['YahooTicker'].tolist()
                selected_tickers = st.multiselect(
                    "Select stocks from Small Cap list:",
                    options=small_cap_tickers,
                    key="batch_small_cap_select"
                )
            except Exception as e:
                st.error(f"Failed to load Small Cap CSV file: {str(e)}")
                selected_tickers = []
        elif input_method == "Mid Cap CSV":
            # Load mid cap tickers from CSV
            try:
                mid_cap_df = pd.read_csv('csv/updated_mid.csv')
                mid_cap_tickers = mid_cap_df['YahooTicker'].tolist()
                selected_tickers = st.multiselect(
                    "Select stocks from Mid Cap list:",
                    options=mid_cap_tickers,
                    key="batch_mid_cap_select"
                )
            except Exception as e:
                st.error(f"Failed to load Mid Cap CSV file: {str(e)}")
                selected_tickers = []
        elif input_method == "Large Cap CSV":
            # Load large cap tickers from CSV
            try:
                large_cap_df = pd.read_csv('csv/updated_large.csv')
                large_cap_tickers = large_cap_df['YahooTicker'].tolist()
                selected_tickers = st.multiselect(
                    "Select stocks from Large Cap list:",
                    options=large_cap_tickers,
                    key="batch_large_cap_select"
                )
            except Exception as e:
                st.error(f"Failed to load Large Cap CSV file: {str(e)}")
                selected_tickers = []
        else:  # Manual Entry
            ticker_input = st.text_input(
                "Enter ticker symbols (comma-separated):",
                key="batch_manual_tickers"
            )
            
            if ticker_input:
                # Parse and normalize tickers
                raw_tickers = [t.strip() for t in ticker_input.split(",")]
                selected_tickers = [normalize_ticker(t) for t in raw_tickers if t]
    
    # Analysis parameters
    col1, col2 = st.columns(2)
    
    with col1:
        timeframe = st.selectbox(
            "Timeframe:",
            options=list(TIMEFRAMES.keys()),
            key="batch_timeframe"
        )
    
    with col2:
        period = st.selectbox(
            "Period:",
            options=list(PERIOD_OPTIONS.keys()),
            key="batch_period"
        )
    
    # Convert selected options to API format
    timeframe_value = TIMEFRAMES[timeframe]
    period_value = PERIOD_OPTIONS[period]
    
    # Function to run analysis for selected tickers using strategy's batch_analyze
    def run_analysis(tickers):
        # Create a progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Define callback for progress updates
        def update_progress(progress, text):
            progress_bar.progress(progress)
            status_text.text(text)
        
        # Use strategy's batch_analyze method (same as single stock analyzer)
        results = strategy.batch_analyze(tickers, update_progress)
        
        # Store the results in session state for potential reuse
        st.session_state.analysis_results = results
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
        return results
    
    # Analysis execution logic
    results = None
    
    # Always require a button press before running
    run_button = st.button("Run Batch Analysis", type="primary")
    
    if run_button and selected_tickers:
        with st.spinner("Analyzing selected stocks..."):
            results = run_analysis(selected_tickers)
    
    # Display results
    if results:
        # Filter successful analyses (no errors)
        success_results = [r for r in results if "error" not in r]
        error_results = [r for r in results if "error" in r]
        
        if success_results:
            # Create a DataFrame using the helper function from attached_assets
            results_df = create_results_table(results)
            
            # Add view options
            view_mode = st.radio("Visningsläge", 
                ["Tabellvy", "Kortvy"],
                horizontal=True,
                key="batch_view_mode")
            
            # Filter options
            st.subheader("Filtrera resultat")
            filter_col1, filter_col2, filter_col3 = st.columns(3)
            
            with filter_col1:
                signal_filter = st.multiselect(
                    "Signal",
                    ["KÖP", "HÅLL", "SÄLJ"],
                    default=["KÖP", "HÅLL", "SÄLJ"],
                    key="batch_signal_filter"
                )
            
            with filter_col2:
                ma40_filter = st.checkbox(
                    "Bara aktier över MA40", 
                    value=False,
                    key="batch_ma40_filter"
                )
            
            with filter_col3:
                tech_score_min = st.slider(
                    "Min Tech Score", 
                    0, 100, 0,
                    key="batch_tech_score_filter"
                )
            
            # Add data source filter
            data_source_filter = st.multiselect(
                "Datakälla",
                ["yahoo", "alphavantage", "local"],
                default=["yahoo", "alphavantage", "local"],
                key="batch_source_filter"
            )
            
            # Apply filters to DataFrame
            filtered_df = results_df.copy()
            
            if signal_filter and "Signal" in filtered_df.columns:
                filtered_df = filtered_df[filtered_df["Signal"].isin(signal_filter)]
            
            if ma40_filter and "Över MA40" in filtered_df.columns:
                filtered_df = filtered_df[filtered_df["Över MA40"] == "Ja"]
            
            if "Tech Score" in filtered_df.columns:
                filtered_df = filtered_df[filtered_df["Tech Score"] >= tech_score_min]
            
            if data_source_filter and "Data Source" in filtered_df.columns:
                filtered_df = filtered_df[filtered_df["Data Source"].isin(data_source_filter)]
            
            # Sort by tech score (high to low)
            if "Tech Score" in filtered_df.columns:
                filtered_df = filtered_df.sort_values("Tech Score", ascending=False)
            
            st.subheader("Analys Resultat")
            
            # Display based on view mode
            if not filtered_df.empty:
                if view_mode == "Tabellvy":
                    # Table view
                    st.dataframe(
                        filtered_df,
                        column_config={
                            "Signal": st.column_config.Column(
                                "Signal",
                                help="Köp, Sälj eller Håll signal baserat på strategin",
                                width="small"
                            ),
                            "Tech Score": st.column_config.ProgressColumn(
                                "Tech Score",
                                help="Tekniskt score 0-100",
                                min_value=0,
                                max_value=100,
                                format="%d"
                            ) if "Tech Score" in filtered_df.columns else None,
                            "Data Source": st.column_config.Column(
                                "Data Source",
                                help="Källa för aktiedata"
                            )
                        },
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    # Card view - create a grid layout for cards
                    num_cards = len(filtered_df)
                    cards_per_row = 3
                    
                    # Calculate number of rows needed
                    num_rows = (num_cards + cards_per_row - 1) // cards_per_row
                    
                    # Create a list to hold all card data
                    all_card_data = []
                    
                    # Prepare data for each card
                    for _, row in filtered_df.iterrows():
                        ticker = row["Ticker"] if "Ticker" in row else ""
                        
                        # Find the full analysis data for this ticker
                        full_analysis = next(
                            (r for r in results if r.get("ticker") == ticker and "error" not in r),
                            None
                        )
                        
                        if full_analysis:
                            all_card_data.append({
                                "ticker": ticker,
                                "name": full_analysis.get("name", ticker),
                                "price": full_analysis.get("price", 0),
                                "signal": row.get("Signal", ""),
                                "tech_score": row.get("Tech Score", 0),
                                "data_source": full_analysis.get("data_source", "unknown"),
                                "rsi": full_analysis.get("rsi", None),
                                "above_ma40": full_analysis.get("above_ma40", False),
                                "full_analysis": full_analysis
                            })
                    
                    # Display cards in a grid
                    for row_idx in range(num_rows):
                        cols = st.columns(cards_per_row)
                        for col_idx in range(cards_per_row):
                            card_idx = row_idx * cards_per_row + col_idx
                            if card_idx < len(all_card_data):
                                card = all_card_data[card_idx]
                                with cols[col_idx]:
                                    # Determine signal color
                                    signal_color = "green" if card["signal"] == "KÖP" else "red" if card["signal"] == "SÄLJ" else "orange"
                                    
                                    # Create card container with border
                                    st.markdown(f"""
                                    <div style="border:1px solid #ddd; border-radius:5px; padding:10px; margin-bottom:10px;">
                                        <h3>{card["name"]} ({card["ticker"]})</h3>
                                        <p>Pris: {card["price"]:.2f} SEK</p>
                                        <p style="color:{signal_color}; font-weight:bold">Signal: {card["signal"]}</p>
                                        <p>Tech Score: {card["tech_score"]}</p>
                                        <p>RSI: {card["rsi"]:.1f if card["rsi"] is not None else "N/A"}</p>
                                        <p>MA40: {"Över" if card["above_ma40"] else "Under"}</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    # Add a button to view detailed analysis
                                    if st.button(f"Visa detaljer", key=f"view_{card['ticker']}"):
                                        st.session_state.selected_batch_analysis_ticker = card["ticker"]
                                        st.rerun()
            
            # Handle selected ticker for detailed analysis
            if 'selected_batch_analysis_ticker' in st.session_state:
                selected_ticker = st.session_state.selected_batch_analysis_ticker
                # Clear from session state to avoid repeated display on rerun
                del st.session_state.selected_batch_analysis_ticker
            else:
                # Add an option to select a ticker for detailed view
                st.subheader("Välj aktie för detaljerad analys")
                ticker_options = filtered_df["Ticker"].tolist() if "Ticker" in filtered_df.columns else []
                selected_ticker = st.selectbox("Aktie", options=ticker_options, key="batch_detailed_ticker")
            
            # Show detailed analysis if a ticker is selected
            if selected_ticker:
                # Find full analysis for selected ticker
                selected_analysis = next(
                    (r for r in results if r.get("ticker") == selected_ticker and "error" not in r),
                    None
                )
                
                if selected_analysis:
                    st.markdown("---")
                    st.subheader(f"{selected_analysis['name']} ({selected_analysis['ticker']}) - Detaljerad Analys")
                    
                    # Show data source indicator
                    source = selected_analysis.get("data_source", "unknown")
                    source_display = {
                        "yahoo": "Yahoo Finance",
                        "alphavantage": "Alpha Vantage", 
                        "local": "Local Cache",
                        "unknown": "Unknown Source"
                    }.get(source, source)
                    
                    source_color = {
                        "yahoo": "#0077b6",  # Blue for Yahoo
                        "alphavantage": "#ff9e00",  # Orange for Alpha Vantage
                        "local": "#2e8b57",  # Green for local cache
                        "unknown": "#6c757d"  # Gray for unknown
                    }.get(source, "#6c757d")
                    
                    st.markdown(
                        f"<div style='margin-bottom:15px;'><span style='background-color:{source_color}; color:white; padding:3px 8px; border-radius:10px; font-size:0.8em'>Data source: {source_display}</span></div>",
                        unsafe_allow_html=True
                    )
                    
                    # Create tabs for detailed view
                    detail_tab1, detail_tab2, detail_tab3 = st.tabs(["Graf", "Fundamentala Data", "Tekniska Indikatorer"])
                    
                    with detail_tab1:
                        # Display chart using the strategy plot function
                        fig = strategy.plot_analysis(selected_analysis)
                        if fig:
                            st.pyplot(fig)
                    
                    with detail_tab2:
                        # Fundamental data with improved formatting
                        col_fund1, col_fund2 = st.columns(2)
                        
                        with col_fund1:
                            st.subheader("Lönsamhet")
                            profitable = selected_analysis.get('is_profitable', False)
                            st.markdown(f"""
                            <div style="background-color:{'#d4edda' if profitable else '#f8d7da'}; 
                                       color:{'#155724' if profitable else '#721c24'}; 
                                       padding:10px; border-radius:5px; margin-bottom:10px;">
                                <b>Lönsamt bolag:</b> {'Ja' if profitable else 'Nej'}
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if selected_analysis.get('pe_ratio') is not None:
                                st.write(f"P/E-tal: {selected_analysis.get('pe_ratio', 0):.2f}")
                            else:
                                st.write("P/E-tal: Data saknas")
                        
                        with col_fund2:
                            st.subheader("Tillväxt")
                            if selected_analysis.get('revenue_growth') is not None:
                                growth_val = selected_analysis.get('revenue_growth', 0)*100
                                growth_color = "#d4edda" if growth_val > 0 else "#f8d7da"
                                growth_text_color = "#155724" if growth_val > 0 else "#721c24"
                                
                                st.markdown(f"""
                                <div style="background-color:{growth_color}; 
                                           color:{growth_text_color}; 
                                           padding:10px; border-radius:5px; margin-bottom:10px;">
                                    <b>Omsättningstillväxt:</b> {growth_val:.1f}%
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.write("Omsättningstillväxt: Data saknas")
                            
                            if selected_analysis.get('profit_margin') is not None:
                                margin_val = selected_analysis.get('profit_margin', 0)*100
                                st.write(f"Vinstmarginal: {margin_val:.1f}%")
                            else:
                                st.write("Vinstmarginal: Data saknas")
                    
                    with detail_tab3:
                        # Technical indicators with improved formatting
                        tech_indicators = [
                            {"name": "Pris över MA40 (40-veckor)", "value": selected_analysis.get('above_ma40', False)},
                            {"name": "Pris över MA4 (4-veckor)", "value": selected_analysis.get('above_ma4', False)},
                            {"name": "RSI över 50", "value": selected_analysis.get('rsi_above_50', False)},
                            {"name": "Högre bottnar", "value": selected_analysis.get('higher_lows', False)},
                            {"name": "Nära 52-veckors högsta", "value": selected_analysis.get('near_52w_high', False)},
                            {"name": "Breakout från konsolidering", "value": selected_analysis.get('breakout', False)}
                        ]
                        
                        # Create grid layout for technical indicators
                        indicator_cols = st.columns(2)
                        
                        for i, indicator in enumerate(tech_indicators):
                            col_idx = i % 2
                            with indicator_cols[col_idx]:
                                bg_color = "#d4edda" if indicator["value"] else "#f8d7da"
                                text_color = "#155724" if indicator["value"] else "#721c24"
                                st.markdown(f"""
                                <div style="background-color:{bg_color}; 
                                           color:{text_color}; 
                                           padding:10px; border-radius:5px; margin-bottom:10px;">
                                    <b>{indicator["name"]}:</b> {'Ja' if indicator["value"] else 'Nej'}
                                </div>
                                """, unsafe_allow_html=True)
                        
                        # Show RSI value
                        if selected_analysis.get('rsi') is not None:
                            rsi_val = selected_analysis.get('rsi')
                            st.write(f"RSI Värde: {rsi_val:.1f}")
                            
                            # RSI interpretation
                            if rsi_val > 70:
                                st.markdown("<div style='color:#721c24'>RSI över 70 - Möjligt överköpt läge</div>", unsafe_allow_html=True)
                            elif rsi_val < 30:
                                st.markdown("<div style='color:#155724'>RSI under 30 - Möjligt översålt läge</div>", unsafe_allow_html=True)
            
            # Display failed analyses if any exist
            if error_results:
                with st.expander(f"Aktier som inte kunde analyseras ({len(error_results)} st)"):
                    for error in error_results:
                        ticker = error.get("ticker", "Unknown")
                        error_msg = error.get("error", "Unknown error")
                        st.warning(f"**{ticker}**: {error_msg}")
                        
            # Technical comparison (not shown in detailed view)
            if not filtered_df.empty:
                st.subheader("Teknisk Jämförelse")
                # Show technical comparison chart if we have tech scores
                if "Tech Score" in filtered_df.columns:
                    # Create horizontal bar chart for comparing tech scores
                    chart_data = filtered_df.copy()
                    
                    fig = go.Figure()
                    
                    # Add bars for each stock
                    fig.add_trace(go.Bar(
                        y=chart_data["Ticker"] if "Ticker" in chart_data.columns else [],
                        x=chart_data["Tech Score"] if "Tech Score" in chart_data.columns else [],
                        orientation='h',
                        marker_color='blue',
                        text=chart_data["Tech Score"] if "Tech Score" in chart_data.columns else [],
                        textposition='auto'
                    ))
                    
                    # Update layout
                    fig.update_layout(
                        title="Teknisk Score (0-100)",
                        xaxis_title="Score",
                        yaxis_title="Ticker",
                        height=max(300, len(chart_data) * 30),
                        margin=dict(l=0, r=0, t=40, b=0)
                    )
                    
                    # Display chart
                    st.plotly_chart(fig, use_container_width=True)
                
                # Add reminder about data sources
                st.info("Alla aktier i batch-analysen använder samma datakälla som individuell aktie-analys, vilket ger konsistenta resultat.")
                
                # Technical score chart
                st.subheader("Technical Score Comparison")
                
                # Prepare data for visualization
                if 'Tech Score' in filtered_df.columns:
                    chart_data = filtered_df[['Ticker', 'Tech Score']].copy()
                    chart_data['signal_color'] = filtered_df['Signal'].apply(
                        lambda x: 'green' if x == 'KÖP' else 'red' if x == 'SÄLJ' else 'orange'
                    )
                    
                    # Convert tech score to numeric (assuming format like "80/100")
                    chart_data['tech_score_value'] = chart_data['Tech Score'].apply(
                        lambda x: float(x.split('/')[0]) if isinstance(x, str) and '/' in x else 0
                    )
                    
                    # Create horizontal bar chart
                    fig = go.Figure()
                    
                    fig.add_trace(go.Bar(
                        y=chart_data['Ticker'],
                        x=chart_data['tech_score_value'],
                        orientation='h',
                        marker_color=chart_data['signal_color'],
                        text=chart_data['Tech Score'],
                        textposition='auto'
                    ))
                    
                    fig.update_layout(
                        title="Technical Score (0-100)",
                        xaxis_title="Score",
                        yaxis_title="Ticker",
                        height=max(300, len(chart_data) * 30),
                        margin=dict(l=0, r=0, t=40, b=0)
                    )
                    
                    # Add reference lines for score thresholds
                    fig.add_shape(
                        type="line",
                        x0=70,
                        y0=-1,
                        x1=70,
                        y1=len(chart_data),
                        line=dict(
                            color="green",
                            width=1,
                            dash="dash",
                        )
                    )
                    
                    fig.add_shape(
                        type="line",
                        x0=40,
                        y0=-1,
                        x1=40,
                        y1=len(chart_data),
                        line=dict(
                            color="red",
                            width=1,
                            dash="dash",
                        )
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Explanation of score thresholds
                    st.info("""
                    **Technical Score Interpretation:**
                    - **Above 70** (Green line): Strong technical strength - potential buy
                    - **40-70**: Moderate technical strength - monitor closely
                    - **Below 40** (Red line): Weak technical strength - potential sell/avoid
                    """)
            
            # Fundamental metrics table
            st.subheader("Fundamental Metrics")
            fund_cols = [
                'ticker', 'fundamental_status', 'pe_ratio',
                'profit_margin', 'revenue_growth'
            ]
            
            if all(col in results_df.columns for col in fund_cols):
                fund_df = results_df[fund_cols].copy()
                
                # Format columns
                fund_df['pe_ratio'] = fund_df['pe_ratio'].apply(
                    lambda x: f"{x:.2f}" if pd.notna(x) else "N/A"
                )
                fund_df['profit_margin'] = fund_df['profit_margin'].apply(
                    lambda x: f"{x:.2%}" if pd.notna(x) else "N/A"
                )
                fund_df['revenue_growth'] = fund_df['revenue_growth'].apply(
                    lambda x: f"{x:.2%}" if pd.notna(x) else "N/A"
                )
                fund_df['fundamental_status'] = fund_df['fundamental_status'].str.capitalize()
                
                # Rename columns for display
                fund_df.columns = [
                    'Ticker', 'Status', 'P/E Ratio',
                    'Profit Margin', 'Revenue Growth'
                ]
                
                st.subheader("Fundamental Metrics")
                st.dataframe(fund_df, hide_index=True, use_container_width=True)
                
                # P/E Ratio comparison chart
                pe_data = results_df[['ticker', 'pe_ratio']].dropna(subset=['pe_ratio']).copy()
                
                if not pe_data.empty:
                    # Sort by P/E ratio
                    pe_data = pe_data.sort_values('pe_ratio')
                    
                    # Create color based on P/E range
                    pe_data['color'] = pe_data['pe_ratio'].apply(
                        lambda x: 'green' if x < 15 else 'red' if x > 30 else 'orange'
                    )
                    
                    # Create bar chart
                    fig = go.Figure()
                    
                    fig.add_trace(go.Bar(
                        x=pe_data['ticker'],
                        y=pe_data['pe_ratio'],
                        marker_color=pe_data['color'],
                        text=pe_data['pe_ratio'].apply(lambda x: f"{x:.2f}"),
                        textposition='auto'
                    ))
                    
                    fig.update_layout(
                        title="P/E Ratio Comparison",
                        xaxis_title="Ticker",
                        yaxis_title="P/E Ratio",
                        height=400
                    )
                    
                    # Add reference lines for P/E thresholds
                    fig.add_shape(
                        type="line",
                        x0=-1,
                        y0=15,
                        x1=len(pe_data),
                        y1=15,
                        line=dict(
                            color="green",
                            width=1,
                            dash="dash",
                        )
                    )
                    
                    fig.add_shape(
                        type="line",
                        x0=-1,
                        y0=30,
                        x1=len(pe_data),
                        y1=30,
                        line=dict(
                            color="red",
                            width=1,
                            dash="dash",
                        )
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No P/E ratio data available for comparison")
                
                # Profit margin comparison chart
                margin_data = results_df[['ticker', 'profit_margin']].dropna(subset=['profit_margin']).copy()
                
                if not margin_data.empty:
                    # Sort by profit margin
                    margin_data = margin_data.sort_values('profit_margin', ascending=False)
                    
                    # Create color based on profit margin
                    margin_data['color'] = margin_data['profit_margin'].apply(
                        lambda x: 'red' if x < 0 else 'orange' if x < 0.1 else 'green'
                    )
                    
                    # Create bar chart
                    fig = go.Figure()
                    
                    fig.add_trace(go.Bar(
                        x=margin_data['ticker'],
                        y=margin_data['profit_margin'],
                        marker_color=margin_data['color'],
                        text=margin_data['profit_margin'].apply(lambda x: f"{x:.2%}"),
                        textposition='auto'
                    ))
                    
                    fig.update_layout(
                        title="Profit Margin Comparison",
                        xaxis_title="Ticker",
                        yaxis_title="Profit Margin",
                        height=400
                    )
                    
                    # Add reference line for profit margin threshold
                    fig.add_shape(
                        type="line",
                        x0=-1,
                        y0=0.1,
                        x1=len(margin_data),
                        y1=0.1,
                        line=dict(
                            color="green",
                            width=1,
                            dash="dash",
                        )
                    )
                    
                    fig.add_shape(
                        type="line",
                        x0=-1,
                        y0=0,
                        x1=len(margin_data),
                        y1=0,
                        line=dict(
                            color="red",
                            width=1,
                            dash="dash",
                        )
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No profit margin data available for comparison")
        
        # Display errors, if any
        if error_results:
            st.subheader("Errors")
            
            for error in error_results:
                st.error(f"Error analyzing {error['ticker']}: {error.get('message', 'Unknown error')}")
    
    # Add a new section to allow viewing historical analysis
    with st.expander("View Historical Analysis"):
        st.subheader("Previously Run Analyses")

        # Get data from the database
        from data.db_integration import get_analysis_results

        # Allow filtering by days
        days_filter = st.slider(
            "Show analyses from the last X days:",
            min_value=1,
            max_value=90,
            value=30
        )

        # Get historical results
        historical_results = get_analysis_results(days=days_filter)

        if historical_results:
            # Group by date
            from collections import defaultdict
            date_grouped = defaultdict(list)

            for result in historical_results:
                date_grouped[result["analysis_date"]].append(result)

            # Show dates as a selectbox
            dates = sorted(date_grouped.keys(), reverse=True)
            selected_date = st.selectbox("Select analysis date:", dates)

            if selected_date:
                # Show tickers analyzed on that date
                date_results = date_grouped[selected_date]
                st.write(
                    f"Found {len(date_results)} stocks analyzed on {selected_date}")

                # Convert to DataFrame for display
                import pandas as pd
                hist_df = pd.DataFrame(date_results)

                # Format for display
                display_df = hist_df[['ticker', 'price', 'signal',
                                    'tech_score', 'rsi_value', 'pe_ratio', 'data_source']].copy()
                display_df.columns = ['Ticker', 'Price', 'Signal',
                                    'Tech Score', 'RSI', 'P/E Ratio', 'Data Source']

                # Display the data
                st.dataframe(display_df, hide_index=True)

                # Option to load this analysis
                if st.button("Load this analysis"):
                    st.session_state.analysis_results = date_results
                    st.rerun()
        else:
            st.info("No historical analyses found in the database.")


    
