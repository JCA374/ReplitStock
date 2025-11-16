"""
Universe Manager for Automatic Stock Analysis

Manages the complete universe of Swedish stocks (355 stocks).
Loads from CSV files, categorizes by market cap, handles updates.
"""

import pandas as pd
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session

from data.db_models import StockUniverse, FundamentalsCache
from data.db_manager import get_db_session
from data.stock_data import StockDataFetcher
from core.settings_manager import SettingsManager, get_settings

logger = logging.getLogger(__name__)


class UniverseManager:
    """
    Manages the stock universe for automatic analysis.

    Responsibilities:
    - Load all stocks from CSV files
    - Categorize by current market cap
    - Update universe in database
    - Provide filtered lists by tier
    """

    def __init__(self, settings: Optional[SettingsManager] = None):
        """
        Initialize Universe Manager

        Args:
            settings: SettingsManager instance (creates new one if None)
        """
        self.settings = settings or get_settings()
        self.session: Session = get_db_session()
        self.fetcher = StockDataFetcher()

        # CSV file paths
        self.csv_dir = Path("data/csv")
        self.csv_files = {
            'large_cap': self.csv_dir / "large_cap.csv",
            'mid_cap': self.csv_dir / "mid_cap.csv",
            'small_cap': self.csv_dir / "small_cap.csv"
        }

    def load_universe_from_csv(self) -> pd.DataFrame:
        """
        Load all Swedish stocks from CSV files

        Returns:
            DataFrame with columns: [ticker, name, sector, csv_category]
        """
        logger.info("Loading stock universe from CSV files...")

        all_stocks = []

        for category, csv_path in self.csv_files.items():
            if not csv_path.exists():
                logger.warning(f"CSV file not found: {csv_path}")
                continue

            try:
                df = pd.read_csv(csv_path)

                # Normalize column names (handle different formats)
                df.columns = df.columns.str.strip().str.lower()

                # Extract relevant columns
                if 'ticker' in df.columns:
                    ticker_col = 'ticker'
                elif 'symbol' in df.columns:
                    ticker_col = 'symbol'
                else:
                    logger.error(f"No ticker column found in {csv_path}")
                    continue

                # Create standardized dataframe
                stock_df = pd.DataFrame({
                    'ticker': df[ticker_col].str.strip(),
                    'name': df.get('name', df.get('company', '')).fillna(''),
                    'sector': df.get('sector', df.get('gics sector', '')).fillna('Unknown'),
                    'csv_category': category
                })

                all_stocks.append(stock_df)

                logger.info(f"Loaded {len(stock_df)} stocks from {category}")

            except Exception as e:
                logger.error(f"Error loading {csv_path}: {e}")
                continue

        if not all_stocks:
            raise ValueError("No stocks loaded from CSV files!")

        # Combine all stocks
        universe = pd.concat(all_stocks, ignore_index=True)

        # Ensure .ST suffix
        universe['ticker'] = universe['ticker'].apply(self._normalize_ticker)

        # Remove duplicates (keep first occurrence)
        universe = universe.drop_duplicates(subset=['ticker'], keep='first')

        logger.info(f"Total universe: {len(universe)} stocks")

        return universe

    def _normalize_ticker(self, ticker: str) -> str:
        """Ensure ticker has .ST suffix for Stockholm Exchange"""
        ticker = ticker.strip().upper()
        if not ticker.endswith('.ST'):
            ticker = f"{ticker}.ST"
        return ticker

    def categorize_by_market_cap(
        self,
        universe: pd.DataFrame,
        force_refresh: bool = False
    ) -> pd.DataFrame:
        """
        Fetch current market caps and categorize stocks into tiers

        Args:
            universe: DataFrame with stock tickers
            force_refresh: If True, fetch fresh market caps even if cached

        Returns:
            DataFrame with added columns: [market_cap, market_cap_tier]
        """
        logger.info("Categorizing stocks by market cap...")

        cache_seconds = self.settings.get_cache_seconds('market_cap')
        current_time = int(time.time())

        market_caps = []

        for idx, row in universe.iterrows():
            ticker = row['ticker']

            # Check if we have cached market cap (less than cache_seconds old)
            if not force_refresh:
                cached_market_cap = self._get_cached_market_cap(ticker, current_time, cache_seconds)
                if cached_market_cap is not None:
                    market_caps.append(cached_market_cap)
                    if (idx + 1) % 50 == 0:
                        logger.info(f"Market cap categorization: {idx + 1}/{len(universe)} (cached)")
                    continue

            # Need to fetch fresh data
            try:
                fundamentals = self.fetcher.get_fundamentals(ticker)
                market_cap = fundamentals.get('market_cap')

                market_caps.append(market_cap)

                if (idx + 1) % 10 == 0:
                    logger.info(f"Market cap fetch: {idx + 1}/{len(universe)}")

                # Small delay to avoid API rate limiting
                time.sleep(0.2)

            except Exception as e:
                logger.warning(f"Failed to get market cap for {ticker}: {e}")
                market_caps.append(None)

        # Add market cap column
        universe['market_cap'] = market_caps

        # Categorize into tiers based on settings
        universe['market_cap_tier'] = universe['market_cap'].apply(
            lambda mc: self.settings.get_tier_for_market_cap(mc) if mc else None
        )

        # Log categorization results
        tier_counts = universe['market_cap_tier'].value_counts()
        logger.info("Market cap categorization complete:")
        for tier, count in tier_counts.items():
            logger.info(f"  {tier}: {count} stocks")

        missing_cap = universe['market_cap'].isna().sum()
        if missing_cap > 0:
            logger.warning(f"  Missing market cap: {missing_cap} stocks")

        return universe

    def _get_cached_market_cap(
        self,
        ticker: str,
        current_time: int,
        cache_seconds: int
    ) -> Optional[float]:
        """Get market cap from cache if fresh enough"""
        try:
            cached = self.session.query(FundamentalsCache).filter(
                FundamentalsCache.ticker == ticker
            ).first()

            if cached:
                age_seconds = current_time - cached.last_updated

                if age_seconds < cache_seconds:
                    return cached.market_cap

        except Exception as e:
            logger.debug(f"Cache lookup failed for {ticker}: {e}")

        return None

    def update_universe_in_database(self, universe: pd.DataFrame) -> int:
        """
        Update or insert stock universe records in database

        Args:
            universe: DataFrame with stock data

        Returns:
            Number of records updated/inserted
        """
        logger.info("Updating universe in database...")

        current_time = int(time.time())
        updated_count = 0

        for _, row in universe.iterrows():
            try:
                # Check if stock exists
                existing = self.session.query(StockUniverse).filter(
                    StockUniverse.ticker == row['ticker']
                ).first()

                if existing:
                    # Update existing record
                    existing.name = row.get('name', existing.name)
                    existing.sector = row.get('sector', existing.sector)
                    existing.market_cap = row.get('market_cap')
                    existing.market_cap_tier = row.get('market_cap_tier')
                    existing.csv_category = row.get('csv_category')
                    existing.last_updated = current_time
                    existing.is_active = True
                else:
                    # Insert new record
                    new_stock = StockUniverse(
                        ticker=row['ticker'],
                        name=row.get('name', ''),
                        sector=row.get('sector', 'Unknown'),
                        market_cap=row.get('market_cap'),
                        market_cap_tier=row.get('market_cap_tier'),
                        csv_category=row.get('csv_category'),
                        last_updated=current_time,
                        is_active=True
                    )
                    self.session.add(new_stock)

                updated_count += 1

                if updated_count % 50 == 0:
                    self.session.commit()
                    logger.info(f"Database update: {updated_count}/{len(universe)}")

            except Exception as e:
                logger.error(f"Error updating {row['ticker']}: {e}")
                self.session.rollback()
                continue

        # Final commit
        try:
            self.session.commit()
            logger.info(f"Universe database update complete: {updated_count} stocks")
        except Exception as e:
            logger.error(f"Final commit failed: {e}")
            self.session.rollback()

        return updated_count

    def get_stocks_for_tier(self, tier: str) -> List[str]:
        """
        Get list of tickers for a specific market cap tier

        Args:
            tier: 'large_cap', 'mid_cap', or 'small_cap'

        Returns:
            List of ticker symbols
        """
        try:
            stocks = self.session.query(StockUniverse).filter(
                StockUniverse.market_cap_tier == tier,
                StockUniverse.is_active == True
            ).all()

            tickers = [stock.ticker for stock in stocks]

            logger.info(f"Retrieved {len(tickers)} stocks for tier {tier}")

            return tickers

        except Exception as e:
            logger.error(f"Error getting stocks for tier {tier}: {e}")
            return []

    def get_all_active_tickers(self) -> List[str]:
        """
        Get all active stock tickers in universe

        Returns:
            List of all active ticker symbols
        """
        try:
            stocks = self.session.query(StockUniverse).filter(
                StockUniverse.is_active == True
            ).all()

            tickers = [stock.ticker for stock in stocks]

            logger.info(f"Retrieved {len(tickers)} active stocks")

            return tickers

        except Exception as e:
            logger.error(f"Error getting all tickers: {e}")
            return []

    def get_universe_summary(self) -> Dict[str, int]:
        """
        Get summary statistics of the universe

        Returns:
            Dict with counts per tier and total
        """
        try:
            summary = {
                'total': 0,
                'large_cap': 0,
                'mid_cap': 0,
                'small_cap': 0,
                'unknown': 0,
                'inactive': 0
            }

            # Count by tier
            all_stocks = self.session.query(StockUniverse).all()

            for stock in all_stocks:
                summary['total'] += 1

                if not stock.is_active:
                    summary['inactive'] += 1
                    continue

                tier = stock.market_cap_tier or 'unknown'
                summary[tier] = summary.get(tier, 0) + 1

            return summary

        except Exception as e:
            logger.error(f"Error getting universe summary: {e}")
            return {}

    def refresh_universe(self, force_market_cap_refresh: bool = False) -> Tuple[int, int]:
        """
        Complete universe refresh: load CSV → categorize → update database

        Args:
            force_market_cap_refresh: Force fresh market cap fetch

        Returns:
            Tuple of (stocks_loaded, stocks_categorized_with_market_cap)
        """
        logger.info("=" * 60)
        logger.info("STARTING UNIVERSE REFRESH")
        logger.info("=" * 60)

        # Step 1: Load from CSV
        universe = self.load_universe_from_csv()
        stocks_loaded = len(universe)

        # Step 2: Categorize by market cap
        universe = self.categorize_by_market_cap(universe, force_market_cap_refresh)
        stocks_with_cap = universe['market_cap'].notna().sum()

        # Step 3: Update database
        self.update_universe_in_database(universe)

        # Step 4: Get summary
        summary = self.get_universe_summary()

        logger.info("=" * 60)
        logger.info("UNIVERSE REFRESH COMPLETE")
        logger.info(f"Total stocks loaded: {stocks_loaded}")
        logger.info(f"Stocks with market cap: {stocks_with_cap}")
        logger.info(f"Large cap: {summary.get('large_cap', 0)}")
        logger.info(f"Mid cap: {summary.get('mid_cap', 0)}")
        logger.info(f"Small cap: {summary.get('small_cap', 0)}")
        logger.info("=" * 60)

        return stocks_loaded, stocks_with_cap

    def __del__(self):
        """Close database session on cleanup"""
        if hasattr(self, 'session'):
            try:
                self.session.close()
            except:
                pass
