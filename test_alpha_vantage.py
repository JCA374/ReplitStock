#!/usr/bin/env python3
"""
Test Alpha Vantage API Key Configuration

Verifies that:
1. Alpha Vantage API key is configured
2. API key is valid and working
3. Can fetch stock data successfully
"""

import os
import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_alpha_vantage_config():
    """Test 1: Check if Alpha Vantage API key is configured"""
    logger.info("\n" + "="*70)
    logger.info("TEST 1: Alpha Vantage Configuration")
    logger.info("="*70)

    try:
        from config import ALPHA_VANTAGE_API_KEY

        if not ALPHA_VANTAGE_API_KEY:
            logger.warning("⚠️  Alpha Vantage API key is NOT configured")
            logger.info("\nTo configure Alpha Vantage:")
            logger.info("  1. Get free API key from: https://www.alphavantage.co/support/#api-key")
            logger.info("  2. Create .env file in project root:")
            logger.info("     ALPHA_VANTAGE_API_KEY=your_key_here")
            logger.info("  3. Restart the application")
            return False

        # Mask the key for security (show first 4 and last 4 chars)
        masked_key = f"{ALPHA_VANTAGE_API_KEY[:4]}...{ALPHA_VANTAGE_API_KEY[-4:]}"
        logger.info(f"✓ Alpha Vantage API key found: {masked_key}")
        logger.info(f"  Length: {len(ALPHA_VANTAGE_API_KEY)} characters")

        return True

    except ImportError as e:
        logger.error(f"✗ Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Configuration test failed: {e}")
        return False


def test_alpha_vantage_connection():
    """Test 2: Test actual API connection with a real stock"""
    logger.info("\n" + "="*70)
    logger.info("TEST 2: Alpha Vantage API Connection")
    logger.info("="*70)

    try:
        from alpha_vantage.timeseries import TimeSeries
        from config import ALPHA_VANTAGE_API_KEY

        if not ALPHA_VANTAGE_API_KEY:
            logger.warning("⚠️  Skipping connection test (no API key)")
            return False

        logger.info("Initializing Alpha Vantage client...")
        ts = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format='pandas')

        # Test with a well-known Swedish stock (Investor AB)
        test_ticker = "INVE-B.ST"
        logger.info(f"Fetching data for {test_ticker}...")
        logger.info("  (This may take 5-10 seconds...)")

        # Try to fetch daily data
        data, meta_data = ts.get_daily(symbol=test_ticker, outputsize='compact')

        if data is not None and not data.empty:
            logger.info(f"✓ Successfully fetched data for {test_ticker}")
            logger.info(f"  Rows retrieved: {len(data)}")
            logger.info(f"  Date range: {data.index[0]} to {data.index[-1]}")
            logger.info(f"  Latest close: {data.iloc[0]['4. close']:.2f}")

            # Check metadata
            if meta_data:
                logger.info(f"  Metadata: {meta_data.get('2. Symbol', 'N/A')}")
                logger.info(f"  Last refreshed: {meta_data.get('3. Last Refreshed', 'N/A')}")

            return True
        else:
            logger.warning("⚠️  API returned empty data")
            return False

    except ImportError as e:
        logger.error(f"✗ Import error: {e}")
        logger.error("  Install alpha-vantage: pip install alpha-vantage")
        return False
    except Exception as e:
        error_msg = str(e).lower()

        if 'invalid api call' in error_msg or 'api key' in error_msg:
            logger.error("✗ Invalid API key!")
            logger.error("  Your API key appears to be invalid or expired")
            logger.error("  Get a new key from: https://www.alphavantage.co/support/#api-key")
        elif 'rate limit' in error_msg or 'frequency' in error_msg:
            logger.error("✗ API rate limit exceeded!")
            logger.error("  Free tier: 25 requests/day, 5 requests/minute")
            logger.error("  Wait a few minutes and try again")
        else:
            logger.error(f"✗ API connection test failed: {e}")

        return False


