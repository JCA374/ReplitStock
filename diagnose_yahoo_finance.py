#!/usr/bin/env python3
"""
Yahoo Finance Connectivity Diagnostic Test

Tests multiple methods to access Yahoo Finance data for Swedish stocks.
Identifies which method works and provides recommendations.
"""

import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_1_basic_network():
    """Test 1: Basic network connectivity to Yahoo Finance"""
    print("\n" + "="*70)
    print("TEST 1: Basic Network Connectivity")
    print("="*70)

    try:
        import socket
        import ssl

        # Test DNS resolution
        print("\n1.1 DNS Resolution:")
        try:
            ip = socket.gethostbyname('finance.yahoo.com')
            print(f"  ✓ finance.yahoo.com resolves to {ip}")
        except Exception as e:
            print(f"  ✗ DNS resolution failed: {e}")
            return False

        # Test basic HTTP connection
        print("\n1.2 HTTP Connection:")
        try:
            import urllib.request

            # Simple GET request
            req = urllib.request.Request(
                'https://finance.yahoo.com',
                headers={'User-Agent': 'Mozilla/5.0'}
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                status = response.status
                print(f"  ✓ HTTP connection successful (status: {status})")
        except Exception as e:
            print(f"  ✗ HTTP connection failed: {e}")
            return False

        # Test SSL/TLS
        print("\n1.3 SSL/TLS Connection:")
        try:
            context = ssl.create_default_context()
            with socket.create_connection(('finance.yahoo.com', 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname='finance.yahoo.com') as ssock:
                    print(f"  ✓ SSL/TLS connection successful")
                    print(f"    Protocol: {ssock.version()}")
                    print(f"    Cipher: {ssock.cipher()[0]}")
        except Exception as e:
            print(f"  ✗ SSL/TLS connection failed: {e}")
            return False

        print("\n✓ Basic network connectivity: WORKING")
        return True

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        return False


def test_2_urllib_method():
    """Test 2: Fetch data using urllib (no external deps)"""
    print("\n" + "="*70)
    print("TEST 2: urllib Method (Built-in Python)")
    print("="*70)

    try:
        import urllib.request
        import json

        ticker = 'VOLV-B.ST'

        # Yahoo Finance query endpoint
        url = f'https://query2.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=5d'

        print(f"\nFetching {ticker} data with urllib...")

        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))

            if 'chart' in data and 'result' in data['chart']:
                result = data['chart']['result'][0]
                meta = result['meta']

                print(f"  ✓ Data fetched successfully")
                print(f"    Symbol: {meta.get('symbol')}")
                print(f"    Currency: {meta.get('currency')}")
                print(f"    Current Price: {meta.get('regularMarketPrice')}")
                print(f"    Data points: {len(result.get('timestamp', []))}")

                return True
            else:
                print(f"  ✗ Invalid response structure")
                return False

    except Exception as e:
        print(f"  ✗ urllib method failed: {e}")
        return False


def test_3_requests_method():
    """Test 3: Fetch data using requests library"""
    print("\n" + "="*70)
    print("TEST 3: requests Library Method")
    print("="*70)

    try:
        import requests

        ticker = 'VOLV-B.ST'
        url = f'https://query2.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=5d'

        print(f"\nFetching {ticker} data with requests...")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()

        if 'chart' in data and 'result' in data['chart']:
            result = data['chart']['result'][0]
            meta = result['meta']

            print(f"  ✓ Data fetched successfully")
            print(f"    Symbol: {meta.get('symbol')}")
            print(f"    Current Price: {meta.get('regularMarketPrice')}")
            print(f"    Data points: {len(result.get('timestamp', []))}")

            return True
        else:
            print(f"  ✗ Invalid response structure")
            return False

    except ImportError:
        print(f"  ⚠️  requests library not installed")
        print(f"     Install with: pip install requests")
        return False
    except Exception as e:
        print(f"  ✗ requests method failed: {e}")
        return False


def test_4_yfinance_original():
    """Test 4: Test current yfinance installation"""
    print("\n" + "="*70)
    print("TEST 4: yfinance Library (Current Installation)")
    print("="*70)

    try:
        import yfinance as yf

        print(f"\nyfinance version: {yf.__version__}")

        ticker = 'VOLV-B.ST'
        print(f"\nFetching {ticker} data with yfinance...")

        stock = yf.Ticker(ticker)
        hist = stock.history(period='5d')

        if not hist.empty:
            print(f"  ✓ Data fetched successfully")
            print(f"    Rows: {len(hist)}")
            print(f"    Columns: {list(hist.columns)}")
            print(f"    Latest close: {hist['Close'].iloc[-1]:.2f}")

            return True
        else:
            print(f"  ✗ No data returned")
            return False

    except Exception as e:
        print(f"  ✗ yfinance failed: {e}")
        print(f"\nError details:")
        import traceback
        traceback.print_exc()
        return False


