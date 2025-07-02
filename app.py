# Standard library imports
import os
import traceback

# Third-party imports
import pandas as pd
import streamlit as st
from streamlit.logger import get_logger

# Local application imports
# Database
from data.db_connection import get_db_connection, get_db_engine, get_db_session, test_connection
from data.db_models import Base

# UI components
from ui.batch_analysis import display_batch_analysis
from ui.company_explorer import display_company_explorer
from ui.database_viewer import display_database_viewer
from ui.watchlist import display_watchlist

# Analysis components and services
from services.company_explorer import CompanyExplorer
from tabs.analysis_tab import render_analysis_tab
from ui.enhanced_scanner import render_enhanced_scanner_ui
from analysis.strategy import ValueMomentumStrategy

# Setup logging
logger = get_logger(__name__)


def initialize_tables(engine):
    """Initialize database tables using SQLAlchemy models"""
    try:
        from data.db_models import Base
        Base.metadata.create_all(engine)
        return True
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        return False


def create_db_storage():
    """Create a database storage object for the watchlist manager and strategy"""
    # This wrapper provides database operations to our classes
    from data.db_integration import add_to_watchlist, remove_from_watchlist, get_watchlist, get_cached_stock_data

    return {
        'engine': get_db_engine(),
        'session': get_db_session,
        'get_cached_stock_data': get_cached_stock_data,
        'add_to_watchlist': add_to_watchlist,
        'remove_from_watchlist': remove_from_watchlist,
        'get_watchlist': get_watchlist
    }

def display_database_status():
    """Display database status in the sidebar"""
    try:
        from data.db_integration import get_database_status
        import os

        status = get_database_status()

        st.sidebar.markdown("---")
        st.sidebar.subheader("📊 Database Status")

        # SQLite status
        if status['sqlite_available']:
            db_size = "Unknown"
            try:
                if os.path.exists("stock_data.db"):
                    size_bytes = os.path.getsize("stock_data.db")
                    db_size = f"{size_bytes / (1024*1024):.1f} MB"
            except:
                pass
            st.sidebar.success(f"✅ SQLite: Active ({db_size})")
        else:
            st.sidebar.error("❌ SQLite: Not available")

        # Supabase status
        if status['supabase_connected']:
            st.sidebar.info("ℹ️ Supabase: Available (not used for watchlist)")
        else:
            st.sidebar.info("ℹ️ Supabase: Not connected")

        # Primary database
        st.sidebar.markdown(
            f"**Primary DB:** :blue[SQLite] (Watchlist uses SQLite exclusively)")

    except Exception as e:
        st.sidebar.error(f"Database status error: {e}")

def display_development_notes():
    """Display development notes and updates for users"""
    st.header("📝 Development Notes")
    st.markdown("Latest updates and improvements to the Stock Analysis Tool")
    
    # Recent Updates Section
    st.subheader("🔄 Recent Updates")
    
    with st.expander("✅ July 2, 2025 - Enhanced Watchlist Management", expanded=True):
        st.markdown("""
        **New Add to Watchlist Features:**
        - ➕ button now opens dropdown menu of all your watchlists
        - Choose exactly which watchlist to add each stock to
        - No more guessing - full control over stock placement
        
        **New Delete from Watchlist Features:**
        - 🗑️ button appears only for stocks already in watchlists
        - Removes stocks from all watchlists containing them
        - Automatic page refresh after deletion
        
        **How to Use:**
        1. Run batch scan → Click ➕ → Select target watchlist → Confirm
        2. Click 🗑️ to remove stocks from all watchlists
        """)
    
    with st.expander("✅ July 2, 2025 - Import/Export Functionality"):
        st.markdown("""
        **Watchlist Import/Export:**
        - Upload CSV files with ticker symbols (Watchlist tab)
        - Download watchlists as CSV with timestamp
        - Smart duplicate detection and Swedish market formatting (.ST)
        
        **Reorganized Interface:**
        - Step-by-step batch analysis flow
        - Development Notes tab for updates and technical info
        """)
    
    # Work in Progress Section
    st.subheader("🚧 Work in Progress")
    
    with st.expander("🔍 Analysis Consistency Investigation"):
        st.markdown("""
        **Investigating potential differences between Single Stock and Batch Analysis:**
        - Data source consistency
        - Technical indicator calculations
        - Signal generation alignment
        
        **Status:** Both methods work correctly, minor variations being resolved
        """)
    
    # Future Improvements Section
    st.subheader("🚀 Planned Improvements")
    
    with st.expander("📋 Upcoming Features"):
        st.markdown("""
        - Enhanced import options (Excel, JSON support)
        - Watchlist categories (growth, value, dividend themes)
        - Portfolio performance tracking
        - Stock movement alerts
        """)
    
    # Technical Notes Section
    st.subheader("🔧 Technical Notes")
    
    with st.expander("⚙️ System Information"):
        st.markdown("""
        **Database:** SQLite (primary), Supabase (backup when available)
        **Data Sources:** Yahoo Finance (prices), Alpha Vantage (fundamentals)
        **Performance:** Cached data, parallel processing, mobile-responsive
        **Market Focus:** Swedish stocks with .ST ticker support
        """)

