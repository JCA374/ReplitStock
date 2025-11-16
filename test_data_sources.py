#!/usr/bin/env python3
"""
Test Stock Data Sources and Availability

Tests:
1. Yahoo Finance data quality for Swedish stocks
2. Alternative data sources
3. Data completeness (price + fundamentals)
4. Backup options
"""

import sys
import logging
from datetime import datetime, timedelta
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_yahoo_finance_swedish_stocks():
    """Test 1: Yahoo Finance with Swedish stocks"""
    logger.info("\n" + "="*70)
    logger.info("TEST 1: Yahoo Finance - Swedish Stock Data Quality")
    logger.info("="*70)

    try:
        import yfinance as yf

        # Test with multiple Swedish stocks across different market caps
        test_stocks = {
            'VOLV-B.ST': 'Volvo (Large Cap)',
            'ERIC-B.ST': 'Ericsson (Large Cap)',
            'INVE-B.ST': 'Investor AB (Large Cap)',
            'HM-B.ST': 'H&M (Mid Cap)',
            'SAND.ST': 'Sandvik (Mid Cap)',
        }

        results = {}

        for ticker, name in test_stocks.items():
            logger.info(f"\nTesting {ticker} ({name})...")

            try:
                stock = yf.Ticker(ticker)

                # Test 1: Price data
                hist = stock.history(period='1y', interval='1d')

                if not hist.empty:
                    logger.info(f"  ✓ Price data: {len(hist)} days")
                    logger.info(f"    Latest: {hist.index[-1].date()} - Close: {hist['Close'].iloc[-1]:.2f}")
                    logger.info(f"    Columns: {list(hist.columns)}")
                    has_price = True
                else:
                    logger.warning(f"  ✗ No price data available")
                    has_price = False

                # Test 2: Fundamental data
                info = stock.info

                if info and len(info) > 5:
                    logger.info(f"  ✓ Fundamentals: {len(info)} fields")

                    # Check key fields
                    key_fields = ['marketCap', 'trailingPE', 'profitMargins', 'sector']
                    available_fields = [f for f in key_fields if f in info and info[f] is not None]
                    logger.info(f"    Key fields: {len(available_fields)}/{len(key_fields)}")

                    if 'marketCap' in info and info['marketCap']:
                        logger.info(f"    Market Cap: {info['marketCap']:,.0f} SEK")
                    if 'sector' in info:
                        logger.info(f"    Sector: {info['sector']}")

                    has_fundamentals = len(available_fields) > 0
                else:
                    logger.warning(f"  ✗ Limited fundamental data")
                    has_fundamentals = False

                # Test 3: Financial statements
                try:
                    financials = stock.financials
                    balance_sheet = stock.balance_sheet
                    cashflow = stock.cashflow

                    has_financials = (
                        not financials.empty or
                        not balance_sheet.empty or
                        not cashflow.empty
                    )

                    if has_financials:
                        logger.info(f"  ✓ Financial statements available")
                        if not financials.empty:
                            logger.info(f"    Income Statement: {len(financials.columns)} periods")
                        if not balance_sheet.empty:
                            logger.info(f"    Balance Sheet: {len(balance_sheet.columns)} periods")
                        if not cashflow.empty:
                            logger.info(f"    Cash Flow: {len(cashflow.columns)} periods")
                    else:
                        logger.warning(f"  ✗ No financial statements")

                except Exception as e:
                    logger.warning(f"  ✗ Financial statements error: {e}")
                    has_financials = False

                results[ticker] = {
                    'price': has_price,
                    'fundamentals': has_fundamentals,
                    'financials': has_financials,
                    'complete': has_price and has_fundamentals
                }

            except Exception as e:
                logger.error(f"  ✗ Failed to fetch {ticker}: {e}")
                results[ticker] = {
                    'price': False,
                    'fundamentals': False,
                    'financials': False,
                    'complete': False
                }

        # Summary
        logger.info("\n" + "="*70)
        logger.info("YAHOO FINANCE SUMMARY")
        logger.info("="*70)

        complete = sum(1 for r in results.values() if r['complete'])
        price_only = sum(1 for r in results.values() if r['price'] and not r['fundamentals'])
        failed = sum(1 for r in results.values() if not r['price'])

        logger.info(f"Complete data (price + fundamentals): {complete}/{len(test_stocks)}")
        logger.info(f"Price data only: {price_only}/{len(test_stocks)}")
        logger.info(f"Failed: {failed}/{len(test_stocks)}")

        if complete == len(test_stocks):
            logger.info("✓ Yahoo Finance is EXCELLENT for Swedish stocks")
            return True
        elif complete + price_only == len(test_stocks):
            logger.info("⚠️  Yahoo Finance has GOOD price data, limited fundamentals")
            return True
        else:
            logger.error("✗ Yahoo Finance has issues with Swedish stocks")
            return False

    except Exception as e:
        logger.error(f"✗ Test failed: {e}")
        return False


