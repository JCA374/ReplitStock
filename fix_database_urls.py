#!/usr/bin/env python3
"""
Script to fix all DATABASE_URL references in the codebase
This replaces the old environment variable name with the correct one.
"""

import os
import re

def fix_database_url_references():
    """Fix all DATABASE_URL references in data/db_manager.py"""
    
    file_path = "data/db_manager.py"
    
    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace all DATABASE_URL references with proper environment variable access
    
    # Pattern 1: if DATABASE_URL:
    content = re.sub(
        r'if DATABASE_URL:',
        'supabase_url = os.getenv("SUPABASE_URL")\n    if supabase_url:',
        content
    )
    
    # Pattern 2: Remove any standalone DATABASE_URL references that cause errors
    # We'll replace them with the proper environment variable check
    content = re.sub(
        r'(\s+)if DATABASE_URL:',
        r'\1supabase_url = os.getenv("SUPABASE_URL")\n\1if supabase_url:',
        content
    )
    
    # Write the file back
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("Fixed DATABASE_URL references in db_manager.py")

if __name__ == "__main__":
    fix_database_url_references()