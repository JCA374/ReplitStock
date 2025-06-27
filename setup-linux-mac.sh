#!/bin/bash

echo "Setting up Stock Analysis App for Linux/Mac..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3.11+ first."
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "Failed to create virtual environment"
    exit 1
fi

# Activate virtual environment and install packages
echo "Activating virtual environment and installing packages..."
source venv/bin/activate

# Install core packages
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

if [ $? -ne 0 ]; then
    echo "Failed to install packages"
    exit 1
fi

# Create .env file template
echo "Creating .env template..."
cat > .env.template << 'EOF'
# Copy this file to .env and add your API keys
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_key_here
EOF

echo ""
echo "Setup complete! To run the app:"
echo "1. Open this folder in VS Code"
echo "2. Press Ctrl+Shift+P and run 'Tasks: Run Task' then select 'Run Streamlit App'"
echo "   OR"
echo "3. Open terminal and run: source venv/bin/activate && streamlit run app.py --server.port 5000"
echo ""
echo "The app will open at http://localhost:5000"