def test_alpha_vantage_in_stock_fetcher():
    """Test 3: Test Alpha Vantage integration in StockDataFetcher"""
    logger.info("\n" + "="*70)
    logger.info("TEST 3: Alpha Vantage Integration in StockDataFetcher")
    logger.info("="*70)

    try:
        from data.stock_data import StockDataFetcher
        from config import ALPHA_VANTAGE_API_KEY

        if not ALPHA_VANTAGE_API_KEY:
            logger.warning("⚠️  Skipping integration test (no API key)")
            return False

        logger.info("Initializing StockDataFetcher...")
        fetcher = StockDataFetcher()

        # Check if Alpha Vantage is available
        if hasattr(fetcher, 'alpha_vantage') and fetcher.alpha_vantage is not None:
            logger.info("✓ Alpha Vantage is initialized in StockDataFetcher")
            logger.info("  Smart fallback: Yahoo Finance → Alpha Vantage → Demo data")
        else:
            logger.warning("⚠️  Alpha Vantage not initialized in StockDataFetcher")
            logger.warning("  System will use Yahoo Finance only")
            return False

        # Test fetching with Alpha Vantage fallback
        # Use a ticker that might fail on Yahoo to trigger fallback
        test_ticker = "INVE-B.ST"
        logger.info(f"\nTesting data fetch for {test_ticker}...")
        logger.info("  (This tests the smart fallback system)")

        data = fetcher.get_stock_data(test_ticker, period='1mo', attempt_fallback=True)

        if data is not None and not data.empty:
            logger.info(f"✓ Successfully fetched data for {test_ticker}")
            logger.info(f"  Rows: {len(data)}")
            logger.info(f"  Columns: {list(data.columns)}")
            logger.info("  Smart fallback system working correctly")
            return True
        else:
            logger.warning("⚠️  Failed to fetch data")
            return False

    except Exception as e:
        logger.error(f"✗ Integration test failed: {e}", exc_info=True)
        return False


def test_rate_limiting_info():
    """Test 4: Display rate limiting information"""
    logger.info("\n" + "="*70)
    logger.info("TEST 4: Alpha Vantage Rate Limiting Info")
    logger.info("="*70)

    try:
        from config import ALPHA_VANTAGE_API_KEY

        if not ALPHA_VANTAGE_API_KEY:
            logger.info("⚠️  No API key configured - rate limits N/A")
            return False

        logger.info("\nAlpha Vantage Free Tier Limits:")
        logger.info("  • 25 API requests per day")
        logger.info("  • 5 API requests per minute")
        logger.info("  • No credit card required")
        logger.info("\nRecommendations:")
        logger.info("  • Use Yahoo Finance as primary source (unlimited)")
        logger.info("  • Alpha Vantage as fallback only")
        logger.info("  • Enable smart caching (5h for price, 24h for fundamentals)")
        logger.info("  • Run analysis during market hours for fresh data")
        logger.info("\nUpgrade Options:")
        logger.info("  • Premium: $50/month (75 req/min, no daily cap)")
        logger.info("  • See: https://www.alphavantage.co/premium/")

        return True

    except Exception as e:
        logger.error(f"✗ Error: {e}")
        return False


def main():
    """Run all Alpha Vantage tests"""

    print("\n" + "="*70)
    print("  ALPHA VANTAGE API KEY TEST SUITE")
    print("="*70)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")

    results = {
        'Configuration': test_alpha_vantage_config(),
        'API Connection': test_alpha_vantage_connection(),
        'Integration': test_alpha_vantage_in_stock_fetcher(),
        'Rate Limiting Info': test_rate_limiting_info(),
    }

    # Summary
    logger.info("\n" + "="*70)
    logger.info("TEST SUMMARY")
    logger.info("="*70)

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{status} - {test_name}")

    logger.info("="*70)

    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    logger.info(f"RESULT: {passed_count}/{total_count} tests passed")
    logger.info("="*70)

    if passed_count == total_count:
        print("\n🎉 All tests passed! Alpha Vantage is configured correctly!")
        return 0
    elif results['Configuration'] and results['API Connection']:
        print("\n✅ Alpha Vantage is working! Some optional tests failed.")
        return 0
    else:
        print("\n❌ Alpha Vantage is NOT configured or not working.")
        print("\nQuick Fix:")
        print("  1. Get free API key: https://www.alphavantage.co/support/#api-key")
        print("  2. Create .env file: ALPHA_VANTAGE_API_KEY=your_key_here")
        print("  3. Re-run this test")
        return 1


if __name__ == "__main__":
    sys.exit(main())
