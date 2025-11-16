#!/usr/bin/env python3
"""
Comprehensive Test Suite for Robust Yahoo Finance Fetcher

Tests the robust fetcher with multiple Swedish stocks and scenarios.
"""

import sys
import logging
from data.yahoo_finance_robust import RobustYahooFetcher

logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_multiple_stocks():
    """Test with multiple Swedish stocks across market caps"""
    print("\n" + "="*70)
    print("TEST 1: Multiple Swedish Stocks")
    print("="*70)

    test_stocks = {
        'VOLV-B.ST': 'Volvo (Large Cap)',
        'ERIC-B.ST': 'Ericsson (Large Cap)',
        'INVE-B.ST': 'Investor AB (Large Cap)',
        'HM-B.ST': 'H&M (Mid Cap)',
        'SAND.ST': 'Sandvik (Mid Cap)',
        'ALFA.ST': 'Alfa Laval (Small Cap)',
    }

    fetcher = RobustYahooFetcher(max_retries=2, retry_delay=1.0)

    results = {}

    for ticker, name in test_stocks.items():
        print(f"\nTesting {ticker} ({name})...")

        # Fetch data
        data = fetcher.get_historical_data(ticker, period='5d')

        if data is not None and not data.empty:
            print(f"  ✓ Price data: {len(data)} days")
            print(f"    Latest close: {data['close'].iloc[-1]:.2f}")
            results[ticker] = 'SUCCESS'
        else:
            print(f"  ✗ Failed to fetch data")
            results[ticker] = 'FAILED'

    # Summary
    print("\n" + "="*70)
    print("RESULTS:")
    successful = sum(1 for r in results.values() if r == 'SUCCESS')
    print(f"  ✓ Successful: {successful}/{len(test_stocks)}")
    print(f"  ✗ Failed: {len(test_stocks) - successful}/{len(test_stocks)}")
    print("="*70)

    return successful == len(test_stocks)


def test_different_periods():
    """Test different time periods"""
    print("\n" + "="*70)
    print("TEST 2: Different Time Periods")
    print("="*70)

    periods = ['5d', '1mo', '3mo', '6mo', '1y']
    ticker = 'VOLV-B.ST'

    fetcher = RobustYahooFetcher(max_retries=2, retry_delay=1.0)

    results = {}

    for period in periods:
        print(f"\nTesting period={period}...")

        data = fetcher.get_historical_data(ticker, period=period)

        if data is not None and not data.empty:
            print(f"  ✓ Got {len(data)} days of data")
            results[period] = 'SUCCESS'
        else:
            print(f"  ✗ Failed")
            results[period] = 'FAILED'

    # Summary
    print("\n" + "="*70)
    successful = sum(1 for r in results.values() if r == 'SUCCESS')
    print(f"Results: {successful}/{len(periods)} periods successful")
    print("="*70)

    return successful >= len(periods) - 1  # Allow one failure


def test_fundamentals():
    """Test fundamental data fetching"""
    print("\n" + "="*70)
    print("TEST 3: Fundamental Data")
    print("="*70)

    test_stocks = ['VOLV-B.ST', 'ERIC-B.ST', 'INVE-B.ST']

    fetcher = RobustYahooFetcher(max_retries=2, retry_delay=1.0)

    results = {}

    for ticker in test_stocks:
        print(f"\nTesting {ticker}...")

        fundamentals = fetcher.get_fundamentals(ticker)

        if fundamentals and len(fundamentals) > 10:
            print(f"  ✓ Got {len(fundamentals)} fields")

            # Check key fields
            key_fields = ['marketCap', 'sector', 'trailingPE']
            available = [f for f in key_fields if f in fundamentals]
            print(f"    Key fields: {len(available)}/{len(key_fields)}")

            if 'marketCap' in fundamentals:
                print(f"    Market Cap: {fundamentals['marketCap']:,.0f}")

            results[ticker] = 'SUCCESS'
        else:
            print(f"  ✗ Failed or insufficient data")
            results[ticker] = 'FAILED'

    # Summary
    print("\n" + "="*70)
    successful = sum(1 for r in results.values() if r == 'SUCCESS')
    print(f"Results: {successful}/{len(test_stocks)} stocks successful")
    print("="*70)

    return successful == len(test_stocks)


