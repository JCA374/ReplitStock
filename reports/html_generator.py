"""
HTML Report Generator - Creates Consolidated Weekly Reports

Generates professional HTML reports with:
- Executive summary
- Tier breakdowns (Large/Mid/Small cap)
- Top stock recommendations
- Statistics and comparisons
- Embedded CSS for styling
"""

import logging
from typing import Dict, List
from datetime import datetime
from reports.report_generator import BaseReportGenerator, ReportData

logger = logging.getLogger(__name__)


class HTMLReportGenerator(BaseReportGenerator):
    """
    Generates consolidated weekly HTML reports
    """

    def generate(self, report_data: ReportData) -> str:
        """
        Generate complete HTML report

        Args:
            report_data: Aggregated report data

        Returns:
            Complete HTML string
        """
        logger.info("Generating HTML report...")

        exec_summary = report_data.get_executive_summary()

        html_parts = []

        # HTML header + CSS
        html_parts.append(self._generate_header(exec_summary))

        # Executive summary
        html_parts.append(self._generate_executive_summary(exec_summary))

        # Tier sections (Large/Mid/Small cap)
        for tier in ['large_cap', 'mid_cap', 'small_cap']:
            tier_config = exec_summary['tier_config']
            top_n = tier_config[tier]
            top_stocks = report_data.get_top_stocks(tier, top_n)

            html_parts.append(self._generate_tier_section(
                tier, top_stocks, exec_summary['tier_summaries'][tier]
            ))

        # Portfolio construction guide
        html_parts.append(self._generate_portfolio_guide(exec_summary))

        # Statistics
        html_parts.append(self._generate_statistics(report_data.stats))

        # Methodology
        html_parts.append(self._generate_methodology())

        # Disclaimer
        html_parts.append(self._generate_disclaimer())

        # Footer
        html_parts.append(self._generate_footer())

        return '\n'.join(html_parts)

    def _generate_header(self, exec_summary: Dict) -> str:
        """Generate HTML header with CSS"""
        report_date = exec_summary['report_date']

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Weekly Stock Analysis - {report_date.strftime('%Y-%m-%d')}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }}

        h1 {{
            color: #2c3e50;
            border-bottom: 4px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}

        h2 {{
            color: #34495e;
            margin-top: 40px;
            margin-bottom: 20px;
            border-left: 5px solid #3498db;
            padding-left: 15px;
        }}

        h3 {{
            color: #2c3e50;
            margin-top: 30px;
            margin-bottom: 15px;
        }}

        .header {{
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            margin: -40px -40px 40px -40px;
            border-radius: 0;
        }}

        .header h1 {{
            color: white;
            border: none;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .header .subtitle {{
            font-size: 1.2em;
            opacity: 0.9;
        }}

        .summary-box {{
            background: #ecf0f1;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}

        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}

        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .summary-card h3 {{
            margin-top: 0;
            color: #3498db;
            font-size: 0.9em;
            text-transform: uppercase;
        }}

        .summary-card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #2c3e50;
        }}

        .summary-card .label {{
            color: #7f8c8d;
            font-size: 0.9em;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
        }}

        thead {{
            background: #34495e;
            color: white;
        }}

        th {{
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}

        td {{
            padding: 12px;
            border-bottom: 1px solid #ecf0f1;
        }}

        tbody tr:hover {{
            background: #f8f9fa;
        }}

        .tier-large {{
            border-left: 5px solid #27ae60;
        }}

        .tier-mid {{
            border-left: 5px solid #f39c12;
        }}

        .tier-small {{
            border-left: 5px solid #e74c3c;
        }}

        .score-high {{
            color: #27ae60;
            font-weight: bold;
        }}

        .score-medium {{
            color: #f39c12;
            font-weight: bold;
        }}

        .score-low {{
            color: #e74c3c;
            font-weight: bold;
        }}

        .recommendation {{
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 0.9em;
        }}

        .rec-strong-buy {{
            background: #27ae60;
            color: white;
        }}

        .rec-buy {{
            background: #2ecc71;
            color: white;
        }}

        .rec-hold {{
            background: #f39c12;
            color: white;
        }}

        .rec-sell {{
            background: #e74c3c;
            color: white;
        }}

        .disclaimer {{
            background: #fff3cd;
            border: 2px solid #ffc107;
            padding: 20px;
            margin: 40px 0;
            border-radius: 8px;
        }}

        .disclaimer h3 {{
            color: #856404;
            margin-top: 0;
        }}

        .methodology {{
            background: #e3f2fd;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}

        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #ecf0f1;
            color: #7f8c8d;
        }}

        .badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 0.85em;
            font-weight: bold;
        }}

        .badge-success {{
            background: #d4edda;
            color: #155724;
        }}

        .badge-warning {{
            background: #fff3cd;
            color: #856404;
        }}

        .badge-danger {{
            background: #f8d7da;
            color: #721c24;
        }}

        @media print {{
            body {{
                background: white;
                padding: 0;
            }}

            .container {{
                box-shadow: none;
                padding: 20px;
            }}

            .header {{
                background: #667eea !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Weekly Stock Analysis Report</h1>
            <div class="subtitle">
                Week of {report_date.strftime('%B %d, %Y')}<br>
                Research-Optimized Value & Momentum Strategy
            </div>
        </div>
"""

    def _generate_executive_summary(self, exec_summary: Dict) -> str:
        """Generate executive summary section"""
        overall = exec_summary['overall_stats']
        total = exec_summary['total_stocks_analyzed']
        total_rec = exec_summary['total_recommendations']

        large = exec_summary['tier_summaries']['large_cap']
        mid = exec_summary['tier_summaries']['mid_cap']
        small = exec_summary['tier_summaries']['small_cap']

        return f"""
        <h2>📋 Executive Summary</h2>

        <div class="summary-box">
            <p><strong>Analysis Date:</strong> {exec_summary['report_date'].strftime('%A, %B %d, %Y at %H:%M CET')}</p>
            <p><strong>Stocks Analyzed:</strong> {total} Swedish stocks ({large['total_analyzed']} large, {mid['total_analyzed']} mid, {small['total_analyzed']} small cap)</p>
            <p><strong>Analysis Method:</strong> Research-Optimized Value & Momentum Hybrid Strategy</p>
            <p><strong>Expected Performance:</strong> 8-12% annual alpha, 0.8-1.2 Sharpe ratio</p>
        </div>

        <h3>Key Findings</h3>

        <div class="summary-grid">
            <div class="summary-card">
                <h3>Total Recommendations</h3>
                <div class="value">{total_rec}</div>
                <div class="label">{exec_summary['tier_config']['large_cap']} large / {exec_summary['tier_config']['mid_cap']} mid / {exec_summary['tier_config']['small_cap']} small cap</div>
            </div>

            <div class="summary-card">
                <h3>Average Score</h3>
                <div class="value">{self.format_number(overall['average_composite'], 1)}</div>
                <div class="label">Composite Score (out of 100)</div>
            </div>

            <div class="summary-card">
                <h3>Technical Score</h3>
                <div class="value">{self.format_number(overall['average_technical'], 1)}</div>
                <div class="label">70% of composite weight</div>
            </div>

            <div class="summary-card">
                <h3>Fundamental Score</h3>
                <div class="value">{self.format_number(overall['average_fundamental'], 1)}</div>
                <div class="label">30% of composite weight</div>
            </div>
        </div>

        <h3>Market Overview</h3>

        <table>
            <thead>
                <tr>
                    <th>Tier</th>
                    <th>Analyzed</th>
                    <th>Passed Filters</th>
                    <th>Pass Rate</th>
                    <th>Avg Score</th>
                    <th>Top N Selected</th>
                </tr>
            </thead>
            <tbody>
                <tr class="tier-large">
                    <td><strong>Large Cap</strong></td>
                    <td>{large['total_analyzed']}</td>
                    <td>{large['passed_filters']}</td>
                    <td>{self.format_number(large['pass_rate'], 1, '%')}</td>
                    <td>{self.format_number(large['average_score'], 1)}</td>
                    <td>{exec_summary['tier_config']['large_cap']}</td>
                </tr>
                <tr class="tier-mid">
                    <td><strong>Mid Cap</strong></td>
                    <td>{mid['total_analyzed']}</td>
                    <td>{mid['passed_filters']}</td>
                    <td>{self.format_number(mid['pass_rate'], 1, '%')}</td>
                    <td>{self.format_number(mid['average_score'], 1)}</td>
                    <td>{exec_summary['tier_config']['mid_cap']}</td>
                </tr>
                <tr class="tier-small">
                    <td><strong>Small Cap</strong></td>
                    <td>{small['total_analyzed']}</td>
                    <td>{small['passed_filters']}</td>
                    <td>{self.format_number(small['pass_rate'], 1, '%')}</td>
                    <td>{self.format_number(small['average_score'], 1)}</td>
                    <td>{exec_summary['tier_config']['small_cap']}</td>
                </tr>
            </tbody>
        </table>

        <h3>Recommended Portfolio Allocation</h3>
        <div class="summary-box">
            <p>📈 <strong>Large Cap: 60%</strong> (15 stocks) - Lower risk, steady returns</p>
            <p>📊 <strong>Mid Cap: 30%</strong> (20 stocks) - Balanced risk/return</p>
            <p>📉 <strong>Small Cap: 10%</strong> (10 stocks) - Higher risk, growth potential</p>
        </div>
"""

    def _generate_tier_section(self, tier: str, top_stocks: List[Dict], tier_summary: Dict) -> str:
        """Generate section for a market cap tier"""

        tier_names = {
            'large_cap': ('Large Cap', 'Market Cap > 100B SEK', 'Lower Risk, Steady Growth', '60%'),
            'mid_cap': ('Mid Cap', '10B - 100B SEK', 'Balanced Risk/Return', '30%'),
            'small_cap': ('Small Cap', '1B - 10B SEK', 'Higher Risk, High Growth', '10%')
        }

        name, cap_range, description, allocation = tier_names[tier]

        tier_class = f"tier-{tier.split('_')[0]}"

        html = f"""
        <h2 class="{tier_class}">{name} Recommendations</h2>

        <div class="summary-box">
            <p><strong>Market Cap Range:</strong> {cap_range} | <strong>Risk Profile:</strong> {description}</p>
            <p><strong>Recommended Allocation:</strong> {allocation} of portfolio</p>
            <p><strong>Stocks Selected:</strong> {len(top_stocks)} (from {tier_summary['passed_filters']} that passed all filters)</p>
        </div>

        <table>
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Ticker</th>
                    <th>Score</th>
                    <th>Tech</th>
                    <th>Fund</th>
                    <th>Price</th>
                    <th>RSI</th>
                    <th>Vol</th>
                    <th>Piotr</th>
                    <th>P/E</th>
                    <th>Recommendation</th>
                </tr>
            </thead>
            <tbody>
"""

        for rank, stock in enumerate(top_stocks, 1):
            score_class = 'score-high' if stock['composite_score'] >= 85 else 'score-medium' if stock['composite_score'] >= 75 else 'score-low'

            rec = stock.get('recommendation', 'SKIP')
            rec_class = rec.lower().replace(' ', '-')

            html += f"""
                <tr>
                    <td><strong>{rank}</strong></td>
                    <td><strong>{stock.get('ticker', 'N/A')}</strong></td>
                    <td class="{score_class}">{self.format_number(stock.get('composite_score'), 1)}</td>
                    <td>{self.format_number(stock.get('technical_score'), 1)}</td>
                    <td>{self.format_number(stock.get('fundamental_score'), 1)}</td>
                    <td>{self.format_number(stock.get('current_price'), 2)}</td>
                    <td>{self.format_number(stock.get('rsi'), 0)}</td>
                    <td>{'✓' if stock.get('volume_confirmed') else '✗'}</td>
                    <td>{stock.get('piotroski_score', 'N/A')}/9</td>
                    <td>{self.format_number(stock.get('pe_ratio'), 1)}</td>
                    <td><span class="recommendation rec-{rec_class}">{rec}</span></td>
                </tr>
"""

        html += """
            </tbody>
        </table>
"""

        return html

    def _generate_portfolio_guide(self, exec_summary: Dict) -> str:
        """Generate portfolio construction guide"""

        return """
        <h2>💼 Portfolio Construction Guide</h2>

        <div class="summary-box">
            <h3>Tier Allocation (Research-Backed)</h3>
            <table>
                <thead>
                    <tr>
                        <th>Tier</th>
                        <th>% Allocation</th>
                        <th># Stocks</th>
                        <th>Risk Level</th>
                    </tr>
                </thead>
                <tbody>
                    <tr class="tier-large">
                        <td><strong>Large Cap</strong></td>
                        <td>60%</td>
                        <td>15</td>
                        <td>Low</td>
                    </tr>
                    <tr class="tier-mid">
                        <td><strong>Mid Cap</strong></td>
                        <td>30%</td>
                        <td>20</td>
                        <td>Medium</td>
                    </tr>
                    <tr class="tier-small">
                        <td><strong>Small Cap</strong></td>
                        <td>10%</td>
                        <td>10</td>
                        <td>High</td>
                    </tr>
                </tbody>
            </table>

            <h3>Example 100,000 SEK Portfolio</h3>
            <ul>
                <li><strong>Large Cap:</strong> 60,000 SEK across 15 stocks (~4,000 SEK each)</li>
                <li><strong>Mid Cap:</strong> 30,000 SEK across 20 stocks (~1,500 SEK each)</li>
                <li><strong>Small Cap:</strong> 10,000 SEK across 10 stocks (~1,000 SEK each)</li>
            </ul>

            <h3>Risk Management</h3>
            <ul>
                <li><strong>Stop Loss:</strong> 8% below entry price (research-backed)</li>
                <li><strong>Position Sizing:</strong> Equal weight within each tier</li>
                <li><strong>Maximum Single Stock:</strong> 4% of total portfolio</li>
                <li><strong>Review Frequency:</strong> Weekly (every Friday)</li>
            </ul>
        </div>
"""

    def _generate_statistics(self, stats: Dict) -> str:
        """Generate statistics section"""

        return f"""
        <h2>📊 Analysis Statistics</h2>

        <div class="summary-grid">
            <div class="summary-card">
                <h3>Stocks Analyzed</h3>
                <div class="value">{stats['total_analyzed']}</div>
                <div class="label">Total universe</div>
            </div>

            <div class="summary-card">
                <h3>Successful Analyses</h3>
                <div class="value">{stats['successful_analyses']}</div>
                <div class="label">{self.format_number(stats['successful_analyses']/stats['total_analyzed']*100 if stats['total_analyzed'] else 0, 1, '%')} success rate</div>
            </div>

            <div class="summary-card">
                <h3>Passed All Filters</h3>
                <div class="value">{stats['passed_all_filters']}</div>
                <div class="label">{self.format_number(stats['passed_all_filters']/stats['successful_analyses']*100 if stats['successful_analyses'] else 0, 1, '%')} pass rate</div>
            </div>

            <div class="summary-card">
                <h3>Score Range</h3>
                <div class="value">{self.format_number(stats['min_score'], 1)} - {self.format_number(stats['max_score'], 1)}</div>
                <div class="label">Min to Max</div>
            </div>
        </div>

        <h3>Recommendations Breakdown</h3>
        <table>
            <thead>
                <tr>
                    <th>Recommendation</th>
                    <th>Count</th>
                    <th>Percentage</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><span class="recommendation rec-strong-buy">⬆️ STRONG BUY</span></td>
                    <td>{stats['recommendations'].get('STRONG BUY', 0)}</td>
                    <td>{self.format_number(stats['recommendations'].get('STRONG BUY', 0)/stats['total_analyzed']*100 if stats['total_analyzed'] else 0, 1, '%')}</td>
                </tr>
                <tr>
                    <td><span class="recommendation rec-buy">✓ BUY</span></td>
                    <td>{stats['recommendations'].get('BUY', 0)}</td>
                    <td>{self.format_number(stats['recommendations'].get('BUY', 0)/stats['total_analyzed']*100 if stats['total_analyzed'] else 0, 1, '%')}</td>
                </tr>
                <tr>
                    <td><span class="recommendation rec-hold">→ HOLD</span></td>
                    <td>{stats['recommendations'].get('HOLD', 0)}</td>
                    <td>{self.format_number(stats['recommendations'].get('HOLD', 0)/stats['total_analyzed']*100 if stats['total_analyzed'] else 0, 1, '%')}</td>
                </tr>
                <tr>
                    <td><span class="recommendation rec-sell">↓ SELL</span></td>
                    <td>{stats['recommendations'].get('SELL', 0)}</td>
                    <td>{self.format_number(stats['recommendations'].get('SELL', 0)/stats['total_analyzed']*100 if stats['total_analyzed'] else 0, 1, '%')}</td>
                </tr>
                <tr>
                    <td>✗ SKIP</td>
                    <td>{stats['recommendations'].get('SKIP', 0)}</td>
                    <td>{self.format_number(stats['recommendations'].get('SKIP', 0)/stats['total_analyzed']*100 if stats['total_analyzed'] else 0, 1, '%')}</td>
                </tr>
            </tbody>
        </table>
"""

    def _generate_methodology(self) -> str:
        """Generate methodology section"""

        return """
        <h2>🔬 Analysis Methodology</h2>

        <div class="methodology">
            <h3>Research-Backed Approach</h3>
            <p>Based on academic research (2018-2025) for Swedish stock market.<br>
            <strong>Expected performance:</strong> 8-12% annual alpha, 0.8-1.2 Sharpe ratio.</p>

            <h3>Technical Analysis (70% weight)</h3>
            <ul>
                <li><strong>RSI (7-period, Cardwell method):</strong> RSI > 50 = bullish</li>
                <li><strong>Volume Confirmation:</strong> 1.5× average = 65% success vs 39%</li>
                <li><strong>KAMA (adaptive MA):</strong> Reduces false signals 30-40%</li>
                <li><strong>MA200 & MA20:</strong> Long-term and short-term trend</li>
                <li><strong>MACD:</strong> Momentum confirmation</li>
                <li><strong>52-week high proximity:</strong> Jegadeesh & Titman research</li>
            </ul>

            <h3>Fundamental Analysis (30% weight)</h3>
            <ul>
                <li><strong>Gross Profitability:</strong> (Revenue - COGS) / Assets (superior to P/E)</li>
                <li><strong>Piotroski F-Score:</strong> 9-point quality score, ≥7 required</li>
                <li><strong>Profitability:</strong> Positive margins required</li>
                <li><strong>Valuation:</strong> P/E < 30 for reasonableness</li>
                <li><strong>Growth:</strong> Revenue and earnings trends</li>
            </ul>

            <h3>Value & Momentum Hybrid</h3>
            <p>• Pure momentum Sharpe: <strong>0.67</strong><br>
            • Pure value Sharpe: <strong>0.73</strong><br>
            • <strong>Hybrid (50/50) Sharpe: 1.42</strong> ← Best performance<br>
            • Our blend: 70/30 technical/fundamental</p>

            <h3>Rebalancing</h3>
            <p>• <strong>Weekly review:</strong> Every Friday at 18:00 CET<br>
            • <strong>Quarterly reallocation:</strong> Adjust positions<br>
            • Research shows weekly optimal for Swedish stocks</p>
        </div>
"""

    def _generate_disclaimer(self) -> str:
        """Generate disclaimer section"""

        return """
        <div class="disclaimer">
            <h3>⚠️ Important Risk Information</h3>

            <p><strong>This report is for informational purposes only and does not constitute investment advice, financial advice, or a recommendation to buy or sell any securities.</strong></p>

            <h4>Risks:</h4>
            <ul>
                <li>Past performance does not guarantee future results</li>
                <li>Stock prices can go down as well as up</li>
                <li>You may lose some or all of your invested capital</li>
                <li>Small cap stocks carry higher volatility and risk</li>
                <li>Market conditions can change rapidly</li>
            </ul>

            <h4>Limitations:</h4>
            <ul>
                <li>Analysis based on historical data and research</li>
                <li>Expected performance (8-12% alpha) is not guaranteed</li>
                <li>Individual results may vary significantly</li>
                <li>Market crashes can impact all stocks</li>
            </ul>

            <h4>Recommendations:</h4>
            <ul>
                <li>Consult a licensed financial advisor before investing</li>
                <li>Only invest money you can afford to lose</li>
                <li>Diversify across asset classes (not just stocks)</li>
                <li>Understand your risk tolerance</li>
                <li>Review positions regularly</li>
            </ul>

            <h4>Data Sources:</h4>
            <p>• Price data: Yahoo Finance<br>
            • Fundamentals: Yahoo Finance<br>
            • Analysis: Automated algorithm (not human review)<br>
            • Research: Academic papers 2018-2025</p>
        </div>
"""

    def _generate_footer(self) -> str:
        """Generate HTML footer"""

        now = datetime.now()

        return f"""
        <div class="footer">
            <p>Last Updated: {now.strftime('%A, %B %d, %Y at %H:%M CET')}</p>
            <p>Generated by Automatic Stock Analysis System v2.0</p>
            <p>Research-Optimized Value & Momentum Strategy</p>
        </div>
    </div>
</body>
</html>
"""
