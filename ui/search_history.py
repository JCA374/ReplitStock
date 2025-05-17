"""
Module for managing search history separate from watchlist.
This allows users to search for stocks without automatically adding them to their watchlist.
"""
import json
import os
import time
from pathlib import Path

# Define the search history file location
SEARCH_HISTORY_FILE = "search_history.json"

def add_to_search_history(symbol, name, exchange="", sector=""):
    """
    Add a stock to search history without affecting watchlist.
    
    Args:
        symbol (str): Stock ticker symbol
        name (str): Company name
        exchange (str, optional): Stock exchange
        sector (str, optional): Company sector
        
    Returns:
        bool: True if added successfully, False otherwise
    """
    try:
        history = get_search_history()
        
        # Check if already in history
        if any(item['symbol'] == symbol for item in history):
            # Update last searched timestamp
            for item in history:
                if item['symbol'] == symbol:
                    item['last_searched'] = int(time.time())
                    break
        else:
            # Add new entry
            history.append({
                'symbol': symbol,
                'name': name,
                'exchange': exchange,
                'sector': sector,
                'last_searched': int(time.time())
            })
        
        # Save back to file
        with open(SEARCH_HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)
            
        return True
    except Exception as e:
        print(f"Error adding to search history: {str(e)}")
        return False

def get_search_history():
    """
    Get the search history.
    
    Returns:
        list: List of dictionaries containing search history entries
    """
    try:
        if not os.path.exists(SEARCH_HISTORY_FILE):
            return []
            
        with open(SEARCH_HISTORY_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error getting search history: {str(e)}")
        return []

def search_in_history(query):
    """
    Search within the history for matching stocks.
    
    Args:
        query (str): Search term
        
    Returns:
        list: List of matching stocks from history
    """
    history = get_search_history()
    query_lower = query.lower()
    
    matches = []
    for item in history:
        if (query_lower in item['symbol'].lower() or 
            (item['name'] and query_lower in item['name'].lower())):
            # Format for consistency with search results
            match = {
                'symbol': item['symbol'],
                'name': item['name'],
                'exchange': item.get('exchange', ''),
                'type': 'Stock',
                'country': '',
                'currency': ''
            }
            matches.append(match)
    
    return matches