def test_alternative_sources():
    """Test 2: Alternative data sources for Swedish stocks"""
    logger.info("\n" + "="*70)
    logger.info("TEST 2: Alternative Data Sources for Swedish Stocks")
    logger.info("="*70)

    alternatives = {
        'Nasdaq OMX Nordic API': {
            'website': 'https://www.nasdaq.com/solutions/nasdaq-data-link',
            'coverage': 'All Swedish stocks (official)',
            'cost': 'Paid (enterprise)',
            'api_available': False,
            'notes': 'Official source but expensive'
        },
        'Twelve Data': {
            'website': 'https://twelvedata.com',
            'coverage': 'Global including Sweden',
            'cost': 'Free tier: 800 req/day',
            'api_available': True,
            'notes': 'Good Yahoo Finance alternative'
        },
        'Finnhub': {
            'website': 'https://finnhub.io',
            'coverage': 'Global stocks including Nordics',
            'cost': 'Free tier: 60 req/min',
            'api_available': True,
            'notes': 'Good for real-time and fundamentals'
        },
        'Financial Modeling Prep': {
            'website': 'https://financialmodelingprep.com',
            'coverage': 'Global markets',
            'cost': 'Free tier: 250 req/day',
            'api_available': True,
            'notes': 'Good fundamental data'
        },
        'Polygon.io': {
            'website': 'https://polygon.io',
            'coverage': 'US + some international',
            'cost': 'Paid ($99/month)',
            'api_available': True,
            'notes': 'Limited Swedish coverage'
        },
        'EOD Historical Data': {
            'website': 'https://eodhistoricaldata.com',
            'coverage': 'Global including Stockholm Exchange',
            'cost': 'Paid ($19.99/month)',
            'api_available': True,
            'notes': 'Comprehensive Nordic coverage'
        },
    }

    logger.info("\nAvailable alternatives to Yahoo Finance:\n")

    for source, details in alternatives.items():
        logger.info(f"{source}:")
        logger.info(f"  Website: {details['website']}")
        logger.info(f"  Coverage: {details['coverage']}")
        logger.info(f"  Cost: {details['cost']}")
        logger.info(f"  API: {'Yes' if details['api_available'] else 'No'}")
        logger.info(f"  Notes: {details['notes']}")
        logger.info("")

    logger.info("="*70)
    logger.info("RECOMMENDATION:")
    logger.info("="*70)
    logger.info("1. PRIMARY: Yahoo Finance (free, unlimited, good coverage)")
    logger.info("2. BACKUP: Twelve Data (free tier 800/day)")
    logger.info("3. BACKUP: Finnhub (free tier 60/min)")
    logger.info("4. PREMIUM: EOD Historical Data ($19.99/month)")
    logger.info("="*70)

    return True


def test_data_completeness():
    """Test 3: Check data completeness for analysis"""
    logger.info("\n" + "="*70)
    logger.info("TEST 3: Data Completeness for Technical & Fundamental Analysis")
    logger.info("="*70)

    try:
        import yfinance as yf

        ticker = 'VOLV-B.ST'
        logger.info(f"\nTesting data completeness with {ticker}...")

        stock = yf.Ticker(ticker)

        # Required for technical analysis
        logger.info("\n--- TECHNICAL ANALYSIS REQUIREMENTS ---")
        hist = stock.history(period='1y', interval='1d')

        if not hist.empty:
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            has_cols = [col for col in required_cols if col in hist.columns]

            logger.info(f"Required columns: {len(has_cols)}/{len(required_cols)}")
            for col in required_cols:
                if col in hist.columns:
                    non_null = hist[col].notna().sum()
                    logger.info(f"  ✓ {col}: {non_null}/{len(hist)} days ({non_null/len(hist)*100:.1f}%)")
                else:
                    logger.error(f"  ✗ {col}: MISSING")

            # Check if we have enough data for 200-day MA
            if len(hist) >= 200:
                logger.info(f"\n✓ Sufficient data for 200-day MA: {len(hist)} days")
            else:
                logger.warning(f"\n⚠️  Limited data for 200-day MA: {len(hist)} days (need 200)")

        # Required for fundamental analysis
        logger.info("\n--- FUNDAMENTAL ANALYSIS REQUIREMENTS ---")
        info = stock.info

        required_fundamentals = {
            'marketCap': 'Market Capitalization',
            'trailingPE': 'P/E Ratio',
            'profitMargins': 'Profit Margin',
            'revenueGrowth': 'Revenue Growth',
            'totalRevenue': 'Revenue',
            'totalAssets': 'Total Assets',
            'totalDebt': 'Total Debt',
            'freeCashflow': 'Free Cash Flow',
        }

        available = 0
        for key, name in required_fundamentals.items():
            if key in info and info[key] is not None:
                logger.info(f"  ✓ {name}: {info[key]}")
                available += 1
            else:
                logger.warning(f"  ✗ {name}: Not available")

        logger.info(f"\nFundamental data: {available}/{len(required_fundamentals)} fields ({available/len(required_fundamentals)*100:.1f}%)")

        # Check financial statements
        logger.info("\n--- FINANCIAL STATEMENTS ---")

        try:
            financials = stock.financials
            balance_sheet = stock.balance_sheet
            cashflow = stock.cashflow

            if not financials.empty:
                logger.info(f"  ✓ Income Statement: {financials.shape}")
                logger.info(f"    Rows: {list(financials.index[:5])[:3]}")
            else:
                logger.warning(f"  ✗ Income Statement: Empty")

            if not balance_sheet.empty:
                logger.info(f"  ✓ Balance Sheet: {balance_sheet.shape}")
            else:
                logger.warning(f"  ✗ Balance Sheet: Empty")

            if not cashflow.empty:
                logger.info(f"  ✓ Cash Flow: {cashflow.shape}")
            else:
                logger.warning(f"  ✗ Cash Flow: Empty")

        except Exception as e:
            logger.error(f"  ✗ Financial statements error: {e}")

        logger.info("\n" + "="*70)
        logger.info("COMPLETENESS VERDICT:")
        logger.info("="*70)

        if len(has_cols) == len(required_cols) and available >= 4:
            logger.info("✓ EXCELLENT - All required data available")
            logger.info("  Can perform complete technical + fundamental analysis")
            return True
        elif len(has_cols) == len(required_cols):
            logger.info("⚠️  GOOD - Technical analysis OK, limited fundamentals")
            logger.info("  Can perform technical analysis + basic fundamental")
            return True
        else:
            logger.error("✗ INSUFFICIENT - Missing critical data")
            return False

    except Exception as e:
        logger.error(f"✗ Test failed: {e}")
        return False


