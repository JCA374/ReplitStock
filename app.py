import streamlit as st
from streamlit.logger import get_logger
import os

# Import UI components
from ui.watchlist import display_watchlist
from ui.single_stock import display_single_stock_analysis
from ui.batch_analysis import display_batch_analysis
from ui.scanner_ui import display_scanner
from ui.database_viewer import display_database_viewer

# Import database initialization
from data.db_manager import initialize_database

# Setup logging
logger = get_logger(__name__)

def main():
    # Initialize the database
    initialize_database()
    
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
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select a page:",
        ["Watchlist", "Single Stock Analysis", "Batch Analysis", "Stock Scanner", "Database Viewer"]
    )
    
    # Display the selected page
    if page == "Watchlist":
        display_watchlist()
    elif page == "Single Stock Analysis":
        display_single_stock_analysis()
    elif page == "Batch Analysis":
        display_batch_analysis()
    elif page == "Stock Scanner":
        display_scanner()
    elif page == "Database Viewer":
        display_database_viewer()

if __name__ == "__main__":
    main()
