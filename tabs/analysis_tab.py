import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt


def render_analysis_tab():
    """Render the individual stock analysis tab"""
    # Access shared objects from session state
    strategy = st.session_state.strategy
    watchlist_manager = st.session_state.watchlist_manager

    # Check if we should analyze a ticker (triggered from sidebar)
    if 'analyze_ticker' in st.session_state:
        ticker = st.session_state.analyze_ticker
        # Clear the trigger so it doesn't re-analyze on every rerun
        del st.session_state.analyze_ticker

        # Run the analysis
        with st.spinner(f"Analyserar {ticker}..."):
            analyze_and_display_stock(ticker, strategy, watchlist_manager)
    else:
        # No analysis in progress, show instructions
        st.info("Använd sidofältet till vänster för att analysera en aktie.")
        
        # Add manual ticker input
        st.subheader("Manuell analys av aktie")
        manual_ticker = st.text_input("Ange aktiesymbol (t.ex. AAPL, VOLV-B.ST):", placeholder="Ticker")
        if st.button("Analysera", key="analyze_manual_ticker"):
            if manual_ticker:
                with st.spinner(f"Analyserar {manual_ticker}..."):
                    analyze_and_display_stock(manual_ticker, strategy, watchlist_manager)
            else:
                st.warning("Ange en aktiesymbol för att analysera.")
        
        st.divider()

        # Option to select from watchlist
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader("Eller välj en aktie från din watchlist")
        
        with col2:
            if st.button("✏️ Hantera Watchlists", key="manage_watchlists_button"):
                st.session_state.show_watchlist_manager = True
        
        # Show watchlist manager if requested
        if st.session_state.get('show_watchlist_manager', False):
            with st.expander("Watchlist Manager", expanded=True):
                # Create a new watchlist
                new_watchlist_name = st.text_input("Skapa ny watchlist:", key="new_watchlist_name")
                if st.button("Skapa Watchlist", key="create_watchlist_button"):
                    if new_watchlist_name:
                        if watchlist_manager.add_watchlist(new_watchlist_name):
                            st.success(f"Watchlist '{new_watchlist_name}' skapad!")
                            st.session_state.new_watchlist_name = ""  # Clear input
                        else:
                            st.error(f"Watchlist '{new_watchlist_name}' finns redan!")
                    else:
                        st.warning("Ange ett namn för watchlisten!")
                
                # Delete a watchlist
                all_wl = watchlist_manager.get_all_watchlists()
                wl_names = [w["name"] for w in all_wl]
                
                if len(wl_names) > 1:  # Don't allow deleting if only one watchlist
                    st.divider()
                    del_col1, del_col2 = st.columns([3, 1])
                    
                    with del_col1:
                        delete_index = st.selectbox(
                            "Välj watchlist att ta bort:",
                            range(len(wl_names)),
                            format_func=lambda i: wl_names[i],
                            key="delete_watchlist_select"
                        )
                    
                    with del_col2:
                        if st.button("Ta bort", key="delete_watchlist_button"):
                            if delete_index > 0:  # Don't delete the first (primary) watchlist
                                if watchlist_manager.delete_watchlist(delete_index):
                                    st.success(f"Watchlist '{wl_names[delete_index]}' borttagen!")
                                else:
                                    st.error("Kunde inte ta bort watchlisten!")
                            else:
                                st.error("Kan inte ta bort huvudwatchlisten!")
                
                # Add stocks to watchlists
                st.divider()
                st.subheader("Lägg till aktier i watchlist")
                
                # Select target watchlist
                target_wl_index = st.selectbox(
                    "Välj målwatchlist:",
                    range(len(wl_names)),
                    format_func=lambda i: wl_names[i],
                    key="target_watchlist_select"
                )
                
                # Add stock form
                add_col1, add_col2 = st.columns([3, 1])
                
                with add_col1:
                    add_ticker = st.text_input("Lägg till aktie (ticker):", 
                                         placeholder="ex. AAPL, VOLV-B.ST", 
                                         key="add_ticker_input")
                
                with add_col2:
                    if st.button("Lägg till", key="add_stock_button"):
                        if add_ticker:
                            if watchlist_manager.add_stock_to_watchlist(target_wl_index, add_ticker):
                                st.success(f"Lade till {add_ticker} i {wl_names[target_wl_index]}!")
                            else:
                                st.error(f"Kunde inte lägga till {add_ticker} (finns den redan?)")
                        else:
                            st.warning("Ange en ticker att lägga till!")
                
                # Remove stock from watchlist
                st.divider()
                st.subheader("Ta bort aktier från watchlist")
                
                # Select watchlist to remove from
                remove_wl_index = st.selectbox(
                    "Välj watchlist:",
                    range(len(wl_names)),
                    format_func=lambda i: wl_names[i],
                    key="remove_wl_select"
                )
                
                # Get stocks in the selected watchlist
                remove_wl = watchlist_manager.get_all_watchlists()[remove_wl_index]
                stocks_in_wl = remove_wl["stocks"]
                
                if stocks_in_wl:
                    # Show dropdown of stocks to remove
                    remove_ticker_index = st.selectbox(
                        "Välj aktie att ta bort:",
                        range(len(stocks_in_wl)),
                        format_func=lambda i: stocks_in_wl[i],
                        key="remove_ticker_select"
                    )
                    
                    if st.button("Ta bort aktie", key="remove_stock_button"):
                        ticker_to_remove = stocks_in_wl[remove_ticker_index]
                        if watchlist_manager.remove_stock_from_watchlist(remove_wl_index, ticker_to_remove):
                            st.success(f"Tog bort {ticker_to_remove} från {wl_names[remove_wl_index]}!")
                        else:
                            st.error(f"Kunde inte ta bort {ticker_to_remove}!")
                else:
                    st.info(f"Ingen aktie i watchlisten {wl_names[remove_wl_index]}.")
                
                # Close watchlist manager
                if st.button("Stäng", key="close_watchlist_manager"):
                    st.session_state.show_watchlist_manager = False
                    st.rerun()
        
        # Get all stocks from all watchlists
        all_watchlists = watchlist_manager.get_all_watchlists()
        
        # Handle the case where there might be no watchlists
        if not all_watchlists:
            st.warning("Inga watchlists hittades. Skapa en watchlist för att fortsätta.")
            return
            
        # First select which watchlist to use
        watchlist_names = [w["name"] for w in all_watchlists]
        selected_watchlist_index = st.selectbox(
            "Välj watchlist:",
            range(len(watchlist_names)), 
            format_func=lambda i: watchlist_names[i],
            key="analysis_watchlist_select"
        )
        
        # Get stocks from selected watchlist
        selected_watchlist = all_watchlists[selected_watchlist_index]
        stocks_in_watchlist = selected_watchlist["stocks"]
        
        if stocks_in_watchlist:
            # Format selection options
            selected_option = st.selectbox(
                "Välj aktie",
                options=[""] + stocks_in_watchlist
            )

            if selected_option:
                # The selected option is directly the ticker
                selected_ticker = selected_option

                if st.button("Analysera vald aktie"):
                    with st.spinner(f"Analyserar {selected_ticker}..."):
                        analyze_and_display_stock(
                            selected_ticker, strategy, watchlist_manager)
        else:
            st.warning(
                "Din watchlist är tom. Lägg till aktier för att kunna välja från listan.")


