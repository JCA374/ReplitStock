import pandas as pd
import streamlit as st
import numpy as np


def create_results_table(analysis_results):
    """
    Create a formatted table from analysis results for display
    
    Args:
        analysis_results: List of analysis result dictionaries
        
    Returns:
        pandas.DataFrame: Formatted table for display
    """
    # Filter out results with errors
    valid_results = [
        r for r in analysis_results if "error" not in r or r.get("error") is None]

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

        signal = result.get("signal", "")
        if not signal:
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
            "Pris": f"{price:.2f}" if isinstance(price, (int, float)) and price > 0 else "N/A",
            "Signal": signal,
            "Tech Score": int(tech_score) if isinstance(tech_score, (int, float)) else 0,
            "Över MA40": "Ja" if above_ma40 else "Nej",
            "Över MA4": "Ja" if above_ma4 else "Nej",
            "RSI > 50": "Ja" if rsi_above_50 else "Nej",
            "Högre Bottnar": "Ja" if higher_lows else "Nej",
            "P/E": f"{pe_ratio:.2f}" if pe_ratio is not None and isinstance(pe_ratio, (int, float)) else "N/A",
            "Vinstmarginal": f"{profit_margin*100:.1f}%" if profit_margin is not None and isinstance(profit_margin, (int, float)) else "N/A",
            "Omsättning Tillväxt": f"{revenue_growth*100:.1f}%" if revenue_growth is not None and isinstance(revenue_growth, (int, float)) else "N/A",
            "Data Source": data_source.title()
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


def safe_float_format(value, decimal_places=2, percentage=False):
    """
    Safely format a float value for display
    
    Args:
        value: The value to format
        decimal_places: Number of decimal places
        percentage: Whether to format as percentage
        
    Returns:
        str: Formatted string
    """
    try:
        if value is None or pd.isna(value):
            return "N/A"

        if not isinstance(value, (int, float)):
            return str(value)

        if percentage:
            return f"{value * 100:.{decimal_places}f}%"
        else:
            return f"{value:.{decimal_places}f}"
    except:
        return "N/A"


def safe_int_format(value):
    """
    Safely format an integer value for display
    
    Args:
        value: The value to format
        
    Returns:
        str: Formatted string
    """
    try:
        if value is None or pd.isna(value):
            return "N/A"

        if isinstance(value, (int, float)):
            return str(int(value))
        else:
            return str(value)
    except:
        return "N/A"


def validate_analysis_result(result):
    """
    Validate that an analysis result has the required fields
    
    Args:
        result: Analysis result dictionary
        
    Returns:
        dict: Validated result with default values for missing fields
    """
    required_fields = {
        'ticker': '',
        'name': '',
        'price': 0,
        'signal': 'HÅLL',
        'tech_score': 0,
        'buy_signal': False,
        'sell_signal': False,
        'above_ma40': False,
        'above_ma4': False,
        'rsi_above_50': False,
        'higher_lows': False,
        'near_52w_high': False,
        'breakout': False,
        'pe_ratio': None,
        'profit_margin': None,
        'revenue_growth': None,
        'is_profitable': False,
        'fundamental_check': False,
        'data_source': 'unknown'
    }

    # Fill in missing fields with defaults
    validated_result = {}
    for field, default_value in required_fields.items():
        validated_result[field] = result.get(field, default_value)

    # Add any additional fields from the original result
    for field, value in result.items():
        if field not in validated_result:
            validated_result[field] = value

    return validated_result