def test_5_pandas_datareader():
    """Test 5: Try pandas_datareader as alternative"""
    print("\n" + "="*70)
    print("TEST 5: pandas_datareader (Alternative Library)")
    print("="*70)

    try:
        import pandas_datareader as pdr
        from datetime import datetime, timedelta

        ticker = 'VOLV-B.ST'
        end = datetime.now()
        start = end - timedelta(days=5)

        print(f"\nFetching {ticker} data with pandas_datareader...")

        df = pdr.get_data_yahoo(ticker, start=start, end=end)

        if not df.empty:
            print(f"  ✓ Data fetched successfully")
            print(f"    Rows: {len(df)}")
            print(f"    Latest close: {df['Close'].iloc[-1]:.2f}")

            return True
        else:
            print(f"  ✗ No data returned")
            return False

    except ImportError:
        print(f"  ⚠️  pandas_datareader not installed")
        print(f"     Install with: pip install pandas-datareader")
        return False
    except Exception as e:
        print(f"  ✗ pandas_datareader failed: {e}")
        return False


def check_dependencies():
    """Check SSL/TLS dependencies"""
    print("\n" + "="*70)
    print("DEPENDENCY CHECK")
    print("="*70)

    print("\nPython SSL/TLS Info:")
    try:
        import ssl
        print(f"  OpenSSL version: {ssl.OPENSSL_VERSION}")
        print(f"  Has SNI: {ssl.HAS_SNI}")
        print(f"  Has TLSv1_3: {hasattr(ssl, 'HAS_TLSv1_3') and ssl.HAS_TLSv1_3}")
    except Exception as e:
        print(f"  Error: {e}")

    print("\nInstalled Packages:")
    packages = [
        'yfinance',
        'requests',
        'urllib3',
        'curl_cffi',
        'certifi',
        'pandas'
    ]

    for pkg in packages:
        try:
            mod = __import__(pkg)
            version = getattr(mod, '__version__', 'unknown')
            print(f"  ✓ {pkg}: {version}")
        except ImportError:
            print(f"  ✗ {pkg}: Not installed")


def main():
    """Run all diagnostic tests"""

    print("\n" + "="*70)
    print("  YAHOO FINANCE CONNECTIVITY DIAGNOSTIC")
    print("="*70)
    print("\nThis will test multiple methods to access Yahoo Finance data")
    print("for Swedish stocks and identify which method works.\n")

    # Check dependencies first
    check_dependencies()

    # Run tests
    results = {
        'Basic Network': test_1_basic_network(),
        'urllib (built-in)': test_2_urllib_method(),
        'requests library': test_3_requests_method(),
        'yfinance (current)': test_4_yfinance_original(),
        'pandas_datareader': test_5_pandas_datareader(),
    }

    # Summary
    print("\n" + "="*70)
    print("  TEST RESULTS SUMMARY")
    print("="*70)

    for test_name, passed in results.items():
        status = "✓ WORKING" if passed else "✗ FAILED"
        print(f"{status:12} - {test_name}")

    print("="*70)

    # Recommendations
    print("\n" + "="*70)
    print("  RECOMMENDATIONS")
    print("="*70)

    working_methods = [name for name, passed in results.items() if passed]

    if working_methods:
        print(f"\n✓ Working methods found: {len(working_methods)}")
        print("\nRecommended approach:")

        if results.get('urllib (built-in)'):
            print("  1. Use urllib (built-in, no dependencies)")
            print("     - Most reliable, no SSL issues")
            print("     - Requires manual JSON parsing")

        if results.get('requests library'):
            print("  2. Use requests library (simple, reliable)")
            print("     - Clean API, good error handling")
            print("     - One external dependency")

        if results.get('yfinance (current)'):
            print("  3. Keep current yfinance setup")
            print("     - Already working")
            print("     - Most convenient API")
        else:
            print("  3. Fix yfinance (recommended for convenience)")
            print("     - Uninstall curl_cffi: pip uninstall curl_cffi")
            print("     - Reinstall yfinance: pip install --force-reinstall yfinance")

    else:
        print("\n✗ No working methods found!")
        print("\nTroubleshooting steps:")
        print("  1. Check internet connection")
        print("  2. Check firewall/proxy settings")
        print("  3. Update SSL certificates: pip install --upgrade certifi")
        print("  4. Try from different network")

    print("="*70 + "\n")

    return 0 if any(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
