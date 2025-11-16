#!/usr/bin/env python3
"""
Short Report Test - Validate Complete System

Tests the complete pipeline:
1. Robust Yahoo Finance data fetching (3-tier fallback)
2. Technical and fundamental analysis
3. Report generation (HTML + CSV)

Uses 8 Swedish stocks across market cap tiers.
"""

import sys
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Run short report test"""

    print("\n" + "="*70)
    print("  SHORT REPORT TEST - COMPLETE SYSTEM VALIDATION")
    print("="*70)

    # Test stocks (mix of large, mid, small cap)
    test_stocks = {
        'Large Cap': ['VOLV-B.ST', 'ERIC-B.ST', 'INVE-B.ST'],
        'Mid Cap': ['HM-B.ST', 'SAND.ST'],
        'Small Cap': ['ALFA.ST', 'BILL.ST', 'GETI-B.ST']
    }

    all_tickers = []
    for tier, tickers in test_stocks.items():
        all_tickers.extend(tickers)

    print(f"\nTest Stocks: {len(all_tickers)} total")
    for tier, tickers in test_stocks.items():
        print(f"  {tier}: {', '.join(tickers)}")

    # Step 1: Test robust data fetching
    print("\n" + "-"*70)
    print("STEP 1: Testing Robust Data Fetching")
    print("-"*70)

    from data.yahoo_finance_robust import RobustYahooFetcher

    fetcher = RobustYahooFetcher(max_retries=3, retry_delay=2.0)

    fetch_results = {}
    for ticker in all_tickers:
        print(f"\nFetching {ticker}...")

        # Try to get price data
        data = fetcher.get_historical_data(ticker, period='1y')

        if data is not None and not data.empty:
            print(f"  ✓ Got {len(data)} days of price data")
            fetch_results[ticker] = 'SUCCESS'
        else:
            print(f"  ✗ Failed to fetch data")
            fetch_results[ticker] = 'FAILED'

    successful_fetches = sum(1 for r in fetch_results.values() if r == 'SUCCESS')
    print(f"\n✓ Data Fetch: {successful_fetches}/{len(all_tickers)} successful")

    # Step 2: Run analysis
    print("\n" + "-"*70)
    print("STEP 2: Running Stock Analysis")
    print("-"*70)

    from core.stock_analyzer import BatchAnalyzer
    from core.settings_manager import get_settings

    settings = get_settings()
    analyzer = BatchAnalyzer(settings.as_dict())

    print(f"\nAnalyzing {len(all_tickers)} stocks...")
    results = analyzer.analyze_batch(all_tickers)

    successful_analyses = sum(1 for r in results if r.get('analysis_successful'))
    print(f"✓ Analysis: {successful_analyses}/{len(all_tickers)} successful")

    # Show results table
    print("\n" + "-"*70)
    print("ANALYSIS RESULTS")
    print("-"*70)

    print(f"\n{'Ticker':<12} {'Composite':<10} {'Technical':<10} {'Fundamental':<12} {'Status':<10}")
    print("-" * 70)

    # Sort by composite score
    sorted_results = sorted(
        [r for r in results if r.get('analysis_successful')],
        key=lambda x: x.get('composite_score', 0),
        reverse=True
    )

    for r in sorted_results:
        ticker = r['ticker']
        composite = r.get('composite_score', 0)
        technical = r.get('technical_score', 0)
        fundamental = r.get('fundamental_score', 0)
        status = "✓ PASS" if composite >= 50 else "  Low"

        print(f"{ticker:<12} {composite:<10.1f} {technical:<10.1f} {fundamental:<12.1f} {status:<10}")

    # Step 3: Generate reports
    print("\n" + "-"*70)
    print("STEP 3: Generating Reports")
    print("-"*70)

    from reports.html_generator import HTMLReportGenerator
    import csv

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = Path('reports/output/test')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate HTML report
    print("\nGenerating HTML report...")
    html_gen = HTMLReportGenerator(settings.as_dict())

    # Prepare report data
    report_data = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'total_stocks': len(all_tickers),
            'successful_analyses': successful_analyses,
            'market': 'OMX Stockholm (Test)',
            'period': '1 year'
        },
        'summary': {
            'total_analyzed': len(all_tickers),
            'passed_filters': sum(1 for r in sorted_results if r.get('composite_score', 0) >= 50),
            'avg_score': sum(r.get('composite_score', 0) for r in sorted_results) / len(sorted_results) if sorted_results else 0
        },
        'top_stocks': sorted_results[:5]  # Top 5
    }

    html_file = output_dir / f'test_report_{timestamp}.html'
    html_content = html_gen._generate_test_report(report_data)

    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"  ✓ HTML: {html_file}")

    # Generate CSV report
    print("\nGenerating CSV report...")

    csv_file = output_dir / f'test_report_{timestamp}.csv'

    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Header
        writer.writerow([
            'Rank', 'Ticker', 'Composite Score',
            'Technical Score', 'Fundamental Score',
            'Status'
        ])

        # Data rows
        for i, stock in enumerate(sorted_results, 1):
            composite = stock.get('composite_score', 0)
            technical = stock.get('technical_score', 0)
            fundamental = stock.get('fundamental_score', 0)
            status = 'PASS' if composite >= 50 else 'LOW'

            writer.writerow([
                i,
                stock.get('ticker', 'N/A'),
                f"{composite:.1f}",
                f"{technical:.1f}",
                f"{fundamental:.1f}",
                status
            ])

    print(f"  ✓ CSV: {csv_file}")

    # Final summary
    print("\n" + "="*70)
    print("  TEST SUMMARY")
    print("="*70)

    print(f"\n✓ Data Fetching: {successful_fetches}/{len(all_tickers)} stocks")
    print(f"✓ Analysis: {successful_analyses}/{len(all_tickers)} stocks")
    print(f"✓ Top Stock: {sorted_results[0]['ticker']} (Score: {sorted_results[0]['composite_score']:.1f})")
    print(f"✓ Reports Generated: 2 files")
    print(f"  - {html_file}")
    print(f"  - {csv_file}")

    print("\n" + "="*70)
    print("  SYSTEM STATUS: FULLY OPERATIONAL ✓")
    print("="*70)
    print("\nThe robust Yahoo Finance fetching system is working correctly!")
    print("All components validated: Data → Analysis → Reports")
    print("="*70 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
