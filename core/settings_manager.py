"""
Settings Manager for Automatic Stock Analysis System

Loads and manages configuration from analysis_settings.yaml
Provides type-safe access to all settings with validation.
"""

import yaml
import logging
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import time as dt_time
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class MarketCapTier:
    """Market cap tier configuration"""
    name: str
    min_market_cap: float
    max_market_cap: Optional[float]
    top_n: int

    def is_in_tier(self, market_cap: float) -> bool:
        """Check if a market cap value belongs to this tier"""
        if market_cap is None:
            return False

        above_min = market_cap >= self.min_market_cap
        below_max = self.max_market_cap is None or market_cap < self.max_market_cap

        return above_min and below_max


@dataclass
class CacheSettings:
    """Cache configuration to avoid API overload"""
    price_data_hours: int
    fundamentals_hours: int
    market_cap_hours: int


@dataclass
class RateLimitSettings:
    """API rate limiting configuration"""
    batch_size: int
    delay_between_batches: float
    max_retries: int
    retry_delay: float


@dataclass
class ScheduleSettings:
    """Analysis schedule configuration"""
    enabled: bool
    frequency: str
    time: str
    timezone: str
    run_on_weekends: bool


@dataclass
class ScoringWeights:
    """Scoring weight configuration"""
    technical_weight: float
    fundamental_weight: float
    technical_components: Dict[str, int]
    fundamental_components: Dict[str, int]
    bonuses: Dict[str, int]


