import streamlit as st
import os

st.title("Debug App")
st.write("If you see this, the Streamlit server is running correctly!")

# Print environment variables
st.subheader("Environment Variables")
env_vars = {k: v for k, v in os.environ.items() if not k.startswith('_')}
st.json(env_vars)
