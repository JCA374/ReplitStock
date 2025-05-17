import streamlit as st
import pandas as pd
from data.stock_data import StockDataFetcher
from data.db_integration import add_to_watchlist
from ui.search_history import add_to_search_history, get_search_history, search_in_history
import yfinance as yf

def display_company_search():
    """
    Display a company search interface that helps users find stock tickers
    without knowing the exact symbol formats.
    """
    st.title("Company Search")
    st.write("Search for companies by name and get the correct ticker symbol")
    
    search_query = st.text_input("Enter company name or partial ticker:", 
                                placeholder="e.g., Apple, H&M, Volvo")
    
    market_options = ["All Markets", "US Markets", "Swedish Markets (Stockholm)"]
    selected_market = st.selectbox("Market:", market_options)
    
    if st.button("Search") and search_query:
        st.session_state.search_performed = True
        st.session_state.search_query = search_query
        st.session_state.selected_market = selected_market
    
    # If search has been performed, show results
    if 'search_performed' in st.session_state and st.session_state.search_performed:
        search_query = st.session_state.search_query
        selected_market = st.session_state.selected_market
        
        with st.spinner("Searching for companies..."):
            results = search_companies(search_query, selected_market)
            
            if results:
                st.subheader("Search Results")
                
                # Create a DataFrame for display
                results_df = pd.DataFrame(results)
                
                # Format columns for better readability
                if not results_df.empty:
                    # Reorder and rename columns for better display
                    display_columns = []
                    column_mapping = {}
                    
                    # Define available columns and their display names
                    possible_columns = {
                        'symbol': 'Ticker',
                        'name': 'Company Name',
                        'exchange': 'Exchange',
                        'country': 'Country', 
                        'currency': 'Currency'
                    }
                    
                    # Only include columns that exist in our results
                    for col, display_name in possible_columns.items():
                        if col in results_df.columns:
                            display_columns.append(col)
                            column_mapping[col] = display_name
                    
                    # Apply the column selection and renaming
                    if display_columns:
                        results_df = results_df[display_columns]
                        results_df = results_df.rename(columns=column_mapping)
                
                # Display results table
                st.dataframe(results_df)
                
                # Allow adding to watchlist
                st.subheader("Add to Watchlist")
                
                # Create columns for selection
                col1, col2 = st.columns(2)
                
                with col1:
                    # Let user select one of the results
                    symbols = results_df['Ticker'].tolist()
                    selected_symbol = st.selectbox("Select company:", symbols)
                
                with col2:
                    # Get the full record for the selected symbol
                    selected_row = results_df[results_df['Ticker'] == selected_symbol].iloc[0]
                    
                    # Display additional info about the selected company
                    st.write(f"**Exchange:** {selected_row['Exchange']}")
                    if 'Country' in selected_row:
                        st.write(f"**Country:** {selected_row['Country']}")
                    
                # Provide option to add to watchlist
                if st.button("Add to Watchlist"):
                    success = add_to_watchlist(
                        ticker=selected_symbol,
                        name=selected_row['Company Name'],
                        exchange=selected_row['Exchange'],
                        sector=""  # We could try to get sector info in the future
                    )
                    
                    if success:
                        st.success(f"Added {selected_row['Company Name']} ({selected_symbol}) to watchlist!")
                    else:
                        st.warning(f"{selected_symbol} is already in your watchlist.")
                
                # Option to view stock directly
                if st.button("View Stock Analysis"):
                    st.session_state.selected_stock = selected_symbol
                    st.rerun()  # Rerun to redirect
            else:
                st.warning(f"No results found for '{search_query}'. Try a different search term.")
                
    # Reset search button
    if 'search_performed' in st.session_state and st.session_state.search_performed:
        if st.button("Clear Search"):
            st.session_state.search_performed = False
            st.rerun()

