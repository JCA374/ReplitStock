# test/simple_pe_test.py - Standalone P/E Test (No Complex Imports)

"""
Simple P/E Ratio Test - No complex imports needed
Run this directly to debug P/E issues quickly
"""

import os
import sys
import json
from datetime import datetime


def test_basic_imports():
    """Test if basic required modules are available"""
    print("🔍 Testing Basic Imports...")

    required_modules = [
        ('yfinance', 'yf'),
        ('pandas', 'pd'),
        ('requests', 'requests')
    ]

    available_modules = {}

    for module_name, alias in required_modules:
        try:
            module = __import__(module_name)
            available_modules[module_name] = module
            print(f"  ✅ {module_name}")
        except ImportError as e:
            print(f"  ❌ {module_name}: {e}")
            available_modules[module_name] = None

    return available_modules


def test_yahoo_finance_pe_simple():
    """Simple Yahoo Finance P/E test"""
    print("\n📊 Testing Yahoo Finance P/E (Simple)...")

    try:
        import yfinance as yf

        # Test reliable US stocks
        test_stocks = ['AAPL', 'MSFT', 'GOOGL']
        results = {}

        for ticker in test_stocks:
            print(f"\n  Testing {ticker}:")

            try:
                stock = yf.Ticker(ticker)
                info = stock.info

                # Get P/E ratios
                trailing_pe = info.get('trailingPE')
                forward_pe = info.get('forwardPE')

                print(f"    Trailing P/E: {trailing_pe}")
                print(f"    Forward P/E: {forward_pe}")

                # What would our app logic use?
                app_pe = trailing_pe or forward_pe
                print(f"    App would use: {app_pe}")

                results[ticker] = {
                    'trailing_pe': trailing_pe,
                    'forward_pe': forward_pe,
                    'app_pe': app_pe,
                    'success': app_pe is not None
                }

                if app_pe:
                    print(f"    ✅ SUCCESS: P/E = {app_pe}")
                else:
                    print(f"    ❌ FAILED: No P/E data")

            except Exception as e:
                print(f"    ❌ Error: {e}")
                results[ticker] = {'error': str(e), 'success': False}

        # Summary
        successful = sum(1 for r in results.values()
                         if r.get('success', False))
        total = len(results)

        print(f"\n  📋 Yahoo Finance Summary:")
        print(
            f"    Success rate: {successful}/{total} ({successful/total*100:.1f}%)")

        return results

    except ImportError:
        print("  ❌ yfinance not available")
        return {}


def test_alpha_vantage_simple():
    """Simple Alpha Vantage test"""
    print("\n📊 Testing Alpha Vantage API...")

    # Try to get API key from environment or secrets
    api_key = None

    # Method 1: Environment variable
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')

    # Method 2: Try to load from streamlit secrets
    if not api_key:
        try:
            import streamlit as st
            api_key = st.secrets.get('ALPHA_VANTAGE_API_KEY')
        except:
            pass

    # Method 3: Try to load from secrets file
    if not api_key:
        secrets_path = os.path.join('..', '.streamlit', 'secrets.toml')
        if os.path.exists(secrets_path):
            try:
                with open(secrets_path, 'r') as f:
                    content = f.read()
                    for line in content.split('\n'):
                        if 'ALPHA_VANTAGE_API_KEY' in line and '=' in line:
                            api_key = line.split(
                                '=')[1].strip().strip('"').strip("'")
                            break
            except:
                pass

    if not api_key:
        print("  ❌ No Alpha Vantage API key found")
        print("  💡 Checked: Environment, Streamlit secrets, .streamlit/secrets.toml")
        return {}

    print(f"  ✅ API Key found: {'*' * 8}{api_key[-4:]}")

    try:
        import requests

        ticker = 'AAPL'
        url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={api_key}'

        print(f"  🌐 Testing API call for {ticker}...")
        response = requests.get(url)
        data = response.json()

        if 'PERatio' in data:
            pe_ratio = data['PERatio']
            print(f"  ✅ P/E Ratio: {pe_ratio}")

            # Show other available data
            fundamental_fields = ['PERatio', 'PEGRatio',
                                  'BookValue', 'DividendYield', 'EPS']
            print("  📈 Other fundamentals:")
            for field in fundamental_fields:
                value = data.get(field, 'N/A')
                print(f"    {field}: {value}")

            return {'success': True, 'pe_ratio': pe_ratio, 'data': data}

        elif 'Error Message' in data:
            print(f"  ❌ API Error: {data['Error Message']}")
            return {'success': False, 'error': data['Error Message']}

        elif 'Note' in data:
            print(f"  ⚠️ API Limit: {data['Note']}")
            return {'success': False, 'error': 'API limit reached'}

        else:
            print(f"  ❌ Unexpected response format")
            print(f"  🔍 Available keys: {list(data.keys())}")
            return {'success': False, 'error': 'Unexpected response', 'keys': list(data.keys())}

    except ImportError:
        print("  ❌ requests module not available")
        return {}
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return {'success': False, 'error': str(e)}


