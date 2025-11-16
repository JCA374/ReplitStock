"""
Stock Analyzer - Orchestrates Complete Analysis for Single Stock

Combines technical indicators and fundamental metrics to generate
comprehensive stock analysis with research-backed scoring.

Flow:
1. Fetch price data and fundamentals
2. Calculate technical indicators
3. Calculate fundamental metrics
4. Generate composite score (70% tech, 30% fundamental)
5. Apply filters and determine recommendation
"""

import logging
from typing import Dict, Optional
from datetime import datetime
import pandas as pd

from core.technical_indicators import TechnicalIndicators, calculate_technical_score
from core.fundamental_metrics import FundamentalMetrics, calculate_fundamental_score
from data.stock_data import StockDataFetcher

logger = logging.getLogger(__name__)


class StockAnalyzer:
    """
    Analyzes a single stock using technical and fundamental analysis.

    Uses research-backed parameters and weighting (70% technical, 30% fundamental)
    """

    def __init__(self, settings: Dict, data_fetcher: Optional[StockDataFetcher] = None):
        """
        Initialize stock analyzer

        Args:
            settings: Analysis settings from SettingsManager
            data_fetcher: Optional StockDataFetcher instance
        """
        self.settings = settings
        self.fetcher = data_fetcher or StockDataFetcher()

    def analyze(self, ticker: str) -> Dict:
        """
        Perform complete analysis on a stock

        Args:
            ticker: Stock ticker symbol (e.g., 'INVE-B.ST')

        Returns:
            Dict with complete analysis results
        """
        logger.info(f"Analyzing {ticker}...")

        try:
            # 1. Fetch data
            price_data = self.fetcher.get_historical_data(ticker, period='1y')
            fundamentals = self.fetcher.get_fundamentals(ticker)

            if price_data is None or price_data.empty:
                logger.warning(f"{ticker}: Insufficient price data")
                return self._create_failed_result(ticker, "Insufficient price data")

            # 2. Calculate technical indicators
            tech_calc = TechnicalIndicators(price_data)
            tech_indicators = tech_calc.calculate_all(self.settings)

            if not tech_indicators.get('calculation_successful', False):
                logger.warning(f"{ticker}: Technical calculation failed")
                return self._create_failed_result(ticker, "Technical calculation failed")

            # 3. Calculate fundamental metrics
            fund_calc = FundamentalMetrics(fundamentals)
            fund_metrics = fund_calc.calculate_all(self.settings)

            if not fund_metrics.get('calculation_successful', False):
                logger.warning(f"{ticker}: Fundamental calculation failed")
                # Continue anyway - technical analysis might be sufficient

            # 4. Calculate scores
            tech_score_result = calculate_technical_score(tech_indicators, self.settings)
            fund_score_result = calculate_fundamental_score(fund_metrics, self.settings)

            # 5. Calculate composite score (70% tech, 30% fundamental)
            composite_score = self._calculate_composite_score(
                tech_score_result, fund_score_result
            )

            # 6. Apply filters
            passed_all_filters = (
                tech_score_result.get('passed_filters', False) and
                fund_score_result.get('passed_filters', False)
            )

            # 7. Determine recommendation
            recommendation = self._determine_recommendation(
                composite_score, passed_all_filters
            )

            # 8. Create result
            result = {
                # Identification
                'ticker': ticker,
                'analysis_date': datetime.now().isoformat(),
                'analysis_successful': True,

                # Scores
                'composite_score': composite_score,
                'technical_score': tech_score_result.get('technical_score', 0),
                'fundamental_score': fund_score_result.get('fundamental_score', 0),

                # Score breakdown
                'technical_breakdown': tech_score_result.get('score_breakdown', {}),
                'fundamental_breakdown': fund_score_result.get('score_breakdown', {}),

                # Filters
                'passed_all_filters': passed_all_filters,
                'technical_filters': tech_score_result.get('filter_results', {}),
                'fundamental_filters': fund_score_result.get('filter_results', {}),

                # Recommendation
                'recommendation': recommendation,

                # Key metrics
                'current_price': tech_indicators.get('current_price'),
                'market_cap': fund_metrics.get('market_cap'),
                'rsi': tech_indicators.get('rsi'),
                'ma200_distance_pct': tech_indicators.get('ma200_distance_pct'),
                'ma20_distance_pct': tech_indicators.get('ma20_distance_pct'),
                'high52_proximity_pct': tech_indicators.get('high52_proximity_pct'),
                'volume_confirmed': tech_indicators.get('volume_confirmed'),
                'piotroski_score': fund_metrics.get('piotroski_score'),
                'gross_profitability': fund_metrics.get('gross_profitability'),
                'pe_ratio': fund_metrics.get('pe_ratio'),
                'profit_margin': fund_metrics.get('profit_margin'),
                'revenue_growth': fund_metrics.get('revenue_growth'),

                # Full indicator details
                'technical_indicators': tech_indicators,
                'fundamental_metrics': fund_metrics,
            }

            logger.info(
                f"{ticker}: Score={composite_score:.1f} "
                f"(Tech={tech_score_result.get('technical_score', 0):.1f}, "
                f"Fund={fund_score_result.get('fundamental_score', 0):.1f}) "
                f"- {recommendation}"
            )

            return result

        except Exception as e:
            logger.error(f"{ticker}: Analysis failed - {e}")
            return self._create_failed_result(ticker, str(e))

    def _calculate_composite_score(
        self,
        tech_score_result: Dict,
        fund_score_result: Dict
    ) -> float:
        """
        Calculate composite score using 70% technical, 30% fundamental weighting

        Research: Value & Momentum hybrid outperforms pure strategies
        """
        scoring = self.settings.get('scoring', {})
        tech_weight = scoring.get('technical_weight', 70) / 100
        fund_weight = scoring.get('fundamental_weight', 30) / 100

        tech_score = tech_score_result.get('technical_score', 0)
        fund_score = fund_score_result.get('fundamental_score', 0)

        composite = (tech_score * tech_weight) + (fund_score * fund_weight)

        # Apply bonuses if configured
        bonuses = scoring.get('bonuses', {})
        # Bonuses would be applied here if needed

        return round(composite, 2)

    def _determine_recommendation(
        self,
        composite_score: float,
        passed_all_filters: bool
    ) -> str:
        """
        Determine recommendation based on score and filters

        Returns:
            'STRONG BUY', 'BUY', 'HOLD', 'SELL', or 'SKIP'
        """
        if not passed_all_filters:
            return 'SKIP'  # Failed filters

        momentum_settings = self.settings.get('analysis', {}).get('momentum', {})
        min_composite = momentum_settings.get('min_composite_score', 65)

        if composite_score >= 85:
            return 'STRONG BUY'
        elif composite_score >= 75:
            return 'BUY'
        elif composite_score >= min_composite:
            return 'HOLD'
        else:
            return 'SELL'

    def _create_failed_result(self, ticker: str, reason: str) -> Dict:
        """Create result dict for failed analysis"""
        return {
            'ticker': ticker,
            'analysis_date': datetime.now().isoformat(),
            'analysis_successful': False,
            'failure_reason': reason,
            'composite_score': 0,
            'technical_score': 0,
            'fundamental_score': 0,
            'passed_all_filters': False,
            'recommendation': 'SKIP'
        }


