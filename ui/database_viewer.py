import streamlit as st
import pandas as pd
from data.db_manager import get_db_session, get_db_engine, StockDataCache, Watchlist, FundamentalsCache
import json
import io
from sqlalchemy import text
from datetime import datetime

def display_database_viewer():
    """
    Display a view of the SQLite database content.
    """
    st.title("Database Viewer")
    st.write("View the content of the local SQLite database")
    
    # Create tabs for different tables
    tab_watchlist, tab_stock_cache, tab_fundamentals, tab_custom = st.tabs([
        "Watchlist", "Stock Data Cache", "Fundamentals", "Custom Query"
    ])
    
    # Watchlist tab
    with tab_watchlist:
        st.subheader("Watchlist Table")
        try:
            session = get_db_session()
            watchlist_data = session.query(Watchlist).all()
            
            if watchlist_data:
                # Convert to list of dictionaries
                watchlist_records = []
                for item in watchlist_data:
                    watchlist_records.append({
                        'ID': item.id,
                        'Ticker': item.ticker,
                        'Name': item.name,
                        'Exchange': item.exchange,
                        'Sector': item.sector,
                        'Added Date': item.added_date
                    })
                
                watchlist_df = pd.DataFrame(watchlist_records)
                st.dataframe(watchlist_df)
                st.info(f"Total records: {len(watchlist_data)}")
            else:
                st.info("No watchlist records found.")
            
            session.close()
        except Exception as e:
            st.error(f"Error querying watchlist: {str(e)}")
    
    # Stock Data Cache tab
    with tab_stock_cache:
        st.subheader("Stock Data Cache")
        
        try:
            session = get_db_session()
            cache_data = session.query(StockDataCache).all()
            
            if cache_data:
                # Convert to list of dictionaries
                cache_records = []
                for item in cache_data:
                    try:
                        timestamp_dt = datetime.fromtimestamp(item.timestamp)
                        data_size = len(str(item.data)) if item.data else 0
                        
                        cache_records.append({
                            'ID': item.id,
                            'Ticker': item.ticker,
                            'Timeframe': item.timeframe,
                            'Period': item.period,
                            'Source': item.source,
                            'Timestamp': timestamp_dt,
                            'Data Size (bytes)': data_size
                        })
                    except Exception as e:
                        st.warning(f"Skipped record due to: {str(e)}")
                
                cache_df = pd.DataFrame(cache_records)
                st.dataframe(cache_df)
                st.info(f"Total cached stock records: {len(cache_records)}")
                
                # Option to view data for a specific ticker
                if cache_records:
                    # Extract ticker strings for display
                    ticker_strings = []
                    for record in cache_records:
                        ticker = record['Ticker']
                        if ticker not in ticker_strings:
                            ticker_strings.append(ticker)
                    ticker_strings.sort()
                    
                    selected_ticker = st.selectbox("Select ticker to view cached data:", ticker_strings)
                    
                    if selected_ticker:
                        # Find the first matching record
                        selected_item = None
                        for item in cache_data:
                            if str(item.ticker) == selected_ticker:
                                selected_item = item
                                break
                        
                        if selected_item:
                            try:
                                # Get the data as a string and ensure it's valid
                                data_str = str(selected_item.data) if selected_item.data else ""
                                
                                if data_str:
                                    # Parse the JSON data
                                    df = pd.read_json(data_str)
                                    st.subheader(f"Preview of {selected_ticker} data:")
                                    st.dataframe(df.head(10))
                                    
                                    # Show chart
                                    st.subheader(f"Chart for {selected_ticker}:")
                                    st.line_chart(df['Close'])
                                else:
                                    st.warning("No data available for this ticker.")
                            except Exception as e:
                                st.error(f"Error parsing data: {str(e)}")
            else:
                st.info("No stock data cache records found.")
            
            session.close()
        except Exception as e:
            st.error(f"Error querying stock data cache: {str(e)}")
    
    # Fundamentals tab
    with tab_fundamentals:
        st.subheader("Fundamentals Cache")
        
        try:
            session = get_db_session()
            fundamentals_data = session.query(FundamentalsCache).all()
            
            if fundamentals_data:
                # Convert to list of dictionaries
                fund_records = []
                for item in fundamentals_data:
                    try:
                        last_updated_dt = datetime.fromtimestamp(item.last_updated)
                        
                        fund_records.append({
                            'Ticker': item.ticker,
                            'P/E Ratio': item.pe_ratio,
                            'Profit Margin': item.profit_margin,
                            'Revenue Growth': item.revenue_growth,
                            'Earnings Growth': item.earnings_growth,
                            'Book Value': item.book_value,
                            'Market Cap': item.market_cap,
                            'Dividend Yield': item.dividend_yield,
                            'Last Updated': last_updated_dt
                        })
                    except Exception as e:
                        st.warning(f"Skipped fundamental record due to: {str(e)}")
                
                fund_df = pd.DataFrame(fund_records)
                st.dataframe(fund_df)
                st.info(f"Total fundamental records: {len(fund_records)}")
            else:
                st.info("No fundamentals cache records found.")
            
            session.close()
        except Exception as e:
            st.error(f"Error querying fundamentals: {str(e)}")
    
    # Custom SQL Query tab
    with tab_custom:
        st.subheader("Run Custom SQL Query")
        st.write("Execute a custom SQL query against the SQLite database")
        
        # Show the available tables
        st.write("Available tables:")
        st.code("watchlist, stock_data_cache, fundamentals_cache")
        
        # Example queries
        st.write("Example queries:")
        example_queries = {
            "Count records by table": "SELECT 'Watchlist' as table_name, COUNT(*) as count FROM watchlist UNION ALL SELECT 'Stock Cache', COUNT(*) FROM stock_data_cache UNION ALL SELECT 'Fundamentals', COUNT(*) FROM fundamentals_cache",
            "Recent watchlist additions": "SELECT * FROM watchlist ORDER BY added_date DESC LIMIT 5",
            "Stock data by timeframe": "SELECT ticker, timeframe, period, source, datetime(timestamp, 'unixepoch') as updated_at FROM stock_data_cache ORDER BY timestamp DESC LIMIT 10",
            "Stocks by exchange": "SELECT exchange, COUNT(*) as count FROM watchlist GROUP BY exchange ORDER BY count DESC"
        }
        
        selected_example = st.selectbox("Load example query:", ["--Select--"] + list(example_queries.keys()))
        
        if selected_example != "--Select--":
            query = example_queries[selected_example]
        else:
            query = ""
        
        custom_query = st.text_area("Enter SQL query:", value=query, height=100)
        
        if st.button("Execute Query"):
            if custom_query.strip():
                try:
                    engine = get_db_engine()
                    with engine.connect() as conn:
                        # Execute the query
                        result = conn.execute(text(custom_query))
                        
                        # Get column names
                        columns = result.keys()
                        
                        # Fetch all results
                        rows = result.fetchall()
                        
                        if rows:
                            # Convert to DataFrame with list comprehension to avoid column issues
                            df_data = [{columns[i]: value for i, value in enumerate(row)} for row in rows]
                            df = pd.DataFrame(df_data)
                            st.dataframe(df)
                            st.success(f"Query executed successfully. {len(rows)} rows returned.")
                        else:
                            st.info("Query executed successfully, but no results were returned.")
                except Exception as e:
                    st.error(f"Error executing query: {str(e)}")
            else:
                st.warning("Please enter a SQL query to execute.")
    
    # Add a button to refresh the data
    if st.button("Refresh Data"):
        st.rerun()