def analyze_and_display_stock(ticker, strategy, watchlist_manager):
    """Analyze a stock and display the results"""
    analysis = strategy.analyze_stock(ticker)

    if "error" in analysis and analysis["error"] is not None:
        st.error(f"Fel: {analysis['error']}")
        return

    # Display analysis results
    render_analysis_results(analysis, strategy, watchlist_manager)


def render_analysis_results(analysis, strategy, watchlist_manager):
    """Render the analysis results for a single stock"""
    # Visa sammanfattning
    signal_color = "green" if analysis["buy_signal"] else "red" if analysis["sell_signal"] else "orange"
    signal_text = "KÖP" if analysis["buy_signal"] else "SÄLJ" if analysis["sell_signal"] else "HÅLL"

    st.header(f"{analysis['name']} ({analysis['ticker']})")
    st.subheader(f"Pris: {analysis['price']:.2f} SEK")

    st.markdown(
        f"<h3 style='color:{signal_color}'>Signal: {signal_text}</h3>", unsafe_allow_html=True)

    # Add a data source indicator
    source = analysis.get("data_source", "unknown")
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

    # Show watchlist options - updated to allow adding to any watchlist
    st.subheader("Lägg till i watchlist")

    # Create a radio button to select which watchlist to add to
    all_watchlists = watchlist_manager.get_all_watchlists()
    watchlist_names = [w["name"] for w in all_watchlists]

    target_watchlist = st.radio(
        "Välj watchlist",
        options=range(len(watchlist_names)),
        format_func=lambda i: watchlist_names[i],
        horizontal=True
    )

    # Check if the stock already exists in the selected watchlist
    selected_watchlist = all_watchlists[target_watchlist]
    already_in_watchlist = analysis["ticker"] in selected_watchlist["stocks"]

    if already_in_watchlist:
        st.info(
            f"{analysis['ticker']} finns redan i {selected_watchlist['name']}")
    else:
        if st.button("Lägg till i watchlist"):
            if watchlist_manager.add_stock_to_watchlist(target_watchlist, analysis["ticker"]):
                st.success(
                    f"Lade till {analysis['ticker']} i {watchlist_names[target_watchlist]}")
            else:
                st.error("Kunde inte lägga till aktien")

    # Skapa flikar för detaljer
    tab2_1, tab2_2, tab2_3 = st.tabs(
        ["Översikt", "Fundamenta", "Teknisk Analys"])

    with tab2_1:
        # Visa diagram
        fig = strategy.plot_analysis(analysis)
        if fig:
            st.pyplot(fig)

        # Visa kort sammanfattning
        st.subheader("Sammanfattning")
        st.write(f"Datum för analys: {analysis['date']}")
        st.write(
            "Fundamentala kriterier uppfyllda" if analysis["fundamental_check"] else "Fundamentala kriterier EJ uppfyllda")
        st.write(
            "Tekniska kriterier uppfyllda" if analysis["technical_check"] else "Tekniska kriterier EJ uppfyllda")
        st.write(f"Tech Score: {analysis['tech_score']}/100")

    with tab2_2:
        st.subheader("Fundamentala Data")
        st.write(
            f"Lönsamt bolag: {'Ja' if analysis['is_profitable'] else 'Nej'}")
        st.write(
            f"P/E-tal: {analysis['pe_ratio']:.2f}" if analysis['pe_ratio'] else "P/E-tal: Data saknas")
        st.write(
            f"Omsättningstillväxt: {analysis['revenue_growth']*100:.1f}%" if analysis['revenue_growth'] else "Omsättningstillväxt: Data saknas")
        st.write(
            f"Vinstmarginal: {analysis['profit_margin']*100:.1f}%" if analysis['profit_margin'] else "Vinstmarginal: Data saknas")
        st.write(
            f"Vinstutveckling: {analysis['earnings_trend']}")

    with tab2_3:
        st.subheader("Tekniska Indikatorer")
        st.write(
            f"Pris över MA40 (40-veckor): {'Ja' if analysis['above_ma40'] else 'Nej'}")
        st.write(
            f"Pris över MA4 (4-veckor): {'Ja' if analysis['above_ma4'] else 'Nej'}")
        st.write(
            f"RSI över 50: {'Ja' if analysis['rsi_above_50'] else 'Nej'}")
        st.write(
            f"Högre bottnar: {'Ja' if analysis['higher_lows'] else 'Nej'}")
        st.write(
            f"Nära 52-veckors högsta: {'Ja' if analysis['near_52w_high'] else 'Nej'}")
        st.write(
            f"Breakout från konsolidering: {'Ja' if analysis['breakout'] else 'Nej'}")

    # Add option to compare with another stock (enhancement example)
    with st.expander("Jämför med en annan aktie"):
        compare_ticker = st.text_input(
            "Jämför med (t.ex. MSFT, AAPL)", key="compare_input")
        if st.button("Jämför", key="compare_button"):
            if compare_ticker:
                st.session_state['compare_tickers'] = [
                    analysis["ticker"], compare_ticker]
                # This could trigger a comparison feature in a future tab
                st.info(
                    f"Jämförelse mellan {analysis['ticker']} och {compare_ticker} är inte implementerad ännu.")
            else:
                st.warning("Ange en ticker att jämföra med")