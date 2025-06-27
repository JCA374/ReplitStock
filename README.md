# Stock Analysis Application

A comprehensive stock analysis tool built with Streamlit, focused on Swedish market stocks with advanced screening and analysis capabilities.

![Stock Analysis App](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)

## Features

- **📊 Batch Stock Analysis**: Analyze multiple stocks simultaneously with technical and fundamental metrics
- **🎯 Advanced Stock Scanner**: Custom filtering with Value & Momentum strategies
- **📝 Watchlist Management**: Create and manage multiple stock collections
- **🔍 Company Explorer**: Search and explore Swedish market companies
- **💾 Smart Caching**: Dual database system (SQLite + Supabase) with intelligent data management
- **📈 Technical Analysis**: RSI, MACD, moving averages, and trend analysis
- **💰 Fundamental Analysis**: P/E ratios, profit margins, revenue growth analysis

## Quick Start

### Option 1: Automated Setup (Recommended)

**Windows:**
```bash
# Download and run setup
git clone <your-repo-url>
cd stock-analysis-app
setup-windows.bat
```

**Mac/Linux:**
```bash
# Download and run setup
git clone <your-repo-url>
cd stock-analysis-app
chmod +x setup-linux-mac.sh
./setup-linux-mac.sh
```

### Option 2: Manual Setup

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd stock-analysis-app
   ```

2. **Create virtual environment:**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # Mac/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install streamlit pandas numpy sqlalchemy plotly matplotlib yfinance requests supabase pg8000 alpha-vantage trafilatura python-dotenv
   ```

4. **Run the application:**
   ```bash
   streamlit run app.py
   ```

5. **Open in browser:** http://localhost:8501

## VS Code Setup

For the best development experience in VS Code:

1. **Open the project folder in VS Code**
2. **Install recommended extensions:**
   - Python
   - Streamlit (optional)
3. **Use built-in tasks:**
   - Press `Ctrl+Shift+P`
   - Type "Tasks: Run Task"
   - Select "Run Streamlit App"

See [README-VS-Code-Setup.md](README-VS-Code-Setup.md) for detailed VS Code configuration.

## Configuration

### Environment Variables (Optional)

For live data and cloud features, create a `.env` file:

```env
# Alpha Vantage API (for real-time stock data)
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key

# Supabase (for cloud database)
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
```

### Getting API Keys

1. **Alpha Vantage** (Free): https://www.alphavantage.co/support/#api-key
2. **Supabase** (Free tier): https://supabase.com/

## Application Structure

```
stock-analysis-app/
├── app.py                    # Main Streamlit application
├── config.py                 # Configuration settings
├── helpers.py                # Utility functions
├── analysis/                 # Analysis modules
│   ├── bulk_scanner.py      # High-performance bulk analysis
│   ├── fundamental.py       # Fundamental analysis
│   ├── scanner.py           # Stock screening engine
│   ├── strategy.py          # Value & Momentum strategy
│   └── technical.py         # Technical indicators
├── data/                     # Data management
│   ├── db_connection.py     # Database connections
│   ├── db_integration.py    # Unified data access
│   ├── db_models.py         # Database models
│   ├── stock_data.py        # Stock data fetching
│   └── supabase_client.py   # Supabase integration
├── services/                 # Business logic
│   ├── company_explorer.py  # Company search
│   ├── stock_data_manager.py # Data operations
│   └── watchlist_manager.py # Watchlist operations
├── ui/                       # User interface components
│   ├── batch_analysis.py    # Batch analysis UI
│   ├── company_explorer.py  # Company explorer UI
│   ├── database_viewer.py   # Database viewer UI
│   ├── enhanced_scanner.py  # Advanced scanner UI
│   └── watchlist.py         # Watchlist management UI
└── .vscode/                  # VS Code configuration
    ├── launch.json          # Debug configuration
    ├── settings.json        # Editor settings
    └── tasks.json           # Build tasks
```

## Usage Guide

### 1. Batch Analysis
- Select a watchlist or enter stock symbols
- Choose analysis criteria
- Review technical and fundamental scores
- Export results for further analysis

### 2. Stock Scanner
- Set filtering criteria (P/E ratio, tech score, etc.)
- Choose scanning strategy (Value & Momentum)
- Review filtered results
- Add promising stocks to watchlist

### 3. Watchlist Management
- Create multiple themed watchlists
- Import/export watchlist data
- Track portfolio performance
- Manage stock collections

### 4. Company Explorer
- Search Swedish market companies
- Filter by sector and market cap
- Explore company fundamentals
- Add discoveries to watchlists

## Data Sources

- **Primary**: Alpha Vantage API (comprehensive financial data)
- **Fallback**: Yahoo Finance (free alternative)
- **Storage**: SQLite (local) + Supabase (cloud)
- **Market Focus**: Swedish stocks (OMXS30 and broader market)

## Performance Features

- **Bulk Data Loading**: Minimizes database queries
- **Parallel Processing**: Multi-threaded analysis
- **Smart Caching**: Reduces API calls
- **Progressive Loading**: Real-time progress updates

## Troubleshooting

### Common Issues

**App won't start:**
- Verify Python 3.11+ is installed
- Check virtual environment is activated
- Ensure all dependencies are installed

**No data showing:**
- App works offline with sample data
- Add API keys for live data
- Check database viewer for cached data

**Performance issues:**
- Reduce batch size for large analyses
- Enable caching for repeated queries
- Use database-only mode for faster scanning

### Windows Specific
- Use Command Prompt or PowerShell
- Ensure Python is in system PATH
- Run setup scripts as administrator if needed

### Getting Help
1. Check the built-in database viewer
2. Review VS Code setup guide
3. Verify environment variables
4. Test with smaller datasets first

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source. See LICENSE file for details.

## Architecture

Built with modern Python practices:
- **Framework**: Streamlit for rapid web development
- **Database**: SQLAlchemy ORM with dual database support
- **Analysis**: Pandas and NumPy for data processing
- **Visualization**: Plotly and Matplotlib for charts
- **APIs**: Integration with financial data providers