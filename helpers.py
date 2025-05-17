import pandas as pd
import streamlit as st

def create_results_table(analysis_results):
    """
    Create a formatted table from analysis results for display
    
    Args:
        analysis_results: List of analysis result dictionaries
        
    Returns:
        pandas.DataFrame: Formatted table for display
    """
    # Filter out results with errors
    valid_results = [r for r in analysis_results if "error" not in r]
    
    if not valid_results:
        return pd.DataFrame()
        
    # Create list to hold formatted data
    formatted_data = []
    
    for result in valid_results:
        # Extract basic info
        ticker = result.get("ticker", "")
        name = result.get("name", ticker)
        price = result.get("price", 0)
        
        # Get signals
        buy_signal = result.get("buy_signal", False)
        sell_signal = result.get("sell_signal", False)
        
        signal = "KÖP" if buy_signal else "SÄLJ" if sell_signal else "HÅLL"
        
        # Get tech score
        tech_score = result.get("tech_score", 0)
        
        # Get technical indicators
        above_ma40 = result.get("above_ma40", False)
        above_ma4 = result.get("above_ma4", False)
        rsi_above_50 = result.get("rsi_above_50", False)
        higher_lows = result.get("higher_lows", False)
        
        # Get fundamentals
        pe_ratio = result.get("pe_ratio")
        profit_margin = result.get("profit_margin")
        revenue_growth = result.get("revenue_growth")
        
        # Get data source
        data_source = result.get("data_source", "unknown")
        
        # Format into a row
        row = {
            "Ticker": ticker,
            "Namn": name,
            "Pris": price,
            "Signal": signal,
            "Tech Score": tech_score,
            "Över MA40": "Ja" if above_ma40 else "Nej",
            "Över MA4": "Ja" if above_ma4 else "Nej",
            "RSI > 50": "Ja" if rsi_above_50 else "Nej",
            "Högre Bottnar": "Ja" if higher_lows else "Nej",
            "P/E": pe_ratio if pe_ratio is not None else None,
            "Vinstmarginal": profit_margin*100 if profit_margin is not None else None,
            "Omsättning Tillväxt": revenue_growth*100 if revenue_growth is not None else None,
            "Data Source": data_source
        }
        
        formatted_data.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(formatted_data)
    
    return df

def get_index_constituents(index_name):
    """
    Get the constituents of a stock index
    
    Args:
        index_name: Name of the index (e.g., "OMXS30", "S&P 500 Top 30", "Dow Jones")
        
    Returns:
        list: List of ticker symbols in the index
    """
    if index_name == "OMXS30":
        return [
            "ABB.ST", "ALFA.ST", "ALIV-SDB.ST", "ASSA-B.ST", "ATCO-A.ST",
            "ATCO-B.ST", "ATRL.ST", "BOL.ST", "ELUX-B.ST", "ERIC-B.ST",
            "ESSITY-B.ST", "EVO.ST", "GETI-B.ST", "HEXA-B.ST", "HM-B.ST",
            "INVE-B.ST", "KINV-B.ST", "NDA-SE.ST", "SAND.ST", "SCA-B.ST",
            "SEB-A.ST", "SHB-A.ST", "SINCH.ST", "SKA-B.ST", "SKF-B.ST",
            "SSAB-A.ST", "STE-R.ST", "SWED-A.ST", "TEL2-B.ST", "VOLV-B.ST"
        ]
    elif index_name == "S&P 500 Top 30":
        return [
            "AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "GOOG", "META", "BRK-B",
            "UNH", "LLY", "JPM", "XOM", "V", "AVGO", "JNJ", "PG", "MA", "HD",
            "TSLA", "MRK", "CVX", "PEP", "COST", "ABBV", "KO", "ADBE", "MCD",
            "WMT", "BAC", "CRM"
        ]
    elif index_name == "Dow Jones":
        return [
            "AAPL", "AMGN", "AXP", "BA", "CAT", "CRM", "CSCO", "CVX", "DIS",
            "DOW", "GS", "HD", "HON", "IBM", "INTC", "JNJ", "JPM", "KO",
            "MCD", "MMM", "MRK", "MSFT", "NKE", "PG", "TRV", "UNH", "V",
            "VZ", "WBA", "WMT"
        ]
    else:
        return []

def preserve_state_on_action(action_func):
    """
    Decorator to preserve session state when performing an action
    
    Args:
        action_func: Function to decorate
        
    Returns:
        Function: Decorated function
    """
    def wrapper(*args, **kwargs):
        # Store current state
        if 'analysis_results' in st.session_state:
            cached_results = st.session_state.analysis_results
        else:
            cached_results = None
            
        # Call the original function
        result = action_func(*args, **kwargs)
        
        # Restore state
        if cached_results is not None:
            st.session_state.analysis_results = cached_results
            
        return result
    
    return wrapper