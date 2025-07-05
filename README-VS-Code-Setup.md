# VS Code Setup for Stock Analysis App

This guide helps you set up and run the Stock Analysis App in VS Code on Windows, Mac, or Linux after downloading from GitHub.

## Quick Start

### For Windows Users:
1. Download/clone this repository
2. Double-click `setup-windows.bat` to automatically set everything up
3. Open the folder in VS Code
4. Press `Ctrl+Shift+P` → Type "Tasks: Run Task" → Select "Run Streamlit App"
5. App opens at http://localhost:8501

### For Mac/Linux Users:
1. Download/clone this repository
2. Run `./setup-linux-mac.sh` in terminal
3. Open the folder in VS Code
4. Press `Ctrl+Shift+P` → Type "Tasks: Run Task" → Select "Run Streamlit App"
5. App opens at http://localhost:8501

## Manual Setup (if scripts don't work)

### Prerequisites
- Python 3.11 or higher
- VS Code with Python extension

### Step-by-Step Setup

1. **Open terminal in VS Code** (`Ctrl+` ` or View → Terminal)

2. **Create virtual environment:**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Mac/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install required packages:**
   ```bash
   pip install streamlit pandas numpy sqlalchemy plotly matplotlib yfinance requests supabase pg8000 alpha-vantage trafilatura python-dotenv
   ```

4. **Run the app:**
   ```bash
   streamlit run app.py
   ```

## VS Code Features

### Quick Actions
- **F5**: Start debugging the app
- **Ctrl+Shift+P** → "Tasks: Run Task" → "Run Streamlit App": Start the app
- **Ctrl+Shift+P** → "Tasks: Run Task" → "Open App in Browser": Open app in browser

### Debugging
- Set breakpoints in Python files
- Use F5 to start debugging mode
- View variables and step through code

### Terminal Commands
```bash
# Activate environment (Windows)
venv\Scripts\activate

# Activate environment (Mac/Linux)
source venv/bin/activate

# Run app
streamlit run app.py

# Run with debug info
streamlit run app.py --logger.level debug
```

## Configuration (Optional)

### API Keys
1. Copy `.env.template` to `.env`
2. Add your API keys:
   ```
   ALPHA_VANTAGE_API_KEY=your_key_here
   SUPABASE_URL=your_url_here
   SUPABASE_KEY=your_key_here
   ```

### VS Code Settings
The app includes VS Code configuration files:
- `.vscode/settings.json`: Python and Streamlit settings
- `.vscode/launch.json`: Debug configurations
- `.vscode/tasks.json`: Quick tasks for running the app

## Troubleshooting

### Common Issues

**"Python not found"**
- Install Python from python.org
- Make sure Python is added to PATH

**"pip not recognized"**
- Use `python -m pip` instead of `pip`

**"Port already in use"**
- Change port in command: `streamlit run app.py --server.port 5001`

**"Module not found"**
- Make sure virtual environment is activated
- Reinstall packages: `pip install -r requirements.txt`

### Windows Specific
- If scripts don't run, right-click → "Run as administrator"
- Use Command Prompt or PowerShell, not Git Bash

### Performance Tips
- The app works offline with SQLite database
- Add API keys for live data updates
- Use "Database Viewer" tab to see cached data

## App Features

- **Batch Analysis**: Scan multiple stocks at once
- **Watchlist Management**: Create and manage stock lists
- **Technical Analysis**: RSI, MACD, moving averages
- **Fundamental Analysis**: P/E ratios, profit margins
- **Database Viewer**: See cached data and analysis results
- **Company Explorer**: Search Swedish market stocks

## Support

If you encounter issues:
1. Check that Python 3.11+ is installed
2. Verify virtual environment is activated
3. Try manual setup steps
4. Check VS Code Python extension is installed