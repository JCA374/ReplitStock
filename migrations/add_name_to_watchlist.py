"""Add name column to watchlist_memberships table"""
import logging
import sys
import os

# Add the parent directory to sys.path to import data modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from data.db_manager import get_db_session

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    """Add name column to existing watchlist_memberships table"""
    session = get_db_session()
    try:
        # Check if column already exists (for SQLite)
        try:
            result = session.execute(text(
                "PRAGMA table_info(watchlist_memberships)"
            )).fetchall()
            
            # Check if 'name' column exists
            columns = [row[1] for row in result]
            if 'name' in columns:
                logger.info("Name column already exists in watchlist_memberships table")
                return
                
        except Exception:
            # If PRAGMA fails, we might be on PostgreSQL
            try:
                result = session.execute(text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name='watchlist_memberships' AND column_name='name'"
                )).fetchone()

                if result:
                    logger.info("Name column already exists in watchlist_memberships table")
                    return
            except Exception:
                pass

        # Add the column
        logger.info("Adding name column to watchlist_memberships table...")
        session.execute(text(
            "ALTER TABLE watchlist_memberships ADD COLUMN name VARCHAR(200)"
        ))
        session.commit()
        logger.info("Successfully added name column to watchlist_memberships table")

    except Exception as e:
        logger.error(f"Migration error: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    migrate()