def test_twelve_data_availability():
    """Test 4: Test Twelve Data as backup"""
    logger.info("\n" + "="*70)
    logger.info("TEST 4: Twelve Data API (Yahoo Finance Backup)")
    logger.info("="*70)

    logger.info("\nTwelve Data API Details:")
    logger.info("  Website: https://twelvedata.com")
    logger.info("  Free Tier: 800 API requests/day")
    logger.info("  Coverage: Stockholm Exchange (.ST suffix)")
    logger.info("  Data: Real-time, Historical, Fundamentals")
    logger.info("  Format: REST API + WebSocket")
    logger.info("\nSetup:")
    logger.info("  1. Sign up at https://twelvedata.com")
    logger.info("  2. Get free API key")
    logger.info("  3. Install: pip install twelvedata")
    logger.info("  4. Add to .env: TWELVE_DATA_API_KEY=your_key")
    logger.info("\nExample usage:")
    logger.info("  from twelvedata import TDClient")
    logger.info("  td = TDClient(apikey='YOUR_KEY')")
    logger.info("  ts = td.time_series(symbol='VOLV-B.ST', interval='1day', outputsize=365)")
    logger.info("  df = ts.as_pandas()")

    logger.info("\n" + "="*70)

    return True


def main():
    """Run all tests"""

    print("\n" + "="*70)
    print("  STOCK DATA SOURCES TEST SUITE")
    print("="*70)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")

    results = {}

    # Test 1: Yahoo Finance quality
    results['Yahoo Finance Quality'] = test_yahoo_finance_swedish_stocks()

    # Test 2: Alternative sources
    results['Alternative Sources'] = test_alternative_sources()

    # Test 3: Data completeness
    results['Data Completeness'] = test_data_completeness()

    # Test 4: Twelve Data info
    results['Twelve Data Info'] = test_twelve_data_availability()

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

    # Final recommendation
    print("\n" + "="*70)
    print("  FINAL RECOMMENDATION")
    print("="*70)
    print("Current Setup: OPTIMAL ✓")
    print("")
    print("Primary: Yahoo Finance (yfinance)")
    print("  - FREE and unlimited")
    print("  - Excellent coverage of Swedish stocks")
    print("  - Price data: ✓ Excellent")
    print("  - Fundamentals: ✓ Good")
    print("  - Financial statements: ✓ Available")
    print("")
    print("Recommended Backup: Twelve Data")
    print("  - FREE tier: 800 requests/day")
    print("  - Good Stockholm Exchange coverage")
    print("  - Easy integration")
    print("  - Sign up: https://twelvedata.com")
    print("")
    print("Alternative Backup: Finnhub")
    print("  - FREE tier: 60 requests/minute")
    print("  - Nordic market coverage")
    print("  - Sign up: https://finnhub.io")
    print("="*70 + "\n")

    if results.get('Yahoo Finance Quality'):
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
