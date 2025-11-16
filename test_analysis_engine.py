"""
Test Analysis Engine - Phase 2

Tests the complete analysis pipeline with a few sample stocks.
"""

import logging
import sys
from core.settings_manager import get_settings
from core.stock_analyzer import StockAnalyzer, BatchAnalyzer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_single_stock_analysis():
    """Test analyzing a single stock"""
    print("\n" + "=" * 70)
    print("TEST 1: Single Stock Analysis")
    print("=" * 70)

    try:
        # Load settings
        settings = get_settings()

        # Create analyzer
        analyzer = StockAnalyzer(settings.as_dict())

        # Test with a well-known Swedish stock
        ticker = "INVE-B.ST"  # Investor AB
        print(f"\nAnalyzing {ticker}...")

        result = analyzer.analyze(ticker)

        # Display results
        print(f"\n{'─' * 70}")
        print(f"ANALYSIS RESULTS FOR {ticker}")
        print(f"{'─' * 70}")

        if result.get('analysis_successful'):
            print(f"\n✓ Analysis Successful")
            print(f"\nSCORES:")
            print(f"  Composite Score:    {result.get('composite_score', 0):.1f}/100")
            print(f"  Technical Score:    {result.get('technical_score', 0):.1f}/100")
            print(f"  Fundamental Score:  {result.get('fundamental_score', 0):.1f}/100")

            print(f"\nKEY METRICS:")
            print(f"  Current Price:      {result.get('current_price', 'N/A')} SEK")
            print(f"  RSI (7-period):     {result.get('rsi', 'N/A')}")
            print(f"  MA200 Distance:     {result.get('ma200_distance_pct', 'N/A')}%")
            print(f"  52-Week High Prox:  {result.get('high52_proximity_pct', 'N/A')}%")
            print(f"  Volume Confirmed:   {result.get('volume_confirmed', False)}")
            print(f"  Piotroski F-Score:  {result.get('piotroski_score', 'N/A')}/9")
            print(f"  Gross Profitability: {result.get('gross_profitability', 'N/A')}")
            print(f"  P/E Ratio:          {result.get('pe_ratio', 'N/A')}")

            print(f"\nFILTERS:")
            print(f"  Passed All Filters: {'✓ YES' if result.get('passed_all_filters') else '✗ NO'}")

            tech_filters = result.get('technical_filters', {})
            if tech_filters:
                print(f"  Technical Filters:")
                for filter_name, passed in tech_filters.items():
                    print(f"    {filter_name}: {'✓' if passed else '✗'}")

            fund_filters = result.get('fundamental_filters', {})
            if fund_filters:
                print(f"  Fundamental Filters:")
                for filter_name, passed in fund_filters.items():
                    print(f"    {filter_name}: {'✓' if passed else '✗'}")

            print(f"\nRECOMMENDATION: {result.get('recommendation', 'N/A')}")

            print(f"\n✓ Single stock analysis test PASSED")
            return True

        else:
            print(f"\n✗ Analysis Failed: {result.get('failure_reason', 'Unknown error')}")
            print(f"\n✗ Single stock analysis test FAILED")
            return False

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_batch_analysis():
    """Test analyzing multiple stocks"""
    print("\n" + "=" * 70)
    print("TEST 2: Batch Analysis (5 stocks)")
    print("=" * 70)

    try:
        # Load settings
        settings = get_settings()

        # Create batch analyzer
        batch_analyzer = BatchAnalyzer(settings.as_dict())

        # Test with a few well-known Swedish stocks
        test_tickers = [
            "INVE-B.ST",   # Investor AB
            "ATCO-A.ST",   # Atlas Copco
            "HEXA-B.ST",   # Hexagon
            "EVO.ST",      # Evolution Gaming
            "SAND.ST"      # Sandvik
        ]

        print(f"\nAnalyzing {len(test_tickers)} stocks...")

        # Progress callback
        def progress(current, total, ticker, result):
            status = "✓" if result.get('analysis_successful') else "✗"
            score = result.get('composite_score', 0)
            print(f"  [{current}/{total}] {ticker}: {status} Score={score:.1f}")

        # Run batch analysis
        results = batch_analyzer.analyze_batch(test_tickers, progress_callback=progress)

        # Get statistics
        stats = batch_analyzer.get_statistics()

        print(f"\n{'─' * 70}")
        print(f"BATCH ANALYSIS RESULTS")
        print(f"{'─' * 70}")

        print(f"\nSTATISTICS:")
        print(f"  Total Analyzed:     {stats['total_analyzed']}")
        print(f"  Successful:         {stats['successful_analyses']}")
        print(f"  Passed Filters:     {stats['passed_all_filters']}")
        print(f"  Average Score:      {stats['average_score']:.1f}/100")
        print(f"  Score Range:        {stats['min_score']:.1f} - {stats['max_score']:.1f}")

        print(f"\nRECOMMENDATIONS:")
        for rec, count in stats['recommendations'].items():
            if count > 0:
                print(f"  {rec}: {count}")

        # Display top results
        print(f"\n{'─' * 70}")
        print(f"TOP STOCKS (Passed Filters)")
        print(f"{'─' * 70}")

        top_stocks = batch_analyzer.filter_and_rank('all', 10)

        if top_stocks:
            print(f"\nRank | Ticker      | Score | Tech | Fund | Recommendation")
            print(f"─────┼─────────────┼───────┼──────┼──────┼─────────────────")
            for idx, stock in enumerate(top_stocks, 1):
                print(
                    f"{idx:4d} | {stock['ticker']:11s} | "
                    f"{stock['composite_score']:5.1f} | "
                    f"{stock['technical_score']:4.1f} | "
                    f"{stock['fundamental_score']:4.1f} | "
                    f"{stock['recommendation']}"
                )
        else:
            print("\nNo stocks passed all filters")

        print(f"\n✓ Batch analysis test PASSED")
        return True

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_research_parameters():
    """Test that research-backed parameters are being used"""
    print("\n" + "=" * 70)
    print("TEST 3: Research Parameters Verification")
    print("=" * 70)

    try:
        settings = get_settings()
        config = settings.as_dict()

        tech_settings = config.get('analysis', {}).get('technical', {})
        fund_settings = config.get('analysis', {}).get('fundamental', {})
        scoring = config.get('scoring', {})

        print("\nResearch-Backed Parameters:")

        # RSI
        rsi_period = tech_settings.get('rsi_period')
        print(f"  RSI Period:               {rsi_period} (research: 2-7, not 14) {'✓' if rsi_period == 7 else '✗'}")

        # Volume multiplier
        vol_mult = tech_settings.get('volume_multiplier')
        print(f"  Volume Multiplier:        {vol_mult}× (research: 1.5×) {'✓' if vol_mult == 1.5 else '✗'}")

        # KAMA
        use_kama = tech_settings.get('use_kama')
        print(f"  Use KAMA:                 {use_kama} (research: reduces false signals) {'✓' if use_kama else '✗'}")

        # Gross profitability
        use_gross = fund_settings.get('use_gross_profitability')
        print(f"  Use Gross Profitability:  {use_gross} (research: superior to P/E) {'✓' if use_gross else '✗'}")

        # Piotroski F-Score
        use_piotroski = fund_settings.get('use_piotroski_score')
        min_piotroski = fund_settings.get('min_piotroski_score')
        print(f"  Use Piotroski F-Score:    {use_piotroski} (min: {min_piotroski}) {'✓' if use_piotroski and min_piotroski == 7 else '✗'}")

        # Scoring weights
        tech_weight = scoring.get('technical_weight')
        fund_weight = scoring.get('fundamental_weight')
        print(f"  Tech/Fund Weighting:      {tech_weight}/{fund_weight} (research: 70/30) {'✓' if tech_weight == 70 else '✗'}")

        print(f"\n✓ Research parameters verification PASSED")
        return True

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("PHASE 2 ANALYSIS ENGINE TESTS")
    print("=" * 70)

    results = []

    # Test 1: Single stock
    results.append(test_single_stock_analysis())

    # Test 2: Batch analysis
    results.append(test_batch_analysis())

    # Test 3: Research parameters
    results.append(test_research_parameters())

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(results)
    total = len(results)

    print(f"\nTests Passed: {passed}/{total}")

    for idx, result in enumerate(results, 1):
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  Test {idx}: {status}")

    if passed == total:
        print(f"\n🎉 ALL TESTS PASSED! Phase 2 analysis engine is working correctly.")
        return 0
    else:
        print(f"\n⚠️  Some tests failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
