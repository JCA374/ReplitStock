import streamlit as st
from streamlit.logger import get_logger
import os

# Import UI components
from ui.watchlist import display_watchlist
from ui.batch_analysis import display_batch_analysis
from ui.scanner_ui import display_scanner
from ui.database_viewer import display_database_viewer
from ui.company_search import display_company_search

# Import the new analysis tab implementation
from tabs.analysis_tab import render_analysis_tab
from tabs.strategy import ValueMomentumStrategy
from services.watchlist_manager import WatchlistManager
from data.db_integration import create_supabase_tables, get_cached_stock_data

# Import database initializations
from data.db_manager import initialize_database

# Setup logging
logger = get_logger(__name__)

def main():
    # Initialize databases
    initialize_database()
    create_supabase_tables()
    
    # Set page title and configuration
    st.set_page_config(
        page_title="Stock Analysis Tool",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    # Header section
    st.title("Stock Analysis Tool")
    st.markdown("""
    Analyze stocks using both fundamental (value) and technical (momentum) factors.
    """)
    
    # Initialize strategy and watchlist manager in session state if not already done
    if 'strategy' not in st.session_state:
        st.session_state.strategy = ValueMomentumStrategy()
    
    if 'watchlist_manager' not in st.session_state:
        # Create a database storage object to pass to the watchlist manager
        st.session_state.db_storage = create_db_storage()
        st.session_state.watchlist_manager = WatchlistManager(st.session_state.db_storage)
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select a page:",
        ["Watchlist", "Company Search", "Single Stock Analysis", "Batch Analysis", "Stock Scanner", "Database Viewer"]
    )
    
    # Display the selected page
    if page == "Watchlist":
        display_watchlist()
    elif page == "Company Search":
        display_company_search()
    elif page == "Single Stock Analysis":
        render_analysis_tab()  # Use the new implementation
    elif page == "Batch Analysis":
        display_batch_analysis()
    elif page == "Stock Scanner":
        display_scanner()
    elif page == "Database Viewer":
        display_database_viewer()

def create_db_storage():
    """Create a database storage object for the watchlist manager and strategy"""
    # This is a simple wrapper to provide DB storage operations to our classes
    # For now, we'll just use the existing functions from db_integration
    return {
        'get_cached_stock_data': get_cached_stock_data,
        'add_to_watchlist': create_supabase_tables,  # Just a placeholder, not used directly
    }

if __name__ == "__main__":
    main()
