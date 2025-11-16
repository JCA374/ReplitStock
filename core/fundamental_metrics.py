"""
Fundamental Metrics Calculator - Research-Backed Parameters

Implements evidence-based fundamental analysis metrics optimized for
Swedish stock market based on 2018-2025 academic research.

Key Features:
- Piotroski F-Score (9-point financial strength score)
- Gross Profitability: (Revenue - COGS) / Total Assets (superior to P/E)
- Profitability metrics (profit margin, ROE, ROA)
- Valuation metrics (P/E, P/B)
- Growth metrics (revenue growth, earnings growth)
- Financial health (debt/equity, current ratio)
"""

import logging
from typing import Dict, Optional
import numpy as np

logger = logging.getLogger(__name__)


class FundamentalMetrics:
    """
    Calculate fundamental metrics for stock fundamentals data.

    Research shows gross profitability and Piotroski F-Score are
    superior predictors of stock performance vs traditional P/E ratio.
    """

    def __init__(self, fundamentals: Dict):
        """
        Initialize with fundamentals data

        Args:
            fundamentals: Dict with fundamental data from Yahoo Finance or similar
                         Keys: market_cap, pe_ratio, profit_margin, revenue_growth,
                               total_revenue, cost_of_revenue, total_assets,
                               net_income, total_debt, total_equity, etc.
        """
        self.fund = fundamentals

    def calculate_all(self, settings: Dict) -> Dict:
        """
        Calculate all fundamental metrics based on settings

        Args:
            settings: Analysis settings from SettingsManager

        Returns:
            Dict with all fundamental metrics and scores
        """
        try:
            fund_settings = settings.get('analysis', {}).get('fundamental', {})

            # Calculate individual metrics
            gross_profitability = self.calculate_gross_profitability()
            piotroski_score = self.calculate_piotroski_score()

            profit_margin = self.fund.get('profit_margin')
            pe_ratio = self.fund.get('pe_ratio')
            revenue_growth = self.fund.get('revenue_growth')
            debt_to_equity = self.calculate_debt_to_equity()

            roe = self.fund.get('return_on_equity')
            roa = self.fund.get('return_on_assets')
            current_ratio = self.fund.get('current_ratio')

            # Check conditions
            is_profitable = (profit_margin and profit_margin > 0) if profit_margin else False

            pe_reasonable = (
                pe_ratio and
                fund_settings.get('min_pe_ratio', 0) < pe_ratio < fund_settings.get('max_pe_ratio', 30)
            ) if pe_ratio else False

            gross_profit_ok = (
                gross_profitability and
                gross_profitability >= fund_settings.get('min_gross_profitability', 0.20)
            ) if gross_profitability else False

            piotroski_ok = (
                piotroski_score and
                piotroski_score >= fund_settings.get('min_piotroski_score', 7)
            ) if piotroski_score is not None else False

            revenue_growth_positive = (
                revenue_growth and revenue_growth > 0
            ) if revenue_growth else False

            return {
                # Raw metrics
                'gross_profitability': gross_profitability,
                'piotroski_score': piotroski_score,
                'profit_margin': profit_margin,
                'pe_ratio': pe_ratio,
                'revenue_growth': revenue_growth,
                'debt_to_equity': debt_to_equity,
                'roe': roe,
                'roa': roa,
                'current_ratio': current_ratio,

                # Market data
                'market_cap': self.fund.get('market_cap'),
                'total_revenue': self.fund.get('total_revenue'),
                'net_income': self.fund.get('net_income'),

                # Boolean conditions
                'is_profitable': is_profitable,
                'pe_reasonable': pe_reasonable,
                'gross_profit_ok': gross_profit_ok,
                'piotroski_ok': piotroski_ok,
                'revenue_growth_positive': revenue_growth_positive,

                # Status flags
                'data_sufficient': self._check_data_sufficiency(),
                'calculation_successful': True
            }

        except Exception as e:
            logger.error(f"Error calculating fundamental metrics: {e}")
            return {
                'calculation_successful': False,
                'error': str(e)
            }

    def calculate_gross_profitability(self) -> Optional[float]:
        """
        Calculate Gross Profitability = (Revenue - COGS) / Total Assets

        Research: Superior predictive power vs P/E ratio for stock returns
        Measures operational efficiency and pricing power

        Returns:
            Gross profitability ratio (e.g., 0.35 = 35%)
        """
        try:
            revenue = self.fund.get('total_revenue')
            cogs = self.fund.get('cost_of_revenue')  # Cost of Goods Sold
            total_assets = self.fund.get('total_assets')

            if not all([revenue, total_assets]):
                return None

            # If COGS not available, estimate from gross profit
            if cogs is None:
                gross_profit = self.fund.get('gross_profit')
                if gross_profit:
                    cogs = revenue - gross_profit
                else:
                    return None

            gross_profit = revenue - cogs
            gross_profitability = gross_profit / total_assets

            return float(gross_profitability)

        except Exception as e:
            logger.warning(f"Gross profitability calculation failed: {e}")
            return None

    def calculate_piotroski_score(self) -> Optional[int]:
        """
        Calculate Piotroski F-Score (9-point score)

        Research: F-Score >= 7 eliminates value traps
        Evaluates financial strength across 3 dimensions:
        1. Profitability (4 points)
        2. Leverage/Liquidity (3 points)
        3. Operating Efficiency (2 points)

        Returns:
            Score from 0-9 (higher is better)
        """
        try:
            score = 0

            # Get current and prior year data (if available)
            current = self.fund
            prior = self.fund.get('prior_year', {})  # May not always be available

            # ===== PROFITABILITY (4 points) =====

            # 1. Positive net income
            net_income = current.get('net_income')
            if net_income and net_income > 0:
                score += 1

            # 2. Positive operating cash flow
            operating_cash_flow = current.get('operating_cash_flow')
            if operating_cash_flow and operating_cash_flow > 0:
                score += 1

            # 3. ROA (Return on Assets) - positive
            roa = current.get('return_on_assets')
            if roa and roa > 0:
                score += 1

            # 4. Quality of earnings (OCF > Net Income)
            if operating_cash_flow and net_income and operating_cash_flow > net_income:
                score += 1

            # ===== LEVERAGE/LIQUIDITY (3 points) =====

            # 5. Decrease in long-term debt (or low debt)
            total_debt = current.get('total_debt', 0) or 0
            prior_debt = prior.get('total_debt', total_debt) if prior else total_debt
            if total_debt <= prior_debt:
                score += 1

            # 6. Increase in current ratio (liquidity improving)
            current_ratio = current.get('current_ratio')
            prior_current_ratio = prior.get('current_ratio', current_ratio) if prior else current_ratio
            if current_ratio and prior_current_ratio and current_ratio >= prior_current_ratio:
                score += 1

            # 7. No new shares issued (or shares decreased)
            shares = current.get('shares_outstanding')
            prior_shares = prior.get('shares_outstanding', shares) if prior else shares
            if shares and prior_shares and shares <= prior_shares:
                score += 1

            # ===== OPERATING EFFICIENCY (2 points) =====

            # 8. Increase in gross margin
            gross_margin = self._calculate_gross_margin(current)
            prior_gross_margin = self._calculate_gross_margin(prior) if prior else gross_margin
            if gross_margin and prior_gross_margin and gross_margin > prior_gross_margin:
                score += 1

            # 9. Increase in asset turnover
            asset_turnover = self._calculate_asset_turnover(current)
            prior_asset_turnover = self._calculate_asset_turnover(prior) if prior else asset_turnover
            if asset_turnover and prior_asset_turnover and asset_turnover > prior_asset_turnover:
                score += 1

            return score

        except Exception as e:
            logger.warning(f"Piotroski score calculation failed: {e}")
            return None

    def _calculate_gross_margin(self, data: Dict) -> Optional[float]:
        """Calculate gross margin from revenue and COGS"""
        try:
            revenue = data.get('total_revenue')
            cogs = data.get('cost_of_revenue')

            if not revenue:
                return None

            if cogs is None:
                gross_profit = data.get('gross_profit')
                if gross_profit:
                    return gross_profit / revenue

            if cogs:
                return (revenue - cogs) / revenue

            return None

        except:
            return None

    def _calculate_asset_turnover(self, data: Dict) -> Optional[float]:
        """Calculate asset turnover = Revenue / Total Assets"""
        try:
            revenue = data.get('total_revenue')
            assets = data.get('total_assets')

            if revenue and assets and assets > 0:
                return revenue / assets

            return None

        except:
            return None

    def calculate_debt_to_equity(self) -> Optional[float]:
        """
        Calculate Debt to Equity ratio

        Returns:
            Debt/Equity ratio (e.g., 0.5 = 50% debt relative to equity)
        """
        try:
            total_debt = self.fund.get('total_debt', 0) or 0
            total_equity = self.fund.get('total_equity')

            if not total_equity or total_equity <= 0:
                return None

            return float(total_debt / total_equity)

        except Exception as e:
            logger.warning(f"Debt to equity calculation failed: {e}")
            return None

    def _check_data_sufficiency(self) -> bool:
        """Check if we have sufficient data for analysis"""
        required_fields = ['market_cap', 'total_revenue', 'total_assets']

        return all(self.fund.get(field) is not None for field in required_fields)


