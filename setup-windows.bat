@echo off
echo Setting up Stock Analysis App for Windows...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH. Please install Python 3.11+ from python.org
    pause
    exit /b 1
)

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo Failed to create virtual environment
    pause
    exit /b 1
)

REM Activate virtual environment and install packages
echo Activating virtual environment and installing packages...
call venv\Scripts\activate.bat

REM Install core packages
pip install streamlit>=1.29.0
pip install pandas>=2.0.0
pip install numpy>=1.24.0
pip install sqlalchemy>=2.0.0
pip install plotly>=5.17.0
pip install matplotlib>=3.7.0
pip install yfinance>=0.2.25
pip install requests>=2.31.0
pip install supabase>=2.0.0
pip install pg8000>=1.30.0
pip install alpha-vantage>=2.3.1
pip install trafilatura>=1.6.0
pip install python-dotenv>=1.0.0

if %errorlevel% neq 0 (
    echo Failed to install packages
    pause
    exit /b 1
)

REM Create .env file template
echo Creating .env template...
echo # Copy this file to .env and add your API keys > .env.template
echo ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here >> .env.template
echo SUPABASE_URL=your_supabase_url_here >> .env.template
echo SUPABASE_KEY=your_supabase_key_here >> .env.template

echo.
echo Setup complete! To run the app:
echo 1. Open this folder in VS Code
echo 2. Press Ctrl+Shift+P and run "Tasks: Run Task" then select "Run Streamlit App"
echo    OR
echo 3. Open terminal and run: venv\Scripts\streamlit.exe run app.py
echo.
echo The app will open at http://localhost:8501
pause