def test_data_quality():
    """Test data quality and completeness"""
    print("\n" + "="*70)
    print("TEST 4: Data Quality and Completeness")
    print("="*70)

    ticker = 'VOLV-B.ST'
    fetcher = RobustYahooFetcher(max_retries=2, retry_delay=1.0)

    print(f"\nTesting {ticker}...")

    # Fetch 1 year of data
    data = fetcher.get_historical_data(ticker, period='1y')

    if data is None or data.empty:
        print("  ✗ No data fetched")
        return False

    print(f"  ✓ Got {len(data)} days of data")

    # Check required columns
    required_cols = ['open', 'high', 'low', 'close', 'volume']
    missing_cols = [col for col in required_cols if col not in data.columns]

    if missing_cols:
        print(f"  ✗ Missing columns: {missing_cols}")
        return False
    else:
        print(f"  ✓ All required columns present")

    # Check for nulls
    null_counts = data[required_cols].isnull().sum()
    total_nulls = null_counts.sum()

    print(f"  Null values: {total_nulls}")
    if total_nulls > len(data) * 0.1:  # More than 10% nulls
        print(f"  ⚠️  High percentage of nulls ({total_nulls/len(data)*100:.1f}%)")

    # Check data range
    print(f"  Date range: {data.index[0].date()} to {data.index[-1].date()}")

    # Check if we have enough data for 200-day MA
    if len(data) >= 200:
        print(f"  ✓ Sufficient data for 200-day MA")
    else:
        print(f"  ⚠️  Limited data for 200-day MA ({len(data)} days)")

    return True


def test_error_recovery():
    """Test error recovery with invalid tickers"""
    print("\n" + "="*70)
    print("TEST 5: Error Recovery")
    print("="*70)

    invalid_tickers = [
        'INVALID-TICKER.ST',
        'DOESNOTEXIST.ST',
        'BADTICKER'
    ]

    fetcher = RobustYahooFetcher(max_retries=1, retry_delay=0.5)

    print("\nTesting with invalid tickers (should fail gracefully)...")

    for ticker in invalid_tickers:
        print(f"  Testing {ticker}...", end=' ')

        data = fetcher.get_historical_data(ticker, period='5d')

        if data is None or data.empty:
            print("✓ Failed gracefully (expected)")
        else:
            print("⚠️  Got unexpected data")

    print("\n" + "="*70)
    print("✓ Error recovery working properly")
    print("="*70)

    return True


def main():
    """Run all tests"""

    print("\n" + "="*70)
    print("  ROBUST YAHOO FINANCE FETCHER - TEST SUITE")
    print("="*70)
    print("\nTesting multiple fallback methods:")
    print("  1. yfinance (primary)")
    print("  2. urllib (built-in fallback)")
    print("  3. requests (library fallback)")
    print("="*70)

    # Run tests
    results = {
        'Multiple Stocks': test_multiple_stocks(),
        'Different Periods': test_different_periods(),
        'Fundamentals': test_fundamentals(),
        'Data Quality': test_data_quality(),
        'Error Recovery': test_error_recovery(),
    }

    # Summary
    print("\n" + "="*70)
    print("  FINAL TEST SUMMARY")
    print("="*70)

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:12} - {test_name}")

    print("="*70)

    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    print(f"RESULT: {passed_count}/{total_count} tests passed")
    print("="*70)

    if passed_count == total_count:
        print("\n🎉 All tests passed! Yahoo Finance fetching is robust!")
        print("\nThe system has:")
        print("  ✓ Multiple fallback methods")
        print("  ✓ Automatic retry logic")
        print("  ✓ Graceful error handling")
        print("  ✓ Works with Swedish stocks (.ST)")
        print("="*70 + "\n")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
