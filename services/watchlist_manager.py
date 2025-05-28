import streamlit as st
import pandas as pd
import logging
from datetime import datetime, timedelta
import time

from data.db_manager import (
    add_to_watchlist,
    remove_from_watchlist,
    get_watchlist
)

class WatchlistManager:
    """
    Manager for watchlist operations.
    Allows multiple watchlists to be maintained.
    """
    
    def __init__(self):
        """
        Initialize the watchlist manager with SQLite storage.
        """
        self.logger = logging.getLogger(__name__)
        
        # Default watchlists
        self.default_watchlists = [
            {"name": "My Watchlist", "stocks": []},
            {"name": "Potential Buys", "stocks": []},
            {"name": "Portfolio", "stocks": []}
        ]
        
        # Initialize watchlists if not in session
        if 'watchlists' not in st.session_state:
            # Try to load from database
            db_watchlist = get_watchlist()
            
            if db_watchlist:
                # Create a single watchlist from database
                all_stocks = [item['ticker'] for item in db_watchlist]
                self.default_watchlists[0]["stocks"] = all_stocks
                
            st.session_state.watchlists = self.default_watchlists
            
        # Ensure all default watchlists exist
        self._ensure_default_watchlists()
        
        # Initialize active watchlist index if not set
        if 'active_watchlist_index' not in st.session_state:
            st.session_state.active_watchlist_index = 0
    
    def get_all_watchlists(self):
        """
        Get all watchlists.
        
        Returns:
            list: List of watchlist dictionaries
        """
        return st.session_state.watchlists
    
    def add_watchlist(self, name):
        """
        Add a new watchlist.
        
        Args:
            name (str): Name of the watchlist
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Check if watchlist name already exists
        existing_names = [w["name"] for w in st.session_state.watchlists]
        if name in existing_names:
            return False
            
        # Add new watchlist
        st.session_state.watchlists.append({"name": name, "stocks": []})
        return True
    
    def _ensure_default_watchlists(self):
        """
        Ensure all default watchlists exist in the session state.
        """
        default_names = set(wl["name"] for wl in self.default_watchlists)
        existing_names = set(wl["name"] for wl in st.session_state.watchlists)
        
        # Add missing watchlists
        for name in default_names - existing_names:
            for wl in self.default_watchlists:
                if wl["name"] == name:
                    st.session_state.watchlists.append({"name": name, "stocks": []})
    
    def delete_watchlist(self, index):
        """
        Delete a watchlist.
        
        Args:
            index (int): Index of the watchlist to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        if index < 0 or index >= len(st.session_state.watchlists):
            return False
            
        # Don't delete the default watchlist
        if index == 0:
            return False
            
        # Delete watchlist
        st.session_state.watchlists.pop(index)
        return True
    
    def add_stock_to_watchlist(self, watchlist_index, ticker, add_to_db=True):
        """
        Add a stock to a specific watchlist.
        
        Args:
            watchlist_index (int): Index of the watchlist
            ticker (str): Stock ticker symbol
            add_to_db (bool): Whether to add to database
            
        Returns:
            bool: True if successful, False otherwise
        """
        if watchlist_index < 0 or watchlist_index >= len(st.session_state.watchlists):
            return False
            
        # Get watchlist
        watchlist = st.session_state.watchlists[watchlist_index]
        
        # Check if stock already exists
        if ticker in watchlist["stocks"]:
            return False
            
        # Add to watchlist
        watchlist["stocks"].append(ticker)
        
        # Add to database if requested
        if add_to_db and watchlist_index == 0:  # Only sync the main watchlist
            try:
                from data.stock_data import StockDataFetcher
                
                # Get stock info for database
                fetcher = StockDataFetcher()
                info = fetcher.get_stock_info(ticker)
                
                # Add to database
                add_to_watchlist(
                    ticker, 
                    info.get('shortName', ticker),
                    info.get('exchange', ''),
                    info.get('sector', '')
                )
            except Exception as e:
                self.logger.error(f"Error adding stock to database: {e}")
        
        return True
    
    def remove_stock_from_watchlist(self, watchlist_index, ticker, remove_from_db=True):
        """
        Remove a stock from a specific watchlist.
        
        Args:
            watchlist_index (int): Index of the watchlist
            ticker (str): Stock ticker symbol
            remove_from_db (bool): Whether to remove from database
            
        Returns:
            bool: True if successful, False otherwise
        """
        if watchlist_index < 0 or watchlist_index >= len(st.session_state.watchlists):
            return False
            
        # Get watchlist
        watchlist = st.session_state.watchlists[watchlist_index]
        
        # Check if stock exists
        if ticker not in watchlist["stocks"]:
            return False
            
        # Remove from watchlist
        watchlist["stocks"].remove(ticker)
        
        # Remove from database if requested
        if remove_from_db and watchlist_index == 0:  # Only sync the main watchlist
            try:
                remove_from_watchlist(ticker)
            except Exception as e:
                self.logger.error(f"Error removing stock from database: {e}")
        
        return True
    def get_active_watchlist_index(self):
        """Get the index of the currently active watchlist."""
        return st.session_state.active_watchlist_index
        
    def get_active_watchlist(self):
        """Get the currently active watchlist."""
        return st.session_state.watchlists[self.get_active_watchlist_index()]
        
    def set_active_watchlist(self, index):
        """Set the active watchlist by index."""
        if 0 <= index < len(st.session_state.watchlists):
            st.session_state.active_watchlist_index = index
            return True
        return False

    def rename_watchlist(self, index, new_name):
        """
        Rename a watchlist.

        Args:
            index (int): Index of the watchlist to rename
            new_name (str): New name for the watchlist

        Returns:
            bool: True if successful, False otherwise
        """
        if index < 0 or index >= len(st.session_state.watchlists):
            return False

        # Check if the new name is empty or already exists
        if not new_name or new_name in [wl["name"] for wl in st.session_state.watchlists]:
            return False

        # Rename watchlist
        st.session_state.watchlists[index]["name"] = new_name
        return True

    def delete_watchlist(self, index):
        """
        Delete a watchlist.
        
        Args:
            index (int): Index of the watchlist to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        if index < 0 or index >= len(st.session_state.watchlists):
            return False
            
        # Don't delete the default watchlist
        if index == 0:
            return False
            
        # Delete watchlist
        st.session_state.watchlists.pop(index)
        return True

