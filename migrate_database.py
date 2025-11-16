"""
Database Migration Script for Automatic Analysis System

Creates new tables for:
- stock_universe
- analysis_runs
- daily_rankings
- data_fetch_log

Safe to run multiple times (won't drop existing tables).
"""

import logging
from sqlalchemy import create_engine
from data.db_models import Base, StockUniverse, AnalysisRun, DailyRanking, DataFetchLog
from core.settings_manager import get_settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def migrate_database():
    """Create new tables for automatic analysis system"""

    logger.info("=" * 70)
    logger.info("DATABASE MIGRATION - Automatic Analysis System")
    logger.info("=" * 70)

    # Get database path from settings
    settings = get_settings()
    db_path = settings.get_database_path()

    logger.info(f"Database: {db_path}")

    # Create engine
    engine = create_engine(f'sqlite:///{db_path}', echo=False)

    # Create all tables (only creates if they don't exist)
    logger.info("Creating tables...")

    try:
        Base.metadata.create_all(engine)
        logger.info("✓ Tables created successfully")

        # List all tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        logger.info(f"\nDatabase contains {len(tables)} tables:")
        for table in sorted(tables):
            logger.info(f"  - {table}")

        # Check for new tables specifically
        new_tables = ['stock_universe', 'analysis_runs', 'daily_rankings', 'data_fetch_log']
        logger.info("\nNew tables for automatic analysis:")
        for table in new_tables:
            if table in tables:
                logger.info(f"  ✓ {table} - ready")
            else:
                logger.warning(f"  ✗ {table} - missing!")

        logger.info("\n" + "=" * 70)
        logger.info("MIGRATION COMPLETE")
        logger.info("=" * 70)

        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = migrate_database()
    exit(0 if success else 1)
