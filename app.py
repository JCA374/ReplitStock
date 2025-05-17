import streamlit as st
import os
import sys
import traceback

# Basic app that just shows debug info
st.set_page_config(page_title="Debug App")

try:
    # Show basic environment information
    st.title("Debug Information")

    st.write("## System Info")
    st.write(f"Python version: {sys.version}")
    st.write(f"Current directory: {os.getcwd()}")
    st.write(f"Directory contents: {os.listdir('.')}")

    st.write("## Secrets Check")
    # Safely check for secrets without exposing values
    secrets_to_check = ["DATABASE_URL", "SUPABASE_KEY",
                        "ALPHA_VANTAGE_API_KEY", "DATABASE_PASSWORD"]
    for secret in secrets_to_check:
        try:
            exists = secret in st.secrets
            st.write(f"{secret} exists: {exists}")
        except Exception as e:
            st.write(f"Error checking {secret}: {e}")

    st.write("## Import Check")
    # Try importing your modules one by one to see which one fails
    try:
        import streamlit
        st.write("✅ streamlit imported")

        from data.db_manager import initialize_database
        st.write("✅ data.db_manager imported")

        from services.watchlist_manager import WatchlistManager
        st.write("✅ services.watchlist_manager imported")

        # Add more imports as needed
    except Exception as e:
        st.write(f"❌ Import error: {e}")
        st.code(traceback.format_exc())

    st.success("Debug app loaded successfully!")

except Exception as e:
    st.error(f"Debug app failed: {e}")
    st.code(traceback.format_exc())
