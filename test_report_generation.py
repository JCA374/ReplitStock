"""
Test Report Generation - Phase 3

Creates sample analysis results and generates reports in all formats.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

from core.settings_manager import get_settings
from reports import WeeklyReportOrchestrator, ReportData

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_sample_results() -> list:
    """
    Create sample analysis results for testing

    Returns:
        List of sample stock results
    """
    logger.info("Creating sample analysis results...")

    # Sample stocks with varying scores and characteristics
    sample_results = [
        # Large cap - STRONG BUY
        {
            'ticker': 'INVE-B.ST',
            'analysis_date': datetime.now().isoformat(),
            'analysis_successful': True,
            'composite_score': 92.5,
            'technical_score': 94.2,
            'fundamental_score': 88.7,
            'passed_all_filters': True,
            'technical_filters': {'ma200_filter': True, 'ma20_filter': True, 'rsi_filter': True, 'volume_filter': True},
            'fundamental_filters': {'profitable_filter': True, 'gross_profit_filter': True, 'piotroski_filter': True, 'pe_filter': True},
            'recommendation': 'STRONG BUY',
            'current_price': 245.60,
            'market_cap': 852000000000,
            'market_cap_tier': 'large_cap',
            'rsi': 62,
            'ma200_distance_pct': 12.3,
            'ma20_distance_pct': 4.2,
            'high52_proximity_pct': 94.0,
            'volume_confirmed': True,
            'piotroski_score': 8,
            'gross_profitability': 0.345,
            'pe_ratio': 18.3,
            'profit_margin': 0.284,
            'revenue_growth': 0.123,
            'technical_indicators': {'macd_bullish': True, 'above_ma200': True, 'above_ma20': True}
        },

        # Large cap - BUY
        {
            'ticker': 'ATCO-A.ST',
            'analysis_date': datetime.now().isoformat(),
            'analysis_successful': True,
            'composite_score': 89.3,
            'technical_score': 91.5,
            'fundamental_score': 85.1,
            'passed_all_filters': True,
            'technical_filters': {'ma200_filter': True, 'ma20_filter': True, 'rsi_filter': True, 'volume_filter': True},
            'fundamental_filters': {'profitable_filter': True, 'gross_profit_filter': True, 'piotroski_filter': True, 'pe_filter': True},
            'recommendation': 'BUY',
            'current_price': 187.40,
            'market_cap': 745000000000,
            'market_cap_tier': 'large_cap',
            'rsi': 58,
            'ma200_distance_pct': 10.1,
            'ma20_distance_pct': 3.8,
            'high52_proximity_pct': 91.0,
            'volume_confirmed': True,
            'piotroski_score': 8,
            'gross_profitability': 0.312,
            'pe_ratio': 22.1,
            'profit_margin': 0.247,
            'revenue_growth': 0.105,
            'technical_indicators': {'macd_bullish': True, 'above_ma200': True, 'above_ma20': True}
        },

        # Mid cap - BUY
        {
            'ticker': 'EVO.ST',
            'analysis_date': datetime.now().isoformat(),
            'analysis_successful': True,
            'composite_score': 86.5,
            'technical_score': 89.7,
            'fundamental_score': 80.9,
            'passed_all_filters': True,
            'technical_filters': {'ma200_filter': True, 'ma20_filter': True, 'rsi_filter': True, 'volume_filter': True},
            'fundamental_filters': {'profitable_filter': True, 'gross_profit_filter': True, 'piotroski_filter': True, 'pe_filter': True},
            'recommendation': 'BUY',
            'current_price': 1234.50,
            'market_cap': 67000000000,
            'market_cap_tier': 'mid_cap',
            'rsi': 56,
            'ma200_distance_pct': 8.4,
            'ma20_distance_pct': 2.9,
            'high52_proximity_pct': 88.0,
            'volume_confirmed': True,
            'piotroski_score': 7,
            'gross_profitability': 0.387,
            'pe_ratio': 28.5,
            'profit_margin': 0.421,
            'revenue_growth': 0.234,
            'technical_indicators': {'macd_bullish': True, 'above_ma200': True, 'above_ma20': True}
        },

        # Small cap - HOLD
        {
            'ticker': 'SMALL-A.ST',
            'analysis_date': datetime.now().isoformat(),
            'analysis_successful': True,
            'composite_score': 72.3,
            'technical_score': 76.4,
            'fundamental_score': 64.1,
            'passed_all_filters': True,
            'technical_filters': {'ma200_filter': True, 'ma20_filter': True, 'rsi_filter': True, 'volume_filter': True},
            'fundamental_filters': {'profitable_filter': True, 'gross_profit_filter': True, 'piotroski_filter': True, 'pe_filter': True},
            'recommendation': 'HOLD',
            'current_price': 45.60,
            'market_cap': 5000000000,
            'market_cap_tier': 'small_cap',
            'rsi': 54,
            'ma200_distance_pct': 5.2,
            'ma20_distance_pct': 1.8,
            'high52_proximity_pct': 82.0,
            'volume_confirmed': True,
            'piotroski_score': 7,
            'gross_profitability': 0.245,
            'pe_ratio': 15.8,
            'profit_margin': 0.089,
            'revenue_growth': 0.067,
            'technical_indicators': {'macd_bullish': True, 'above_ma200': True, 'above_ma20': True}
        },

        # Failed filters - SKIP
        {
            'ticker': 'FAIL-A.ST',
            'analysis_date': datetime.now().isoformat(),
            'analysis_successful': True,
            'composite_score': 58.2,
            'technical_score': 62.1,
            'fundamental_score': 51.3,
            'passed_all_filters': False,
            'technical_filters': {'ma200_filter': False, 'ma20_filter': True, 'rsi_filter': True, 'volume_filter': False},
            'fundamental_filters': {'profitable_filter': True, 'gross_profit_filter': False, 'piotroski_filter': False, 'pe_filter': True},
            'recommendation': 'SKIP',
            'current_price': 123.45,
            'market_cap': 45000000000,
            'market_cap_tier': 'mid_cap',
            'rsi': 45,
            'ma200_distance_pct': -2.3,
            'ma20_distance_pct': 0.8,
            'high52_proximity_pct': 65.0,
            'volume_confirmed': False,
            'piotroski_score': 5,
            'gross_profitability': 0.145,
            'pe_ratio': 32.4,
            'profit_margin': 0.045,
            'revenue_growth': -0.023,
            'technical_indicators': {'macd_bullish': False, 'above_ma200': False, 'above_ma20': True}
        }
    ]

    logger.info(f"Created {len(sample_results)} sample results")

    return sample_results


def test_report_generation():
    """Test complete report generation pipeline"""

    print("\n" + "=" * 70)
    print("PHASE 3 REPORT GENERATION TEST")
    print("=" * 70)

    try:
        # Load settings
        print("\n1. Loading settings...")
        settings = get_settings()
        print(f"   ✓ Settings loaded from {settings.config_path}")

        # Create sample results
        print("\n2. Creating sample analysis results...")
        results = create_sample_results()
        print(f"   ✓ Created {len(results)} sample results")

        # Create report orchestrator
        print("\n3. Initializing report orchestrator...")
        orchestrator = WeeklyReportOrchestrator(settings.as_dict())
        print(f"   ✓ Orchestrator initialized")

        # Generate reports
        print("\n4. Generating reports...")
        generated_files = orchestrator.generate_weekly_report(results)

        # Verify files
        print("\n5. Verifying generated files...")
        all_exist = True

        for format_name, file_path in generated_files.items():
            exists = file_path.exists()
            size = file_path.stat().st_size if exists else 0

            status = "✓" if exists else "✗"
            print(f"   {status} {format_name.upper()}: {file_path} ({size:,} bytes)")

            if not exists:
                all_exist = False

        # Display summary
        print("\n6. Report summary...")
        report_data = ReportData(results, settings.as_dict())
        summary = orchestrator.get_report_summary(report_data)
        print("\n" + summary)

        # Final result
        print("\n" + "=" * 70)

        if all_exist:
            print("✅ ALL TESTS PASSED")
            print("\nReport Generation Complete!")
            print("\nGenerated files:")
            for format_name, file_path in generated_files.items():
                print(f"  • {file_path}")

            print("\nNext steps:")
            print("  • Open the HTML report in your browser")
            print("  • Open the CSV file in Excel")
            print("  • Use the JSON file for programmatic access")

            return 0
        else:
            print("❌ SOME TESTS FAILED")
            print("One or more report files were not generated.")
            return 1

    except Exception as e:
        print(f"\n❌ TEST FAILED WITH ERROR:")
        print(f"   {e}")

        import traceback
        traceback.print_exc()

        return 1


def main():
    """Run test"""
    exit_code = test_report_generation()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