class BatchAnalyzer:
    """
    Analyzes multiple stocks with rate limiting and progress tracking.

    Processes all 352 Swedish stocks with smart caching and error handling.
    """

    def __init__(self, settings: Dict):
        """
        Initialize batch analyzer

        Args:
            settings: Analysis settings from SettingsManager
        """
        self.settings = settings
        self.analyzer = StockAnalyzer(settings)
        self.results = []

    def analyze_all_stocks(self, progress_callback: Optional[callable] = None) -> list:
        """
        Analyze all active stocks in the universe (352 Swedish stocks)

        Args:
            progress_callback: Optional callback(current, total, ticker, result)

        Returns:
            List of analysis results for all stocks
        """
        logger.info("Fetching all active stocks from universe...")

        # Import here to avoid circular imports
        from core.universe_manager import UniverseManager

        # Get all active tickers from universe
        # UniverseManager will create its own settings instance
        universe = UniverseManager()
        tickers = universe.get_all_active_tickers()

        if not tickers:
            logger.error("No active stocks found in universe!")
            logger.error("Run 'python test_phase1.py' to populate the universe")
            return []

        logger.info(f"Found {len(tickers)} active stocks to analyze")

        # Analyze the batch
        return self.analyze_batch(tickers, progress_callback)

    def analyze_batch(
        self,
        tickers: list,
        progress_callback: Optional[callable] = None
    ) -> list:
        """
        Analyze a batch of stocks

        Args:
            tickers: List of ticker symbols
            progress_callback: Optional callback(current, total, ticker, result)

        Returns:
            List of analysis results
        """
        logger.info(f"Starting batch analysis of {len(tickers)} stocks...")

        results = []
        errors = 0
        consecutive_errors = 0
        max_consecutive_errors = self.settings.get('advanced', {}).get(
            'error_handling', {}
        ).get('max_consecutive_errors', 10)

        for idx, ticker in enumerate(tickers, 1):
            try:
                # Analyze stock
                result = self.analyzer.analyze(ticker)

                results.append(result)

                # Reset consecutive error counter on success
                if result.get('analysis_successful'):
                    consecutive_errors = 0
                else:
                    errors += 1
                    consecutive_errors += 1

                # Progress callback
                if progress_callback:
                    progress_callback(idx, len(tickers), ticker, result)

                # Check error threshold
                if consecutive_errors >= max_consecutive_errors:
                    logger.error(
                        f"Too many consecutive errors ({consecutive_errors}). "
                        f"Stopping batch analysis."
                    )
                    break

                # Rate limiting delay between stocks
                import time
                rate_settings = self.settings.get('data_sources', {}).get('rate_limiting', {})
                delay = rate_settings.get('delay_between_batches', 0.5)

                if idx % 10 == 0:  # Every 10 stocks
                    time.sleep(delay)
                else:
                    time.sleep(0.1)  # Small delay between individual stocks

            except Exception as e:
                logger.error(f"Batch analysis error on {ticker}: {e}")
                errors += 1
                consecutive_errors += 1

                # Add failed result
                results.append({
                    'ticker': ticker,
                    'analysis_successful': False,
                    'failure_reason': str(e),
                    'recommendation': 'SKIP'
                })

        # Summary
        successful = sum(1 for r in results if r.get('analysis_successful'))
        logger.info(
            f"Batch analysis complete: {successful}/{len(tickers)} successful, "
            f"{errors} errors"
        )

        self.results = results
        return results

    def filter_and_rank(self, tier: str, top_n: int) -> list:
        """
        Filter results for a tier and return top N

        Args:
            tier: Market cap tier ('large_cap', 'mid_cap', 'small_cap')
            top_n: Number of top stocks to return

        Returns:
            List of top N results for the tier
        """
        # Filter successful analyses that passed all filters
        valid_results = [
            r for r in self.results
            if r.get('analysis_successful', False) and
            r.get('passed_all_filters', False)
        ]

        # Sort by composite score (descending)
        sorted_results = sorted(
            valid_results,
            key=lambda x: x.get('composite_score', 0),
            reverse=True
        )

        # Take top N
        top_results = sorted_results[:top_n]

        logger.info(
            f"{tier}: Selected {len(top_results)} stocks "
            f"(from {len(valid_results)} that passed filters)"
        )

        return top_results

    def get_statistics(self) -> Dict:
        """
        Get analysis statistics

        Returns:
            Dict with statistics about the batch analysis
        """
        total = len(self.results)
        successful = sum(1 for r in self.results if r.get('analysis_successful'))
        passed_filters = sum(1 for r in self.results if r.get('passed_all_filters'))

        scores = [r.get('composite_score', 0) for r in self.results if r.get('analysis_successful')]

        return {
            'total_analyzed': total,
            'successful_analyses': successful,
            'passed_all_filters': passed_filters,
            'average_score': sum(scores) / len(scores) if scores else 0,
            'max_score': max(scores) if scores else 0,
            'min_score': min(scores) if scores else 0,
            'recommendations': {
                'STRONG BUY': sum(1 for r in self.results if r.get('recommendation') == 'STRONG BUY'),
                'BUY': sum(1 for r in self.results if r.get('recommendation') == 'BUY'),
                'HOLD': sum(1 for r in self.results if r.get('recommendation') == 'HOLD'),
                'SELL': sum(1 for r in self.results if r.get('recommendation') == 'SELL'),
                'SKIP': sum(1 for r in self.results if r.get('recommendation') == 'SKIP'),
            }
        }