def main():
    try:
        # Set page title and configuration
        st.set_page_config(
            page_title="Stock Analysis Tool",
            page_icon="📈",
            layout="wide",
            initial_sidebar_state="collapsed",
        )
        
        # Global mobile-responsive CSS
        st.markdown("""
        <style>
        /* Force full width on all devices */
        .main .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            max-width: 100% !important;
            width: 100% !important;
        }
        
        /* Mobile responsive breakpoint */
        @media (max-width: 768px) {
            .main .block-container {
                padding-left: 0.5rem !important;
                padding-right: 0.5rem !important;
                max-width: 100% !important;
                width: 100vw !important;
            }
            
            /* Make all horizontal blocks use full width */
            div[data-testid="stHorizontalBlock"] {
                width: 100% !important;
                gap: 0.25rem !important;
            }
            
            div[data-testid="stHorizontalBlock"] > div {
                padding-left: 0.1rem !important;
                padding-right: 0.1rem !important;
                flex: 1 !important;
                min-width: 0 !important;
            }
        }
        </style>
        """, unsafe_allow_html=True)

        # Attempt database connection and show status
        db_connection = get_db_connection()
        engine = db_connection.get_engine()
        
        # Check actual database usage (Supabase integration vs SQLAlchemy)
        from data.db_integration import USE_SUPABASE
        connection_type = "postgresql" if USE_SUPABASE else "sqlite"

        # Create tables if they don't exist
        tables_initialized = initialize_tables(engine)

        # Header section with status indicator
        col1, col2 = st.columns([3, 1])
        with col1:
            st.title("Stock Analysis Tool")
            st.markdown(
                "Analyze stocks using both fundamental (value) and technical (momentum) factors.")

        with col2:
            if connection_type == "postgresql":
                st.success("✅ Connected to Supabase")
            else:
                st.info("💾 Using local SQLite database")
                st.caption("Data stored locally on your device")

        # Initialize strategy and watchlist manager in session state
        if 'strategy' not in st.session_state:
            st.session_state.strategy = ValueMomentumStrategy()

        if 'watchlist_manager' not in st.session_state:
            from services.watchlist_manager import SimpleWatchlistManager
            st.session_state.watchlist_manager = SimpleWatchlistManager()

        # Initialize company explorer in session state
        if 'company_explorer' not in st.session_state:
            # Create a database storage object for company explorer
            db_storage = create_db_storage()
            st.session_state.company_explorer = CompanyExplorer(db_storage)

        # Initialize show_watchlist_manager if not present
        if 'show_watchlist_manager' not in st.session_state:
            st.session_state.show_watchlist_manager = False


        # Main navigation tabs at the top of the page - start with Batch Analysis
        tab1, tab2, tab3, tab4 = st.tabs([
            "📈 Batch Analysis", 
            "📊 Single Stock", 
            "📋 Watchlist",
            "📝 Development Notes"
        ])

        with tab1:
            display_batch_analysis()
            
        with tab2:
            render_analysis_tab()
            
        with tab3:
            display_watchlist()
            
        with tab4:
            display_development_notes()
            
        # Hidden tabs - commented out
        #     display_company_explorer()
        #     
        # with tab5:
        #     render_enhanced_scanner_ui()
        #     
        # with tab6:
        #     display_database_viewer()

        # Footer with database status - HIDDEN
        # st.sidebar.markdown("---")
        # st.sidebar.markdown(f"**Database:** {connection_type.capitalize()}")
        # if st.sidebar.button("Test Connection"):
        #     with st.sidebar:
        #         connection_ok = test_connection()
        #         if connection_ok:
        #             st.success("Database connection is working!")
        #         else:
        #             st.error(
        #                 "Database connection failed. Check your configuration.")

        # Simplified sidebar
        st.sidebar.title("📈 Stock Analyzer")
        st.sidebar.markdown("---")

        # Quick actions
        st.sidebar.subheader("Quick Actions")
        if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        # Help section
        with st.sidebar.expander("ℹ️ Help"):
            st.markdown("""
            - **Single Stock**: Analyze individual stocks
            - **Batch Analysis**: Analyze multiple stocks
            - **Watchlist**: Manage your stock lists
            - **Explorer**: Search for stocks
            - **Scanner**: Find stocks by criteria
            """)

        # Footer
        st.sidebar.markdown("---")
        st.sidebar.caption(f"v1.0 | DB: {connection_type}")

    except Exception as e:
        st.error(f"Application error: {e}")
        st.code(traceback.format_exc())
        st.info(
            "Please check the configuration and try again. If the error persists, contact support.")


if __name__ == "__main__":
    main()