def calculate_portfolio_metrics(results):
    """
    Calculate portfolio-level metrics from analysis results
    
    Args:
        results: List of analysis results
        
    Returns:
        dict: Portfolio metrics
    """
    valid_results = [
        r for r in results if "error" not in r or r.get("error") is None]

    if not valid_results:
        return {}

    total_stocks = len(valid_results)

    # Count signals
    buy_signals = sum(1 for r in valid_results if r.get('buy_signal', False))
    sell_signals = sum(1 for r in valid_results if r.get('sell_signal', False))
    hold_signals = total_stocks - buy_signals - sell_signals

    # Calculate average tech score
    tech_scores = [r.get('tech_score', 0) for r in valid_results if isinstance(
        r.get('tech_score'), (int, float))]
    avg_tech_score = np.mean(tech_scores) if tech_scores else 0

    # Count stocks above moving averages
    above_ma40 = sum(1 for r in valid_results if r.get('above_ma40', False))
    above_ma4 = sum(1 for r in valid_results if r.get('above_ma4', False))

    # Count profitable stocks
    profitable = sum(1 for r in valid_results if r.get('is_profitable', False))

    # Data source breakdown
    data_sources = {}
    for result in valid_results:
        source = result.get('data_source', 'unknown')
        data_sources[source] = data_sources.get(source, 0) + 1

    return {
        'total_stocks': total_stocks,
        'buy_signals': buy_signals,
        'sell_signals': sell_signals,
        'hold_signals': hold_signals,
        'buy_percentage': (buy_signals / total_stocks) * 100 if total_stocks > 0 else 0,
        'sell_percentage': (sell_signals / total_stocks) * 100 if total_stocks > 0 else 0,
        'avg_tech_score': avg_tech_score,
        'above_ma40_count': above_ma40,
        'above_ma40_percentage': (above_ma40 / total_stocks) * 100 if total_stocks > 0 else 0,
        'above_ma4_count': above_ma4,
        'above_ma4_percentage': (above_ma4 / total_stocks) * 100 if total_stocks > 0 else 0,
        'profitable_count': profitable,
        'profitable_percentage': (profitable / total_stocks) * 100 if total_stocks > 0 else 0,
        'data_sources': data_sources
    }


def display_portfolio_summary(metrics):
    """
    Display portfolio summary metrics in Streamlit
    
    Args:
        metrics: Portfolio metrics dictionary
    """
    if not metrics:
        return

    st.subheader("📊 Portfolio Summary")

    # Signal distribution
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Stocks",
            metrics['total_stocks']
        )

    with col2:
        st.metric(
            "Buy Signals",
            metrics['buy_signals'],
            f"{metrics['buy_percentage']:.1f}%"
        )

    with col3:
        st.metric(
            "Hold Signals",
            metrics['hold_signals']
        )

    with col4:
        st.metric(
            "Sell Signals",
            metrics['sell_signals'],
            f"{metrics['sell_percentage']:.1f}%"
        )

    # Technical metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Avg Tech Score",
            f"{metrics['avg_tech_score']:.1f}"
        )

    with col2:
        st.metric(
            "Above MA40",
            metrics['above_ma40_count'],
            f"{metrics['above_ma40_percentage']:.1f}%"
        )

    with col3:
        st.metric(
            "Profitable",
            metrics['profitable_count'],
            f"{metrics['profitable_percentage']:.1f}%"
        )

    # Data source breakdown
    if metrics['data_sources']:
        st.subheader("📡 Data Sources")
        source_cols = st.columns(len(metrics['data_sources']))

        for i, (source, count) in enumerate(metrics['data_sources'].items()):
            with source_cols[i]:
                st.metric(
                    source.title(),
                    count,
                    f"{(count / metrics['total_stocks']) * 100:.1f}%"
                )


def filter_results_by_criteria(results, criteria):
    """
    Filter analysis results based on criteria
    
    Args:
        results: List of analysis results
        criteria: Dictionary of filter criteria
        
    Returns:
        list: Filtered results
    """
    filtered = []

    for result in results:
        # Skip error results
        if "error" in result and result.get("error") is not None:
            continue

        meets_criteria = True

        # Signal filter
        if 'signals' in criteria and criteria['signals']:
            signal = result.get('signal', 'HÅLL')
            if signal not in criteria['signals']:
                meets_criteria = False

        # Tech score filter
        if 'min_tech_score' in criteria:
            tech_score = result.get('tech_score', 0)
            if tech_score < criteria['min_tech_score']:
                meets_criteria = False

        # Data source filter
        if 'data_sources' in criteria and criteria['data_sources']:
            data_source = result.get('data_source', 'unknown')
            if data_source not in criteria['data_sources']:
                meets_criteria = False

        # MA40 filter
        if criteria.get('above_ma40_only', False):
            if not result.get('above_ma40', False):
                meets_criteria = False

        # Profitable filter
        if criteria.get('profitable_only', False):
            if not result.get('is_profitable', False):
                meets_criteria = False

        if meets_criteria:
            filtered.append(result)

    return filtered
