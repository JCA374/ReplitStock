"""
Report Generator - Base Class for All Report Formats

Aggregates analysis results and prepares data for report generation.
Supports HTML, CSV, and JSON output formats.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, date
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class ReportData:
    """
    Container for report data with aggregation and statistics
    """

    def __init__(self, analysis_results: List[Dict], settings: Dict):
        """
        Initialize report data

        Args:
            analysis_results: List of analysis results from BatchAnalyzer
            settings: Analysis settings
        """
        self.results = analysis_results
        self.settings = settings
        self.report_date = datetime.now()

        # Aggregate data
        self._aggregate_data()

    def _aggregate_data(self):
        """Aggregate results by tier and calculate statistics"""

        # Separate by tier and filter status
        self.by_tier = {
            'large_cap': [],
            'mid_cap': [],
            'small_cap': []
        }

        self.passed_filters = []
        self.failed_filters = []
        self.successful = []
        self.failed = []

        for result in self.results:
            # Track success/failure
            if result.get('analysis_successful'):
                self.successful.append(result)

                # Track filter pass/fail
                if result.get('passed_all_filters'):
                    self.passed_filters.append(result)
                else:
                    self.failed_filters.append(result)
            else:
                self.failed.append(result)

        # Calculate overall statistics
        self.stats = self._calculate_statistics()

    def _calculate_statistics(self) -> Dict:
        """Calculate comprehensive statistics"""

        scores = [r.get('composite_score', 0) for r in self.successful]
        tech_scores = [r.get('technical_score', 0) for r in self.successful]
        fund_scores = [r.get('fundamental_score', 0) for r in self.successful]

        # Recommendation counts
        recommendations = {}
        for rec in ['STRONG BUY', 'BUY', 'HOLD', 'SELL', 'SKIP']:
            recommendations[rec] = sum(
                1 for r in self.results if r.get('recommendation') == rec
            )

        # Filter pass rates
        filter_stats = self._calculate_filter_stats()

        return {
            'total_analyzed': len(self.results),
            'successful_analyses': len(self.successful),
            'failed_analyses': len(self.failed),
            'passed_all_filters': len(self.passed_filters),
            'failed_any_filter': len(self.failed_filters),

            'average_composite_score': sum(scores) / len(scores) if scores else 0,
            'average_technical_score': sum(tech_scores) / len(tech_scores) if tech_scores else 0,
            'average_fundamental_score': sum(fund_scores) / len(fund_scores) if fund_scores else 0,

            'max_score': max(scores) if scores else 0,
            'min_score': min(scores) if scores else 0,

            'recommendations': recommendations,
            'filter_statistics': filter_stats
        }

    def _calculate_filter_stats(self) -> Dict:
        """Calculate pass rates for each filter"""

        filters = {
            'technical': {
                'ma200_filter': 0,
                'ma20_filter': 0,
                'rsi_filter': 0,
                'volume_filter': 0
            },
            'fundamental': {
                'profitable_filter': 0,
                'gross_profit_filter': 0,
                'piotroski_filter': 0,
                'pe_filter': 0
            }
        }

        for result in self.successful:
            # Technical filters
            tech_filters = result.get('technical_filters', {})
            for filter_name in filters['technical'].keys():
                if tech_filters.get(filter_name):
                    filters['technical'][filter_name] += 1

            # Fundamental filters
            fund_filters = result.get('fundamental_filters', {})
            for filter_name in filters['fundamental'].keys():
                if fund_filters.get(filter_name):
                    filters['fundamental'][filter_name] += 1

        # Convert counts to percentages
        total = len(self.successful) if self.successful else 1
        for category in filters:
            for filter_name in filters[category]:
                count = filters[category][filter_name]
                filters[category][filter_name] = {
                    'count': count,
                    'percentage': (count / total) * 100
                }

        return filters

    def get_top_stocks(self, tier: Optional[str] = None, top_n: int = 10) -> List[Dict]:
        """
        Get top N stocks, optionally filtered by tier

        Args:
            tier: Market cap tier ('large_cap', 'mid_cap', 'small_cap') or None for all
            top_n: Number of stocks to return

        Returns:
            List of top stock results sorted by composite score
        """
        # Filter by tier if specified
        if tier:
            candidates = [
                r for r in self.passed_filters
                if r.get('market_cap_tier') == tier
            ]
        else:
            candidates = self.passed_filters

        # Sort by composite score (descending)
        sorted_stocks = sorted(
            candidates,
            key=lambda x: x.get('composite_score', 0),
            reverse=True
        )

        return sorted_stocks[:top_n]

    def get_tier_summary(self, tier: str) -> Dict:
        """
        Get summary statistics for a specific tier

        Args:
            tier: Market cap tier name

        Returns:
            Dict with tier statistics
        """
        tier_stocks = [
            r for r in self.successful
            if r.get('market_cap_tier') == tier
        ]

        tier_passed = [
            r for r in tier_stocks
            if r.get('passed_all_filters')
        ]

        scores = [r.get('composite_score', 0) for r in tier_stocks]

        return {
            'tier': tier,
            'total_analyzed': len(tier_stocks),
            'passed_filters': len(tier_passed),
            'pass_rate': (len(tier_passed) / len(tier_stocks) * 100) if tier_stocks else 0,
            'average_score': sum(scores) / len(scores) if scores else 0,
            'max_score': max(scores) if scores else 0,
            'min_score': min(scores) if scores else 0
        }

    def get_executive_summary(self) -> Dict:
        """
        Get executive summary for report header

        Returns:
            Dict with executive summary data
        """
        # Get top N settings
        large_top_n = self.settings.get('market_caps', {}).get('large_cap', {}).get('top_n', 15)
        mid_top_n = self.settings.get('market_caps', {}).get('mid_cap', {}).get('top_n', 20)
        small_top_n = self.settings.get('market_caps', {}).get('small_cap', {}).get('top_n', 10)

        # Get tier summaries
        large_summary = self.get_tier_summary('large_cap')
        mid_summary = self.get_tier_summary('mid_cap')
        small_summary = self.get_tier_summary('small_cap')

        return {
            'report_date': self.report_date,
            'total_stocks_analyzed': self.stats['total_analyzed'],
            'total_recommendations': large_top_n + mid_top_n + small_top_n,

            'tier_config': {
                'large_cap': large_top_n,
                'mid_cap': mid_top_n,
                'small_cap': small_top_n
            },

            'tier_summaries': {
                'large_cap': large_summary,
                'mid_cap': mid_summary,
                'small_cap': small_summary
            },

            'overall_stats': {
                'average_composite': self.stats['average_composite_score'],
                'average_technical': self.stats['average_technical_score'],
                'average_fundamental': self.stats['average_fundamental_score'],
                'total_passed_filters': self.stats['passed_all_filters']
            },

            'recommendations': self.stats['recommendations']
        }

    def get_week_over_week_comparison(self, previous_results: Optional[List[Dict]] = None) -> Dict:
        """
        Compare with previous week's results

        Args:
            previous_results: Previous week's analysis results (if available)

        Returns:
            Dict with week-over-week comparison
        """
        if not previous_results:
            return {
                'available': False,
                'message': 'No previous week data available'
            }

        # Create ticker -> result mappings
        current_map = {r['ticker']: r for r in self.passed_filters}
        previous_map = {r['ticker']: r for r in previous_results if r.get('passed_all_filters')}

        # Find new entries and drops
        current_tickers = set(current_map.keys())
        previous_tickers = set(previous_map.keys())

        new_entries = current_tickers - previous_tickers
        dropped = previous_tickers - current_tickers
        continued = current_tickers & previous_tickers

        # Score changes for continued stocks
        score_changes = []
        for ticker in continued:
            current_score = current_map[ticker].get('composite_score', 0)
            previous_score = previous_map[ticker].get('composite_score', 0)
            change = current_score - previous_score

            if abs(change) >= 5:  # Only significant changes
                score_changes.append({
                    'ticker': ticker,
                    'current_score': current_score,
                    'previous_score': previous_score,
                    'change': change
                })

        # Sort by absolute change
        score_changes.sort(key=lambda x: abs(x['change']), reverse=True)

        return {
            'available': True,
            'new_entries': len(new_entries),
            'new_entry_tickers': list(new_entries),
            'dropped': len(dropped),
            'dropped_tickers': list(dropped),
            'continued': len(continued),
            'significant_changes': score_changes[:10]  # Top 10 changes
        }


class BaseReportGenerator:
    """
    Base class for report generation.

    Provides common functionality for all report formats.
    """

    def __init__(self, settings: Dict):
        """
        Initialize report generator

        Args:
            settings: Analysis settings
        """
        self.settings = settings
        self.output_settings = settings.get('output', {})

        # Create output directories
        self.output_dir = Path(self.output_settings.get('output_directory', 'reports'))
        self.historical_dir = Path(self.output_settings.get('historical_directory', 'reports/history'))

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.historical_dir.mkdir(parents=True, exist_ok=True)

    def generate_filename(self, extension: str, report_date: Optional[datetime] = None) -> str:
        """
        Generate filename based on settings pattern

        Args:
            extension: File extension (html, csv, json)
            report_date: Date for filename (default: today)

        Returns:
            Filename string
        """
        if report_date is None:
            report_date = datetime.now()

        pattern = self.output_settings.get('filename_pattern', 'weekly_analysis_{date}.{ext}')

        filename = pattern.format(
            date=report_date.strftime('%Y-%m-%d'),
            ext=extension
        )

        return filename

    def get_output_path(self, filename: str) -> Path:
        """Get full output path for a filename"""
        return self.output_dir / filename

    def save_to_historical(self, filename: str, content: str):
        """
        Save a copy to historical archive

        Args:
            filename: Original filename
            content: File content to save
        """
        # Create year/month subdirectories
        now = datetime.now()
        archive_dir = self.historical_dir / str(now.year) / f"{now.month:02d}"
        archive_dir.mkdir(parents=True, exist_ok=True)

        # Save copy
        archive_path = archive_dir / filename

        with open(archive_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Archived to {archive_path}")

    def format_number(self, value: Optional[float], decimals: int = 1, suffix: str = '') -> str:
        """
        Format a number for display

        Args:
            value: Number to format
            decimals: Decimal places
            suffix: Suffix to add (%, etc.)

        Returns:
            Formatted string
        """
        if value is None:
            return 'N/A'

        return f"{value:.{decimals}f}{suffix}"

    def format_currency(self, value: Optional[float], currency: str = 'SEK') -> str:
        """Format currency value"""
        if value is None:
            return 'N/A'

        # Convert to billions/millions for readability
        if value >= 1_000_000_000:
            return f"{value / 1_000_000_000:.1f}B {currency}"
        elif value >= 1_000_000:
            return f"{value / 1_000_000:.1f}M {currency}"
        else:
            return f"{value:,.0f} {currency}"

    def format_recommendation(self, rec: str) -> str:
        """Format recommendation with emoji"""
        emoji_map = {
            'STRONG BUY': '⬆️ STRONG BUY',
            'BUY': '✓ BUY',
            'HOLD': '→ HOLD',
            'SELL': '↓ SELL',
            'SKIP': '✗ SKIP'
        }
        return emoji_map.get(rec, rec)

    def generate(self, report_data: ReportData) -> str:
        """
        Generate report (to be implemented by subclasses)

        Args:
            report_data: Aggregated report data

        Returns:
            Generated report content
        """
        raise NotImplementedError("Subclasses must implement generate()")