def search_companies(query, market_filter="All Markets"):
    """
    Search for companies using multiple data sources.
    First checks the search history, then tries external APIs.
    
    Args:
        query (str): Search term (company name or partial ticker)
        market_filter (str): Filter for specific markets
        
    Returns:
        list: List of matching companies with their details
    """
    results = []
    stock_data = StockDataFetcher()
    
    # Step 1: Check our search history first
    try:
        history_results = search_in_history(query)
        
        # Filter by market if needed
        for item in history_results:
            if market_filter == "US Markets" and "Stockholm" in item.get('exchange', ''):
                continue
            elif market_filter == "Swedish Markets (Stockholm)" and "Stockholm" not in item.get('exchange', ''):
                continue
            
            # Add to results if not already there
            if not any(r['symbol'] == item['symbol'] for r in results):
                results.append(item)
    except Exception as e:
        # Silently continue if history search fails
        pass
    
    # Step 2: Check watchlist too (but don't add to results yet if not enough matches)
    if len(results) < 5:
        try:
            from data.db_integration import get_watchlist
            watchlist = get_watchlist()
            
            # Search in watchlist (case-insensitive)
            query_lower = query.lower()
            for item in watchlist:
                # Check if query appears in ticker or name
                if (query_lower in item['ticker'].lower() or 
                    (item['name'] and query_lower in item['name'].lower())):
                    
                    # Apply market filter if needed
                    if market_filter == "US Markets" and "Stockholm" in item.get('exchange', ''):
                        continue
                    elif market_filter == "Swedish Markets (Stockholm)" and "Stockholm" not in item.get('exchange', ''):
                        continue
                    
                    # Add to results
                    result = {
                        'symbol': item['ticker'],
                        'name': item['name'] or 'Unknown',
                        'exchange': item.get('exchange', ''),
                        'type': 'Stock',
                        'country': '',
                        'currency': ''
                    }
                    
                    # Add to results if not already there
                    if not any(r['symbol'] == result['symbol'] for r in results):
                        results.append(result)
        except Exception:
            # Silently continue if watchlist search fails
            pass
    
    # Step 3: Try more Swedish stock variations if searching for Swedish stocks
    swedish_variations = []
    if market_filter in ["All Markets", "Swedish Markets (Stockholm)"]:
        # Common formats for Swedish stocks
        swedish_variations = [
            f"{query}-B.ST",  # Format for B-shares (e.g., VOLVO-B.ST)
            f"{query}.ST",    # Basic Stockholm format
            f"{query}-A.ST",  # Format for A-shares
            f"{query}-PREF.ST"  # Preferred shares
        ]
        
        # Special case for Volvo
        if query.lower() == "volvo":
            swedish_variations = ["VOLV-B.ST", "VOLV-A.ST", "VOLVO-B.ST", "VOLVO.ST"]
    
    # Try direct lookups for Swedish stocks first
    if swedish_variations:
        for ticker in swedish_variations:
            try:
                info = yf.Ticker(ticker).info
                # Check if we got valid data
                if 'symbol' in info and ('shortName' in info or 'longName' in info):
                    result = {
                        'symbol': info.get('symbol'),
                        'name': info.get('shortName', info.get('longName', '')),
                        'exchange': info.get('exchange', ''),
                        'type': 'Stock',
                        'country': info.get('country', ''),
                        'currency': info.get('currency', '')
                    }
                    
                    # Add to search history (not watchlist) for future searches
                    try:
                        add_to_search_history(
                            symbol=result['symbol'],
                            name=result['name'],
                            exchange=result['exchange']
                        )
                    except Exception:
                        pass  # Ignore errors adding to search history
                        
                    # Check for duplicates before adding
                    if not any(item['symbol'] == result['symbol'] for item in results):
                        results.append(result)
            except Exception:
                # Skip tickers that don't work
                continue
    
    # Step 4: Try Yahoo Finance search if we don't have enough results yet
    if len(results) < 5:
        try:
            yahoo_results = stock_data.search_stock(query)
            
            # Filter by market if specified
            if market_filter == "US Markets":
                yahoo_results = [r for r in yahoo_results if 'US' in r.get('exchDisp', '')]
            elif market_filter == "Swedish Markets (Stockholm)":
                yahoo_results = [r for r in yahoo_results if 'Stockholm' in r.get('exchDisp', '')]
            
            # Add Yahoo results
            for item in yahoo_results:
                # Convert Yahoo result structure to our standard format
                result = {
                    'symbol': item.get('symbol'),
                    'name': item.get('shortname', item.get('longname', '')),
                    'exchange': item.get('exchDisp', ''),
                    'type': item.get('typeDisp', ''),
                    'country': '',  # Yahoo doesn't always provide this
                    'currency': ''  # Yahoo doesn't always provide this
                }
                
                # Check for duplicates before adding
                if not any(r['symbol'] == result['symbol'] for r in results):
                    results.append(result)
                    
                    # Add to search history (not watchlist) for future searches
                    try:
                        add_to_search_history(
                            symbol=result['symbol'],
                            name=result['name'],
                            exchange=result['exchange']
                        )
                    except Exception:
                        pass  # Ignore errors adding to search history
        except Exception as e:
            # Silently continue if Yahoo search fails
            pass
    
    # Step 5: Try direct ticker lookup if we still need more results
    if len(results) < 3:
        try:
            # For direct lookups of tickers, also try without extensions
            possible_tickers = [query]
            
            for ticker in possible_tickers:
                try:
                    info = yf.Ticker(ticker).info
                    if 'symbol' in info and ('shortName' in info or 'longName' in info):
                        # Check if we got valid data
                        result = {
                            'symbol': info.get('symbol'),
                            'name': info.get('shortName', info.get('longName', '')),
                            'exchange': info.get('exchange', ''),
                            'type': 'Stock',
                            'country': info.get('country', ''),
                            'currency': info.get('currency', '')
                        }
                        
                        # Filter by market if needed
                        if (market_filter == "US Markets" and 'US' not in result['exchange']) or \
                           (market_filter == "Swedish Markets (Stockholm)" and 'Stockholm' not in result['exchange']):
                            continue
                            
                        # Add to search history (not watchlist) for future searches
                        try:
                            add_to_search_history(
                                symbol=result['symbol'],
                                name=result['name'],
                                exchange=result['exchange']
                            )
                        except Exception:
                            pass  # Ignore errors adding to search history
                            
                        # Check for duplicates before adding
                        if not any(r['symbol'] == result['symbol'] for r in results):
                            results.append(result)
                except Exception:
                    # Skip tickers that don't work
                    continue
        except Exception:
            # Silently continue if direct lookup fails
            pass
    
    return results