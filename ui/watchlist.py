import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data.db_manager import get_watchlist, add_to_watchlist, remove_from_watchlist
from data.stock_data import StockDataFetcher
from analysis.technical import calculate_all_indicators, generate_technical_signals
from analysis.fundamental import analyze_fundamentals
from utils.ticker_mapping import normalize_ticker

def display_watchlist():
    st.header("Watchlists")

    # Initialize WatchlistManager
    watchlist_manager = st.session_state.watchlist_manager

    # Get all watchlists
    all_watchlists = watchlist_manager.get_all_watchlists()
    current_index = watchlist_manager.get_active_watchlist_index()

    # Watchlist selection
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_watchlist = st.selectbox(
            "Select Watchlist",
            range(len(all_watchlists)),
            format_func=lambda i: all_watchlists[i]["name"],
            index=current_index
        )

    with col2:
        if st.button("+ New Watchlist"):
            new_name = f"Watchlist {len(all_watchlists) + 1}"
            watchlist_manager.add_watchlist(new_name)
            st.rerun()

    # Manage selected watchlist
    current_watchlist = all_watchlists[selected_watchlist]

    with st.expander("Manage Watchlist"):
        new_name = st.text_input("Rename watchlist", value=current_watchlist["name"])
        col3, col4 = st.columns(2)

        with col3:
            if st.button("Rename"):
                if watchlist_manager.rename_watchlist(selected_watchlist, new_name):
                    st.success("Watchlist renamed")
                    st.rerun()

        with col4:
            if selected_watchlist > 0:  # Don't allow deleting the main watchlist
                if st.button("Delete Watchlist"):
                    if watchlist_manager.delete_watchlist(selected_watchlist):
                        st.success("Watchlist deleted")
                        st.rerun()

    # Add stocks section
    st.subheader("Add Stocks")

    ticker_input = st.text_input("Enter ticker symbol")

    if ticker_input:
        ticker = normalize_ticker(ticker_input)
        data_fetcher = StockDataFetcher()
        stock_info = data_fetcher.get_stock_info(ticker)

        if stock_info:
            st.write(f"Found: {stock_info['name']} ({ticker})")

            if st.button("Add to Watchlist"):
                success = watchlist_manager.add_stock_to_watchlist(
                    selected_watchlist,
                    ticker,
                    add_to_db=(selected_watchlist == 0)  # Only sync main watchlist with DB
                )

                if success:
                    st.success(f"Added {ticker} to watchlist")
                    st.rerun()
                else:
                    st.warning(f"{ticker} is already in your watchlist")
        else:
            st.error(f"Could not find information for {ticker}")

    # Display stocks in current watchlist
    stocks = current_watchlist["stocks"]

    if not stocks:
        st.info("This watchlist is empty. Add stocks using the form above.")
        return

    # Initialize data fetcher
    data_fetcher = StockDataFetcher()

    # Create DataFrame for watchlist display
    watchlist_data = []

    for ticker in stocks:
        try:
            stock_data = data_fetcher.get_stock_data(ticker, '1d', '5d')

            if not stock_data.empty:
                current_price = stock_data['close'].iloc[-1]
                prev_price = stock_data['close'].iloc[-2] if len(stock_data) > 1 else stock_data['close'].iloc[0]
                change_pct = (current_price - prev_price) / prev_price if prev_price > 0 else 0

                info = data_fetcher.get_stock_info(ticker)
                watchlist_data.append({
                    'Ticker': ticker,
                    'Name': info.get('name', ticker),
                    'Exchange': info.get('exchange', ''),
                    'Price': f"${current_price:.2f}",
                    'Change': f"{change_pct:.2%}"
                })

        except Exception as e:
            st.error(f"Error fetching data for {ticker}: {e}")

    if watchlist_data:
        df = pd.DataFrame(watchlist_data)
        st.dataframe(df, hide_index=True)

    # Remove stocks section
    st.subheader("Remove Stocks")
    stock_to_remove = st.selectbox("Select stock to remove", stocks)

    if stock_to_remove and st.button("Remove from Watchlist"):
        if watchlist_manager.remove_stock_from_watchlist(
            selected_watchlist,
            stock_to_remove,
            remove_from_db=(selected_watchlist == 0)  # Only sync main watchlist with DB
        ):
            st.success(f"Removed {stock_to_remove}")
            st.rerun()