#!/usr/bin/env python3
"""
Generate Weekly Stock Analysis Report

Simple entry point for automatic stock analysis system.
Analyzes all 352 Swedish stocks and generates HTML/CSV/JSON reports.

Usage:
    python generate_weekly_report.py

Output:
    reports/weekly_analysis_YYYY-MM-DD.html
    reports/weekly_analysis_YYYY-MM-DD.csv
    reports/weekly_analysis_YYYY-MM-DD.json
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
    """Run complete weekly analysis and generate reports"""

    print("\n" + "="*70)
    print("  AUTOMATIC STOCK ANALYSIS - SWEDISH MARKET (OMXS)")
    print("="*70)
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Universe: 352 Swedish stocks (100 large, 143 mid, 109 small cap)")
    print("="*70 + "\n")

    try:
        # Import here to catch import errors
        from core.stock_analyzer import BatchAnalyzer
        from core.settings_manager import get_settings
        from reports.weekly_report import WeeklyReportOrchestrator

        # Load settings
        logger.info("Loading configuration...")
        settings = get_settings()

        # Initialize analyzers
        logger.info("Initializing analysis engine...")
        batch_analyzer = BatchAnalyzer(settings.as_dict())

        # Run analysis on all stocks
        logger.info("Analyzing all 352 stocks...")
        logger.info("  (First run: ~15-20 minutes)")
        logger.info("  (With cache: ~5 minutes)")
        print()

        results = batch_analyzer.analyze_all_stocks()

        logger.info(f"Analysis complete! Analyzed {len(results)} stocks")

        # Generate reports
        logger.info("Generating reports (HTML, CSV, JSON)...")
        orchestrator = WeeklyReportOrchestrator(settings.as_dict())
        report_files = orchestrator.generate_weekly_report(results)

        # Display results
        print("\n" + "="*70)
        print("  REPORTS GENERATED SUCCESSFULLY!")
        print("="*70)

        for file_path in report_files:
            file_size = Path(file_path).stat().st_size / 1024  # KB
            print(f"  ✓ {file_path} ({file_size:.1f} KB)")

        print("\n" + "="*70)
        print("  NEXT STEPS:")
        print("="*70)
        print("  1. Open the HTML report in your browser:")
        print(f"     {report_files[0]}")
        print("  2. Import CSV into Excel for deeper analysis")
        print("  3. Use JSON for programmatic access")
        print("="*70 + "\n")

        return 0

    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Make sure you've installed all dependencies:")
        logger.error("  pip install -r requirements.txt")
        return 1

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        logger.error("Make sure you're running from the project root directory")
        return 1

    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        logger.error("\nTroubleshooting:")
        logger.error("  1. Check internet connection (Yahoo Finance data)")
        logger.error("  2. Run database migration: python migrate_database.py")
        logger.error("  3. Check logs in logs/analysis.log")
        return 1

if __name__ == "__main__":
    sys.exit(main())
