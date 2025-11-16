"""
Phase 1 Test Script - Universe Manager

Tests:
1. Settings loading
2. Database tables creation
3. CSV loading (355 stocks)
4. Market cap categorization
5. Database storage

Run this to verify Phase 1 is working correctly.
"""

import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_settings():
    """Test 1: Settings Manager"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 1: Settings Manager")
    logger.info("=" * 70)

    try:
        from core.settings_manager import get_settings

        settings = get_settings()

        logger.info("✓ Settings loaded successfully")
        logger.info(f"  Database: {settings.get_database_path()}")
        logger.info(f"  Large cap top N: {settings.get_top_n_for_tier('large_cap')}")
        logger.info(f"  Mid cap top N: {settings.get_top_n_for_tier('mid_cap')}")
        logger.info(f"  Small cap top N: {settings.get_top_n_for_tier('small_cap')}")
        logger.info(f"  Cache duration (price): {settings.get_cache_hours('price_data')}h")
        logger.info(f"  Min tech score: {settings.get_min_tech_score()}")

        return True

    except Exception as e:
        logger.error(f"✗ Settings test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_migration():
    """Test 2: Database Migration"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 2: Database Migration")
    logger.info("=" * 70)

    try:
        import migrate_database

        success = migrate_database.migrate_database()

        if success:
            logger.info("✓ Database migration successful")
            return True
        else:
            logger.error("✗ Database migration failed")
            return False

    except Exception as e:
        logger.error(f"✗ Migration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_csv_loading():
    """Test 3: Load stocks from CSV"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 3: CSV Loading")
    logger.info("=" * 70)

    try:
        from core.universe_manager import UniverseManager

        manager = UniverseManager()

        # Load universe
        universe = manager.load_universe_from_csv()

        logger.info(f"✓ Loaded {len(universe)} stocks from CSV files")

        # Show breakdown by CSV category
        csv_counts = universe['csv_category'].value_counts()
        for category, count in csv_counts.items():
            logger.info(f"  {category}: {count} stocks")

        # Show sample stocks
        logger.info("\nSample stocks (first 10):")
        for idx, row in universe.head(10).iterrows():
            logger.info(f"  {row['ticker']:<15} {row['name']:<40} {row['sector']}")

        if len(universe) < 300:
            logger.warning(f"Expected ~355 stocks, only got {len(universe)}")

        return True

    except Exception as e:
        logger.error(f"✗ CSV loading test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_market_cap_categorization():
    """Test 4: Market Cap Categorization (LIMITED TEST)"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 4: Market Cap Categorization (Test Mode - 20 stocks)")
    logger.info("=" * 70)

    try:
        from core.universe_manager import UniverseManager
        from core.settings_manager import get_settings

        settings = get_settings()
        manager = UniverseManager(settings)

        # Load universe
        universe = manager.load_universe_from_csv()

        # TEST MODE: Only categorize first 20 stocks to avoid API overload
        logger.info(f"Testing with first 20 stocks (out of {len(universe)} total)")
        test_universe = universe.head(20).copy()

        # Categorize
        test_universe = manager.categorize_by_market_cap(test_universe, force_refresh=False)

        logger.info(f"✓ Categorized {len(test_universe)} stocks")

        # Show results
        tier_counts = test_universe['market_cap_tier'].value_counts()
        logger.info("\nMarket cap distribution (test sample):")
        for tier, count in tier_counts.items():
            logger.info(f"  {tier}: {count} stocks")

        # Show examples from each tier
        logger.info("\nSample stocks by tier:")
        for tier in ['large_cap', 'mid_cap', 'small_cap']:
            tier_stocks = test_universe[test_universe['market_cap_tier'] == tier]
            if not tier_stocks.empty:
                stock = tier_stocks.iloc[0]
                cap_billions = stock['market_cap'] / 1e9 if stock['market_cap'] else 0
                logger.info(f"  {tier}: {stock['ticker']:<15} Market cap: {cap_billions:.1f}B SEK")

        logger.info("\n⚠️  NOTE: This was a LIMITED TEST with only 20 stocks")
        logger.info("    To categorize all 355 stocks, use:")
        logger.info("    python -c \"from core.universe_manager import UniverseManager; UniverseManager().refresh_universe()\"")

        return True

    except Exception as e:
        logger.error(f"✗ Market cap categorization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_storage():
    """Test 5: Database Storage"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 5: Database Storage (Test Mode - 20 stocks)")
    logger.info("=" * 70)

    try:
        from core.universe_manager import UniverseManager

        manager = UniverseManager()

        # Load and categorize (test mode)
        universe = manager.load_universe_from_csv().head(20)
        universe = manager.categorize_by_market_cap(universe, force_refresh=False)

        # Update database
        updated = manager.update_universe_in_database(universe)

        logger.info(f"✓ Updated {updated} stocks in database")

        # Verify by reading back
        summary = manager.get_universe_summary()
        logger.info("\nUniverse summary from database:")
        for key, value in summary.items():
            logger.info(f"  {key}: {value}")

        return True

    except Exception as e:
        logger.error(f"✗ Database storage test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    logger.info("\n")
    logger.info("#" * 70)
    logger.info("# PHASE 1 TEST SUITE - Automatic Stock Analysis System")
    logger.info("#" * 70)

    results = {
        "Settings Manager": test_settings(),
        "Database Migration": test_database_migration(),
        "CSV Loading": test_csv_loading(),
        "Market Cap Categorization": test_market_cap_categorization(),
        "Database Storage": test_database_storage(),
    }

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("TEST SUMMARY")
    logger.info("=" * 70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status} - {test_name}")

    logger.info("=" * 70)
    logger.info(f"RESULT: {passed}/{total} tests passed")
    logger.info("=" * 70)

    if passed == total:
        logger.info("\n🎉 All tests passed! Phase 1 is ready!")
        logger.info("\nNext steps:")
        logger.info("  1. Run full universe refresh:")
        logger.info("     python -c \"from core.universe_manager import UniverseManager; UniverseManager().refresh_universe()\"")
        logger.info("  2. This will categorize all 355 stocks (takes ~10-15 minutes)")
        logger.info("  3. After that, you're ready for Phase 2!")
        return 0
    else:
        logger.error("\n❌ Some tests failed. Please review errors above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