def calculate_fundamental_score(metrics: Dict, settings: Dict) -> Dict:
    """
    Calculate overall fundamental score based on metrics

    Uses research-backed weighting:
    - Gross profitability: 35 points (research: superior to P/E)
    - Piotroski F-Score: 25 points (financial quality)
    - Profitability: 20 points (margin + ROE)
    - Valuation: 10 points (P/E reasonableness)
    - Growth: 10 points (revenue & earnings)

    Args:
        metrics: Dict from FundamentalMetrics.calculate_all()
        settings: Analysis settings

    Returns:
        Dict with fundamental score and breakdown
    """
    if not metrics.get('calculation_successful', False):
        return {
            'fundamental_score': 0,
            'score_breakdown': {},
            'passed_filters': False
        }

    scoring = settings.get('scoring', {})
    fund_components = scoring.get('fundamental_components', {})

    scores = {}

    # 1. Gross Profitability (35 points)
    gross_prof = metrics.get('gross_profitability')
    gross_score = 0
    if gross_prof:
        if gross_prof >= 0.40:  # Exceptional (40%+)
            gross_score = 35
        elif gross_prof >= 0.30:  # Excellent (30-40%)
            gross_score = 30
        elif gross_prof >= 0.20:  # Good (20-30%)
            gross_score = 20
        elif gross_prof >= 0.10:  # Fair (10-20%)
            gross_score = 10
    scores['gross_profitability'] = gross_score

    # 2. Piotroski F-Score (25 points)
    piotroski = metrics.get('piotroski_score')
    piotroski_score = 0
    if piotroski is not None:
        # Convert 0-9 score to 0-25 points
        # 9 = 25 pts, 8 = 22 pts, 7 = 19 pts, etc.
        piotroski_score = int((piotroski / 9) * 25)
    scores['piotroski_score'] = piotroski_score

    # 3. Profitability (20 points)
    profit_score = 0
    profit_margin = metrics.get('profit_margin')
    roe = metrics.get('roe')

    if profit_margin:
        if profit_margin >= 0.20:  # 20%+ margin
            profit_score += 10
        elif profit_margin >= 0.10:  # 10-20% margin
            profit_score += 7
        elif profit_margin >= 0.05:  # 5-10% margin
            profit_score += 5

    if roe:
        if roe >= 0.20:  # 20%+ ROE
            profit_score += 10
        elif roe >= 0.15:  # 15-20% ROE
            profit_score += 7
        elif roe >= 0.10:  # 10-15% ROE
            profit_score += 5

    scores['profitability'] = min(profit_score, 20)  # Cap at 20

    # 4. Valuation (10 points)
    pe_ratio = metrics.get('pe_ratio')
    valuation_score = 0
    if pe_ratio:
        if 10 <= pe_ratio <= 20:  # Sweet spot
            valuation_score = 10
        elif 5 <= pe_ratio < 10 or 20 < pe_ratio <= 25:  # Good
            valuation_score = 7
        elif 0 < pe_ratio < 5 or 25 < pe_ratio <= 30:  # Fair
            valuation_score = 5
    scores['valuation'] = valuation_score

    # 5. Growth (10 points)
    revenue_growth = metrics.get('revenue_growth')
    growth_score = 0
    if revenue_growth:
        if revenue_growth >= 0.20:  # 20%+ growth
            growth_score = 10
        elif revenue_growth >= 0.10:  # 10-20% growth
            growth_score = 7
        elif revenue_growth >= 0.05:  # 5-10% growth
            growth_score = 5
        elif revenue_growth >= 0:  # Positive growth
            growth_score = 3
    scores['growth'] = growth_score

    # Calculate total fundamental score
    total_score = sum(scores.values())

    # Check if passed minimum filters
    fund_settings = settings.get('analysis', {}).get('fundamental', {})

    passed_filters = True
    filter_results = {}

    if fund_settings.get('require_profitable', False):
        passed = metrics.get('is_profitable', False)
        filter_results['profitable_filter'] = passed
        passed_filters = passed_filters and passed

    if fund_settings.get('use_gross_profitability', False):
        passed = metrics.get('gross_profit_ok', False)
        filter_results['gross_profit_filter'] = passed
        passed_filters = passed_filters and passed

    if fund_settings.get('use_piotroski_score', False):
        passed = metrics.get('piotroski_ok', False)
        filter_results['piotroski_filter'] = passed
        passed_filters = passed_filters and passed

    if fund_settings.get('require_reasonable_pe', False):
        passed = metrics.get('pe_reasonable', False)
        filter_results['pe_filter'] = passed
        passed_filters = passed_filters and passed

    return {
        'fundamental_score': total_score,
        'score_breakdown': scores,
        'passed_filters': passed_filters,
        'filter_results': filter_results,
        'max_possible_score': 100
    }
