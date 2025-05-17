"""
Theme switcher utility for the Stock Analysis App.
Handles switching between dark and light modes.
"""
import streamlit as st
import os

def get_current_theme():
    """
    Read the current theme from config.toml and return theme settings.
    
    Returns:
        str: Current theme ('light' or 'dark')
    """
    try:
        # Check if .streamlit/config.toml exists
        if not os.path.exists('.streamlit/config.toml'):
            return 'light'  # Default to light if file doesn't exist
        
        # Read the config.toml file
        with open('.streamlit/config.toml', 'r') as f:
            config_content = f.read()
        
        # Check if 'base = "dark"' is in the file
        if 'base = "dark"' in config_content:
            return 'dark'
        else:
            return 'light'
    except Exception:
        return 'light'  # Default to light if any error occurs

def toggle_theme():
    """
    Toggle between dark and light themes by updating config.toml.
    """
    current_theme = get_current_theme()
    new_theme = 'light' if current_theme == 'dark' else 'dark'
    
    # Define theme settings
    if new_theme == 'dark':
        theme_settings = """[theme]
primaryColor = "#1E88E5"
base = "dark"
backgroundColor = "#0E1117"
secondaryBackgroundColor = "#262730"
textColor = "#FAFAFA"
"""
    else:  # light theme
        theme_settings = """[theme]
primaryColor = "#1E88E5"
base = "light"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
"""
    
    # Read the current config
    try:
        with open('.streamlit/config.toml', 'r') as f:
            config_content = f.read()
        
        # Check if the [theme] section exists
        if '[theme]' in config_content:
            # Replace the theme section
            lines = config_content.split('\n')
            new_lines = []
            in_theme_section = False
            for line in lines:
                if line.strip() == '[theme]':
                    in_theme_section = True
                    new_lines.append(line)  # Keep the [theme] line
                elif in_theme_section and line.strip() and line.strip()[0] == '[':
                    # We've reached a new section after [theme]
                    in_theme_section = False
                    new_lines.append(line)
                elif not in_theme_section:
                    new_lines.append(line)
                # Skip existing theme lines
            
            # Find where to insert theme settings
            theme_idx = new_lines.index('[theme]')
            # Insert theme settings after [theme] line
            new_content = '\n'.join(new_lines[:theme_idx+1]) + '\n' + theme_settings.strip() + '\n\n' + '\n'.join(new_lines[theme_idx+1:])
        else:
            # If no theme section exists, add it to the end
            new_content = config_content + '\n\n' + theme_settings
        
        # Write the new config
        with open('.streamlit/config.toml', 'w') as f:
            f.write(new_content)
            
        # Set a flag to indicate theme change for app restart
        st.session_state.theme_changed = True
        
        return new_theme
    except Exception as e:
        st.error(f"Failed to toggle theme: {e}")
        return current_theme