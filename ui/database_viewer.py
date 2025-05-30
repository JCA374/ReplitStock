import streamlit as st
import pandas as pd
from data.db_manager import get_db_session, get_db_engine, StockDataCache, Watchlist, FundamentalsCache
from data.supabase_client import get_supabase_db
from data.db_integration import USE_SUPABASE
import json
import io
from sqlalchemy import text
from datetime import datetime
import traceback

def display_database_viewer():
    """
    Display a view of the database content (Supabase or SQLite).
    """
    st.title("Database Viewer")
    
    # Show which database is being used
    if USE_SUPABASE:
        st.write("Connected to Supabase database (with SQLite fallback)")
        db_source = st.radio("View data from:", ["Supabase", "Local SQLite"])
    else:
        st.write("Using local SQLite database only")
        db_source = "Local SQLite"
    
    # Create tabs for different tables
    tab_watchlist, tab_stock_cache, tab_fundamentals, tab_custom, tab_analysis = st.tabs([
        "Watchlist", "Stock Data Cache", "Fundamentals", "Custom Query", "Analysis Results"
    ])
    
    # Watchlist tab
    with tab_watchlist:
        st.subheader("Watchlist Table")
        
        if db_source == "Supabase" and USE_SUPABASE:
            # Get data from Supabase
            try:
                supabase_client = get_supabase_db()
                response = supabase_client.get_watchlist()
                
                if response:
                    # Create dataframe directly from response
                    watchlist_df = pd.DataFrame(response)
                    st.dataframe(watchlist_df)
                    st.info(f"Total records in Supabase: {len(response)}")
                else:
                    st.info("No watchlist records found in Supabase.")
            except Exception as e:
                st.error(f"Error querying Supabase watchlist: {str(e)}")
        else:
            # Get data from SQLite
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
                    st.info(f"Total records in SQLite: {len(watchlist_data)}")
                else:
                    st.info("No watchlist records found in SQLite.")
                
                session.close()
            except Exception as e:
                st.error(f"Error querying SQLite watchlist: {str(e)}")
    
    # Stock Data Cache tab
    with tab_stock_cache:
        st.subheader("Stock Data Cache")
        
        if db_source == "Supabase" and USE_SUPABASE:
            # Get data from Supabase
            try:
                supabase_client = get_supabase_db()
                
                # Query the stock_data_cache table
                if supabase_client and supabase_client.client:
                    response = supabase_client.client.table("stock_data_cache").select("*").execute()
                    cache_data = response.data if hasattr(response, 'data') else []
                    
                    if cache_data:
                        # Convert to list of dictionaries
                        cache_records = []
                        for item in cache_data:
                            try:
                                # Convert timestamp to datetime (if it exists)
                                timestamp = item.get('timestamp')
                                if timestamp:
                                    timestamp_dt = datetime.fromtimestamp(float(timestamp))
                                else:
                                    timestamp_dt = None
                                    
                                # Get data size if data exists
                                data = item.get('data')
                                data_size = len(str(data)) if data else 0
                                
                                cache_records.append({
                                    'ID': item.get('id'),
                                    'Ticker': item.get('ticker'),
                                    'Timeframe': item.get('timeframe'),
                                    'Period': item.get('period'),
                                    'Source': item.get('source'),
                                    'Timestamp': timestamp_dt,
                                    'Data Size (bytes)': data_size
                                })
                            except Exception as e:
                                st.warning(f"Skipped Supabase record due to: {str(e)}")
                        
                        if cache_records:
                            cache_df = pd.DataFrame(cache_records)
                            st.dataframe(cache_df)
                            st.info(f"Total cached stock records in Supabase: {len(cache_records)}")
                        else:
                            st.info("No valid stock data cache records found in Supabase.")
                    else:
                        st.info("No stock data cache records found in Supabase.")
                else:
                    st.error("Supabase client is not properly initialized")
            except Exception as e:
                st.error(f"Error querying Supabase stock data cache: {str(e)}")
                st.error(traceback.format_exc())
        else:
            # Get data from SQLite
            try:
                session = get_db_session()
                cache_data = session.query(StockDataCache).all()
                cache_records = []
                
                if cache_data:
                    # Convert to list of dictionaries
                    for item in cache_data:
                        try:
                            timestamp_dt = datetime.fromtimestamp(float(item.timestamp)) if item.timestamp else None
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
                            st.warning(f"Skipped SQLite record due to: {str(e)}")
                    
                    if cache_records:
                        cache_df = pd.DataFrame(cache_records)
                        st.dataframe(cache_df)
                        st.info(f"Total cached stock records in SQLite: {len(cache_records)}")
                    
                        # Option to view data for a specific ticker
                        ticker_strings = sorted(list(set([record['Ticker'] for record in cache_records])))
                        
                        if ticker_strings:
                            selected_ticker = st.selectbox("Select ticker to view cached data:", ticker_strings)
                            
                            if selected_ticker:
                                # Find the first matching record
                                selected_item = None
                                for item in cache_data:
                                    if str(item.ticker) == selected_ticker:
                                        selected_item = item
                                        break
                                
                                if selected_item and selected_item.data:
                                    try:
                                        # Get the data as a string and ensure it's valid
                                        data_str = str(selected_item.data)
                                        
                                        # Parse the JSON data
                                        df = pd.read_json(io.StringIO(data_str))
                                        st.subheader(f"Preview of {selected_ticker} data:")
                                        st.dataframe(df.head(10))
                                        
                                        # Show chart
                                        if 'close' in df.columns:
                                            st.subheader(f"Chart for {selected_ticker}:")
                                            st.line_chart(df['close'])
                                        else:
                                            st.warning("No 'close' column found in the data.")
                                    except Exception as e:
                                        st.error(f"Error parsing data: {str(e)}")
                                else:
                                    st.warning("No data available for this ticker.")
                else:
                    st.info("No stock data cache records found in SQLite.")
                
                session.close()
            except Exception as e:
                st.error(f"Error querying SQLite stock data cache: {str(e)}")
    
    # Fundamentals tab
    with tab_fundamentals:
        st.subheader("Fundamentals Cache")
        
        if db_source == "Supabase" and USE_SUPABASE:
            # Get data from Supabase
            try:
                supabase_client = get_supabase_db()
                
                # Query the fundamentals_cache table
                if supabase_client and supabase_client.client:
                    response = supabase_client.client.table("fundamentals_cache").select("*").execute()
                    fundamentals_data = response.data if hasattr(response, 'data') else []
                    
                    if fundamentals_data:
                        # Convert to list of dictionaries
                        fund_records = []
                        for item in fundamentals_data:
                            try:
                                # Convert timestamp to datetime (if it exists)
                                last_updated = item.get('last_updated')
                                if last_updated:
                                    last_updated_dt = datetime.fromtimestamp(float(last_updated))
                                else:
                                    last_updated_dt = None
                                    
                                fund_records.append({
                                    'Ticker': item.get('ticker'),
                                    'P/E Ratio': item.get('pe_ratio'),
                                    'Profit Margin': item.get('profit_margin'),
                                    'Revenue Growth': item.get('revenue_growth'),
                                    'Earnings Growth': item.get('earnings_growth'),
                                    'Book Value': item.get('book_value'),
                                    'Market Cap': item.get('market_cap'),
                                    'Dividend Yield': item.get('dividend_yield'),
                                    'Last Updated': last_updated_dt
                                })
                            except Exception as e:
                                st.warning(f"Skipped Supabase fundamental record due to: {str(e)}")
                        
                        if fund_records:
                            fund_df = pd.DataFrame(fund_records)
                            st.dataframe(fund_df)
                            st.info(f"Total fundamental records in Supabase: {len(fund_records)}")
                        else:
                            st.info("No valid fundamentals cache records found in Supabase.")
                    else:
                        st.info("No fundamentals cache records found in Supabase.")
                else:
                    st.error("Supabase client is not properly initialized")
            except Exception as e:
                st.error(f"Error querying Supabase fundamentals: {str(e)}")
        else:
            # Get data from SQLite
            try:
                session = get_db_session()
                fundamentals_data = session.query(FundamentalsCache).all()
                
                if fundamentals_data:
                    # Convert to list of dictionaries
                    fund_records = []
                    for item in fundamentals_data:
                        try:
                            last_updated_dt = datetime.fromtimestamp(float(item.last_updated)) if item.last_updated else None
                            
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
                            st.warning(f"Skipped SQLite fundamental record due to: {str(e)}")
                    
                    if fund_records:
                        fund_df = pd.DataFrame(fund_records)
                        st.dataframe(fund_df)
                        st.info(f"Total fundamental records in SQLite: {len(fund_records)}")
                    else:
                        st.info("No valid fundamentals cache records found in SQLite.")
                else:
                    st.info("No fundamentals cache records found in SQLite.")
                
                session.close()
            except Exception as e:
                st.error(f"Error querying SQLite fundamentals: {str(e)}")
    
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
                            df_data = [{col: row[i] for i, col in enumerate(columns)} for row in rows]
                            df = pd.DataFrame(df_data)
                            st.dataframe(df)
                            st.success(f"Query executed successfully. {len(rows)} rows returned.")
                        else:
                            st.info("Query executed successfully, but no results were returned.")
                except Exception as e:
                    st.error(f"Error executing query: {str(e)}")
            else:
                st.warning("Please enter a SQL query to execute.")

    # Add Analysis Results tab
    with tab_analysis:
        st.subheader("Analysis Results")

        if db_source == "Supabase" and USE_SUPABASE:
            # Get data from Supabase
            try:
                supabase_client = get_supabase_db()

                # Query the analysis_results table
                if supabase_client and supabase_client.client:
                    response = supabase_client.client.table("analysis_results").select(
                        "*").order("analysis_date", desc=True).limit(100).execute()
                    analysis_data = response.data if hasattr(
                        response, 'data') else []

                    if analysis_data:
                        # Convert to DataFrame for display
                        analysis_df = pd.DataFrame(analysis_data)
                        st.dataframe(analysis_df)
                        st.info(
                            f"Showing latest 100 analysis results from Supabase ({len(analysis_data)} records)")
                    else:
                        st.info("No analysis results found in Supabase")
            except Exception as e:
                st.error(f"Error querying Supabase analysis results: {e}")
        else:
            # Get data from SQLite
            try:
                from data.db_models import AnalysisResults
                session = get_db_session()
                analysis_data = session.query(AnalysisResults).order_by(
                    AnalysisResults.analysis_date.desc()).limit(100).all()

                if analysis_data:
                    # Convert to list of dictionaries
                    analysis_records = []
                    for item in analysis_data:
                        analysis_records.append({
                            'Ticker': item.ticker,
                            'Date': item.analysis_date,
                            'Price': item.price,
                            'Tech Score': item.tech_score,
                            'Signal': item.signal,
                            'P/E Ratio': item.pe_ratio,
                            'Data Source': item.data_source,
                            'Last Updated': datetime.fromtimestamp(item.last_updated) if item.last_updated else None
                        })

                    # Create DataFrame
                    analysis_df = pd.DataFrame(analysis_records)
                    st.dataframe(analysis_df)
                    st.info(
                        f"Showing latest 100 analysis results from SQLite ({len(analysis_records)} records)")
                else:
                    st.info("No analysis results found in SQLite")

                session.close()
            except Exception as e:
                st.error(f"Error querying SQLite analysis results: {e}")


    # Add a button to refresh the data
    if st.button("Refresh Data"):
        st.rerun()