def test_your_app_config():
    """Test your app's configuration"""
    print("\n🔧 Testing Your App Configuration...")

    # Check if we can find your config file
    config_paths = [
        os.path.join('..', 'config.py'),
        'config.py',
        os.path.join('..', '..', 'config.py')
    ]

    config_found = False
    for path in config_paths:
        if os.path.exists(path):
            print(f"  ✅ Found config at: {path}")
            config_found = True
            break

    if not config_found:
        print("  ❌ config.py not found")
        print(f"  💡 Searched: {config_paths}")
        return False

    # Try to read Alpha Vantage key from config
    try:
        # Add parent directory to path to import config
        parent_dir = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)

        import config

        api_key = getattr(config, 'ALPHA_VANTAGE_API_KEY', None)
        if api_key:
            print(f"  ✅ Alpha Vantage key in config: {'*' * 8}{api_key[-4:]}")
        else:
            print("  ⚠️ No Alpha Vantage key in config")

        # Check other important config
        yahoo_enabled = getattr(config, 'YAHOO_FINANCE_ENABLED', None)
        print(f"  📊 Yahoo Finance enabled: {yahoo_enabled}")

        return True

    except ImportError as e:
        print(f"  ❌ Cannot import config: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Config error: {e}")
        return False


def diagnose_pe_issue(yf_results, av_results):
    """Diagnose the P/E issue based on test results"""
    print("\n🎯 P/E ISSUE DIAGNOSIS")
    print("=" * 30)

    # Count successful P/E retrievals
    yf_success = sum(1 for r in yf_results.values() if r.get('success', False))
    av_success = av_results.get('success', False)

    print(f"Yahoo Finance P/E success: {yf_success}/{len(yf_results)}")
    print(f"Alpha Vantage P/E success: {'Yes' if av_success else 'No'}")

    # Diagnosis
    if yf_success > 0 or av_success:
        print("\n✅ DIAGNOSIS: External APIs have P/E data")
        print("🚨 PROBLEM: Your app is not extracting/processing P/E correctly")
        print("\n💡 SOLUTION: Fix your app's get_fundamentals() function")
        print("📝 Location: data/stock_data.py")
        print("🔧 Fix: Ensure P/E extraction code like this exists:")
        print("""
    # In get_fundamentals() method:
    pe_ratio = info.get('trailingPE') or info.get('forwardPE')
    if pe_ratio is not None:
        fundamentals['pe_ratio'] = float(pe_ratio)
    else:
        fundamentals['pe_ratio'] = None
        """)

    elif yf_success == 0 and not av_success:
        print("\n❌ DIAGNOSIS: No external APIs working")
        print("🚨 PROBLEM: Network, API keys, or rate limits")
        print("\n💡 SOLUTIONS:")
        print("  1. Check internet connection")
        print("  2. Wait a few minutes (rate limits)")
        print("  3. Configure Alpha Vantage API key")
        print("  4. Try different stock tickers")

    else:
        print("\n🤔 DIAGNOSIS: Mixed results")
        print("💡 SOLUTION: Manual investigation needed")


def save_test_results(yf_results, av_results):
    """Save test results to file"""
    try:
        results = {
            'timestamp': datetime.now().isoformat(),
            'yahoo_finance': yf_results,
            'alpha_vantage': av_results
        }

        filename = f"simple_pe_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n💾 Results saved to: {filename}")

    except Exception as e:
        print(f"\n❌ Could not save results: {e}")


def main():
    """Run simple P/E test"""
    print("🧪 SIMPLE P/E RATIO TEST")
    print("=" * 40)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Directory: {os.getcwd()}")

    # Test basic imports
    modules = test_basic_imports()

    if not modules.get('yfinance'):
        print("\n❌ Cannot run tests: yfinance not available")
        print("💡 Install with: pip install yfinance")
        return 1

    # Test app configuration
    config_ok = test_your_app_config()

    # Test Yahoo Finance P/E
    yf_results = test_yahoo_finance_pe_simple()

    # Test Alpha Vantage P/E
    av_results = test_alpha_vantage_simple()

    # Diagnose the issue
    diagnose_pe_issue(yf_results, av_results)

    # Save results
    save_test_results(yf_results, av_results)

    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Return code based on results
    if any(r.get('success', False) for r in yf_results.values()) or av_results.get('success', False):
        return 0  # Success - external APIs work
    else:
        return 1  # Failure - no APIs work


if __name__ == "__main__":
    sys.exit(main())
