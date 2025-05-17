import streamlit as st
import pandas as pd
from services.company_explorer import CompanyExplorer, render_explorer_tab

def display_company_explorer():
    """
    Display the enhanced company explorer interface with Swedish market focus.
    """
    render_explorer_tab()