class SettingsManager:
    """
    Manages all application settings from YAML configuration file.

    Usage:
        settings = SettingsManager()
        top_n = settings.get_top_n_for_tier('large')
        tier = settings.get_tier_for_market_cap(50000000000)
    """

    def __init__(self, config_path: str = "analysis_settings.yaml"):
        """
        Initialize settings manager

        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.market_cap_tiers: Dict[str, MarketCapTier] = {}

        # Load configuration
        self.load_settings()

    def load_settings(self) -> None:
        """Load and validate settings from YAML file"""
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(
                    f"Configuration file not found: {self.config_path}"
                )

            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)

            logger.info(f"Loaded settings from {self.config_path}")

            # Parse market cap tiers
            self._parse_market_cap_tiers()

            # Validate settings
            self._validate_settings()

        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            raise

    def _parse_market_cap_tiers(self) -> None:
        """Parse market cap tier configurations"""
        market_caps_config = self.config.get('market_caps', {})

        for tier_name, tier_config in market_caps_config.items():
            self.market_cap_tiers[tier_name] = MarketCapTier(
                name=tier_name,
                min_market_cap=tier_config['min_market_cap'],
                max_market_cap=tier_config.get('max_market_cap'),
                top_n=tier_config['top_n']
            )

        logger.info(f"Loaded {len(self.market_cap_tiers)} market cap tiers")

    def _validate_settings(self) -> None:
        """Validate loaded settings"""
        # Validate scoring weights sum to 100
        tech_components = self.config['scoring']['technical_components']
        tech_sum = sum(tech_components.values())
        if tech_sum != 100:
            logger.warning(
                f"Technical components sum to {tech_sum}, expected 100"
            )

        fund_components = self.config['scoring']['fundamental_components']
        fund_sum = sum(fund_components.values())
        if fund_sum != 100:
            logger.warning(
                f"Fundamental components sum to {fund_sum}, expected 100"
            )

        # Validate cache hours are positive
        cache_settings = self.config['data_sources']['cache_settings']
        for key, value in cache_settings.items():
            if value <= 0:
                raise ValueError(f"Cache setting {key} must be positive, got {value}")

        logger.info("Settings validation passed")

    def get_tier_for_market_cap(self, market_cap: float) -> Optional[str]:
        """
        Determine which tier a market cap belongs to

        Args:
            market_cap: Market capitalization in SEK

        Returns:
            Tier name ('large_cap', 'mid_cap', 'small_cap') or None
        """
        if market_cap is None:
            return None

        for tier_name, tier in self.market_cap_tiers.items():
            if tier.is_in_tier(market_cap):
                return tier_name

        return None

    def get_top_n_for_tier(self, tier_name: str) -> int:
        """
        Get the top N setting for a specific tier

        Args:
            tier_name: Name of the tier ('large_cap', 'mid_cap', 'small_cap')

        Returns:
            Number of top stocks to select for this tier
        """
        tier = self.market_cap_tiers.get(tier_name)
        if tier:
            return tier.top_n
        return 0

    def get_cache_hours(self, data_type: str) -> int:
        """
        Get cache duration in hours for a data type

        Args:
            data_type: 'price_data', 'fundamentals', or 'market_cap'

        Returns:
            Cache duration in hours
        """
        cache_settings = self.config['data_sources']['cache_settings']
        key = f"{data_type}_hours"
        return cache_settings.get(key, 24)

    def get_cache_seconds(self, data_type: str) -> int:
        """
        Get cache duration in seconds for a data type

        Args:
            data_type: 'price_data', 'fundamentals', or 'market_cap'

        Returns:
            Cache duration in seconds
        """
        return self.get_cache_hours(data_type) * 3600

    def get_rate_limit_settings(self) -> RateLimitSettings:
        """Get API rate limiting settings"""
        rate_config = self.config['data_sources']['rate_limiting']
        return RateLimitSettings(
            batch_size=rate_config['batch_size'],
            delay_between_batches=rate_config['delay_between_batches'],
            max_retries=rate_config['max_retries'],
            retry_delay=rate_config['retry_delay']
        )

    def get_schedule_settings(self) -> ScheduleSettings:
        """Get analysis schedule settings"""
        sched_config = self.config['schedule']
        return ScheduleSettings(
            enabled=sched_config['enabled'],
            frequency=sched_config['frequency'],
            time=sched_config['time'],
            timezone=sched_config['timezone'],
            run_on_weekends=sched_config['run_on_weekends']
        )

    def get_scoring_weights(self) -> ScoringWeights:
        """Get scoring weight configuration"""
        scoring_config = self.config['scoring']
        return ScoringWeights(
            technical_weight=scoring_config['technical_weight'],
            fundamental_weight=scoring_config['fundamental_weight'],
            technical_components=scoring_config['technical_components'],
            fundamental_components=scoring_config['fundamental_components'],
            bonuses=scoring_config.get('bonuses', {})
        )

    def get_min_tech_score(self) -> int:
        """Get minimum technical score for BUY signal"""
        return self.config['analysis']['momentum']['min_tech_score']

    def get_max_pe_ratio(self) -> float:
        """Get maximum P/E ratio threshold"""
        return self.config['analysis']['fundamental']['max_pe_ratio']

    def get_min_profit_margin(self) -> float:
        """Get minimum profit margin threshold"""
        return self.config['analysis']['fundamental']['min_profit_margin']

    def requires_above_ma200(self) -> bool:
        """Check if MA200 filter is required"""
        return self.config['analysis']['momentum']['require_above_ma200']

    def requires_above_ma20(self) -> bool:
        """Check if MA20 filter is required"""
        return self.config['analysis']['momentum']['require_above_ma20']

    def requires_profitable(self) -> bool:
        """Check if profitability is required"""
        return self.config['analysis']['fundamental']['require_profitable']

    def get_output_directory(self) -> Path:
        """Get output directory for reports"""
        return Path(self.config['output']['output_directory'])

    def get_historical_directory(self) -> Path:
        """Get historical reports directory"""
        return Path(self.config['output']['historical_directory'])

    def get_database_path(self) -> Path:
        """Get database file path"""
        return Path(self.config['database']['path'])

    def get_report_formats(self) -> List[str]:
        """Get list of report formats to generate"""
        return self.config['output']['reports']

    def is_parallel_processing_enabled(self) -> bool:
        """Check if parallel processing is enabled"""
        return self.config['advanced']['parallel_processing']['enabled']

    def get_max_workers(self) -> int:
        """Get maximum number of parallel workers"""
        return self.config['advanced']['parallel_processing']['max_workers']

    def is_test_mode(self) -> bool:
        """Check if running in test mode"""
        return self.config['advanced']['development'].get('test_mode', False)

    def get_test_stock_count(self) -> int:
        """Get number of stocks to analyze in test mode"""
        return self.config['advanced']['development'].get('test_stock_count', 20)

    def get_all_tiers(self) -> List[str]:
        """Get list of all tier names"""
        return list(self.market_cap_tiers.keys())

    def get_summary(self) -> str:
        """Get a summary of current settings"""
        summary = []
        summary.append("=== Analysis Settings Summary ===")
        summary.append(f"Database: {self.get_database_path()}")
        summary.append(f"Cache duration (price data): {self.get_cache_hours('price_data')}h")
        summary.append(f"Cache duration (fundamentals): {self.get_cache_hours('fundamentals')}h")
        summary.append("")
        summary.append("Market Cap Tiers:")
        for tier_name, tier in self.market_cap_tiers.items():
            summary.append(
                f"  {tier_name}: Top {tier.top_n} stocks "
                f"(Cap: {tier.min_market_cap/1e9:.0f}B - "
                f"{tier.max_market_cap/1e9:.0f}B SEK)" if tier.max_market_cap
                else f"  {tier_name}: Top {tier.top_n} stocks "
                     f"(Cap: >{tier.min_market_cap/1e9:.0f}B SEK)"
            )
        summary.append("")
        summary.append("Analysis Filters:")
        summary.append(f"  Min tech score: {self.get_min_tech_score()}")
        summary.append(f"  Max P/E ratio: {self.get_max_pe_ratio()}")
        summary.append(f"  Min profit margin: {self.get_min_profit_margin()*100:.1f}%")
        summary.append(f"  Require MA200: {self.requires_above_ma200()}")
        summary.append(f"  Require MA20: {self.requires_above_ma20()}")
        summary.append(f"  Require profitable: {self.requires_profitable()}")

        return "\n".join(summary)

    def __repr__(self) -> str:
        return f"SettingsManager(config_path={self.config_path}, tiers={len(self.market_cap_tiers)})"


# Singleton instance
_settings_instance: Optional[SettingsManager] = None


def get_settings() -> SettingsManager:
    """
    Get the global settings instance (singleton pattern)

    Returns:
        SettingsManager instance
    """
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = SettingsManager()
    return _settings_instance


def reload_settings() -> SettingsManager:
    """
    Force reload settings from file

    Returns:
        SettingsManager instance with fresh settings
    """
    global _settings_instance
    _settings_instance = SettingsManager()
    return _settings_instance
