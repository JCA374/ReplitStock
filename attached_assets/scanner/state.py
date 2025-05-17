# scanner/state.py
import streamlit as st
import pandas as pd

def initialize_scanner_state():
    """Initialize session state variables for the scanner."""
    # Scan results DataFrame
    if 'scan_results' not in st.session_state:
        st.session_state.scan_results = pd.DataFrame()
    
    # Failed tickers list
    if 'failed_tickers' not in st.session_state:
        st.session_state.failed_tickers = []
    
    # Running state
    if 'scanner_running' not in st.session_state:
        st.session_state.scanner_running = False
    
    # Status message
    if 'status_message' not in st.session_state:
        st.session_state.status_message = ""
        
    # Progress tracking
    if 'progress_value' not in st.session_state:
        st.session_state.progress_value = 0.0

def reset_scanner_state():
    """Reset scanner state to default values."""
    # Reset scan results
    st.session_state.scan_results = pd.DataFrame()
    
    # Reset failed tickers
    st.session_state.failed_tickers = []
    
    # Reset status
    st.session_state.status_message = ""
    
    # Reset progress
    st.session_state.progress_value = 0.0