"""
CSV and JSON Report Generators

CSV: Excel-compatible format for easy analysis
JSON: Programmatic access for further processing
"""

import logging
import csv
import json
from typing import Dict, List
from io import StringIO
from reports.report_generator import BaseReportGenerator, ReportData

logger = logging.getLogger(__name__)


class CSVReportGenerator(BaseReportGenerator):
    """
    Generates CSV reports (Excel compatible)
    """

    def generate(self, report_data: ReportData) -> str:
        """
        Generate CSV report

        Args:
            report_data: Aggregated report data

        Returns:
            CSV string
        """
        logger.info("Generating CSV report...")

        # Get all stocks that passed filters, sorted by score
        all_stocks = sorted(
            report_data.passed_filters,
            key=lambda x: x.get('composite_score', 0),
            reverse=True
        )

        # CSV column headers
        headers = [
            'Rank',
            'Tier',
            'Ticker',
            'Composite_Score',
            'Technical_Score',
            'Fundamental_Score',
            'Recommendation',
            'Current_Price',
            'Market_Cap',
            'MA200_Distance_%',
            'MA20_Distance_%',
            'RSI_7',
            'Volume_Confirmed',
            '52Week_High_Proximity_%',
            'MACD_Bullish',
            'Piotroski_Score',
            'Gross_Profitability',
            'PE_Ratio',
            'Profit_Margin',
            'Revenue_Growth',
            'Analysis_Date'
        ]

        # Create CSV in memory
        output = StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(headers)

        # Write data rows
        for rank, stock in enumerate(all_stocks, 1):
            row = [
                rank,
                stock.get('market_cap_tier', 'unknown'),
                stock.get('ticker', ''),
                self._format_csv_number(stock.get('composite_score')),
                self._format_csv_number(stock.get('technical_score')),
                self._format_csv_number(stock.get('fundamental_score')),
                stock.get('recommendation', ''),
                self._format_csv_number(stock.get('current_price')),
                self._format_csv_number(stock.get('market_cap')),
                self._format_csv_number(stock.get('ma200_distance_pct')),
                self._format_csv_number(stock.get('ma20_distance_pct')),
                self._format_csv_number(stock.get('rsi')),
                'Yes' if stock.get('volume_confirmed') else 'No',
                self._format_csv_number(stock.get('high52_proximity_pct')),
                'Yes' if stock.get('technical_indicators', {}).get('macd_bullish') else 'No',
                stock.get('piotroski_score', ''),
                self._format_csv_number(stock.get('gross_profitability')),
                self._format_csv_number(stock.get('pe_ratio')),
                self._format_csv_number(stock.get('profit_margin')),
                self._format_csv_number(stock.get('revenue_growth')),
                stock.get('analysis_date', '')
            ]

            writer.writerow(row)

        csv_content = output.getvalue()
        output.close()

        logger.info(f"CSV report generated: {len(all_stocks)} stocks")

        return csv_content

    def _format_csv_number(self, value) -> str:
        """Format number for CSV (handle None gracefully)"""
        if value is None:
            return ''
        if isinstance(value, (int, float)):
            return f"{value:.2f}"
        return str(value)


class JSONReportGenerator(BaseReportGenerator):
    """
    Generates JSON reports for programmatic access
    """

    def generate(self, report_data: ReportData) -> str:
        """
        Generate JSON report

        Args:
            report_data: Aggregated report data

        Returns:
            JSON string (formatted)
        """
        logger.info("Generating JSON report...")

        exec_summary = report_data.get_executive_summary()

        # Get top stocks by tier
        large_stocks = report_data.get_top_stocks('large_cap',
            exec_summary['tier_config']['large_cap'])
        mid_stocks = report_data.get_top_stocks('mid_cap',
            exec_summary['tier_config']['mid_cap'])
        small_stocks = report_data.get_top_stocks('small_cap',
            exec_summary['tier_config']['small_cap'])

        # Build JSON structure
        report = {
            'metadata': {
                'report_date': exec_summary['report_date'].isoformat(),
                'report_type': 'weekly_consolidated',
                'version': '2.0',
                'analysis_method': 'Research-Optimized Value & Momentum Hybrid'
            },

            'executive_summary': {
                'total_stocks_analyzed': exec_summary['total_stocks_analyzed'],
                'total_recommendations': exec_summary['total_recommendations'],
                'tier_configuration': exec_summary['tier_config'],
                'overall_statistics': exec_summary['overall_stats'],
                'tier_summaries': exec_summary['tier_summaries'],
                'recommendations_breakdown': exec_summary['recommendations']
            },

            'recommendations': {
                'large_cap': self._format_stocks_for_json(large_stocks),
                'mid_cap': self._format_stocks_for_json(mid_stocks),
                'small_cap': self._format_stocks_for_json(small_stocks)
            },

            'statistics': {
                'total': report_data.stats['total_analyzed'],
                'successful': report_data.stats['successful_analyses'],
                'passed_filters': report_data.stats['passed_all_filters'],
                'failed_filters': report_data.stats['failed_any_filter'],
                'scores': {
                    'average_composite': report_data.stats['average_composite_score'],
                    'average_technical': report_data.stats['average_technical_score'],
                    'average_fundamental': report_data.stats['average_fundamental_score'],
                    'max': report_data.stats['max_score'],
                    'min': report_data.stats['min_score']
                },
                'filter_statistics': report_data.stats['filter_statistics']
            },

            'portfolio_allocation': {
                'recommended': {
                    'large_cap': 60,
                    'mid_cap': 30,
                    'small_cap': 10
                },
                'description': {
                    'large_cap': 'Lower risk, steady returns',
                    'mid_cap': 'Balanced risk/return',
                    'small_cap': 'Higher risk, growth potential'
                }
            }
        }

        # Convert to JSON with nice formatting
        json_content = json.dumps(report, indent=2, default=str)

        logger.info(f"JSON report generated")

        return json_content

    def _format_stocks_for_json(self, stocks: List[Dict]) -> List[Dict]:
        """Format stock list for JSON output"""

        formatted = []

        for rank, stock in enumerate(stocks, 1):
            formatted.append({
                'rank': rank,
                'ticker': stock.get('ticker'),
                'scores': {
                    'composite': stock.get('composite_score'),
                    'technical': stock.get('technical_score'),
                    'fundamental': stock.get('fundamental_score')
                },
                'recommendation': stock.get('recommendation'),
                'price_data': {
                    'current_price': stock.get('current_price'),
                    'market_cap': stock.get('market_cap'),
                    'ma200_distance_pct': stock.get('ma200_distance_pct'),
                    'ma20_distance_pct': stock.get('ma20_distance_pct'),
                    'high52_proximity_pct': stock.get('high52_proximity_pct')
                },
                'technical_indicators': {
                    'rsi': stock.get('rsi'),
                    'volume_confirmed': stock.get('volume_confirmed'),
                    'macd_bullish': stock.get('technical_indicators', {}).get('macd_bullish'),
                    'above_ma200': stock.get('technical_indicators', {}).get('above_ma200'),
                    'above_ma20': stock.get('technical_indicators', {}).get('above_ma20')
                },
                'fundamental_metrics': {
                    'piotroski_score': stock.get('piotroski_score'),
                    'gross_profitability': stock.get('gross_profitability'),
                    'pe_ratio': stock.get('pe_ratio'),
                    'profit_margin': stock.get('profit_margin'),
                    'revenue_growth': stock.get('revenue_growth')
                },
                'filters_passed': stock.get('passed_all_filters'),
                'analysis_date': stock.get('analysis_date')
            })

        return formatted
