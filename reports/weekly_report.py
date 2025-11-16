"""
Weekly Report Orchestrator

Coordinates generation of all report formats (HTML, CSV, JSON)
and manages file saving and archiving.
"""

import logging
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime

from reports.report_generator import ReportData
from reports.html_generator import HTMLReportGenerator
from reports.csv_json_generators import CSVReportGenerator, JSONReportGenerator

logger = logging.getLogger(__name__)


class WeeklyReportOrchestrator:
    """
    Orchestrates the generation of consolidated weekly reports in all formats
    """

    def __init__(self, settings: Dict):
        """
        Initialize report orchestrator

        Args:
            settings: Analysis settings dictionary
        """
        self.settings = settings
        self.output_settings = settings.get('output', {})

        # Initialize generators
        self.html_gen = HTMLReportGenerator(settings)
        self.csv_gen = CSVReportGenerator(settings)
        self.json_gen = JSONReportGenerator(settings)

        # Report formats to generate
        self.enabled_formats = self.output_settings.get('reports', ['html', 'csv', 'json'])

        logger.info(f"Report orchestrator initialized. Formats: {', '.join(self.enabled_formats)}")

    def generate_weekly_report(
        self,
        analysis_results: List[Dict],
        previous_results: Optional[List[Dict]] = None
    ) -> Dict[str, Path]:
        """
        Generate complete weekly report in all enabled formats

        Args:
            analysis_results: List of analysis results from BatchAnalyzer
            previous_results: Optional previous week's results for comparison

        Returns:
            Dict mapping format name to output file path
        """
        logger.info("=" * 70)
        logger.info("GENERATING WEEKLY REPORT")
        logger.info("=" * 70)

        # Prepare report data
        report_data = ReportData(analysis_results, self.settings)

        # Track generated files
        generated_files = {}

        # Generate each enabled format
        if 'html' in self.enabled_formats:
            html_path = self._generate_and_save_html(report_data)
            generated_files['html'] = html_path

        if 'csv' in self.enabled_formats:
            csv_path = self._generate_and_save_csv(report_data)
            generated_files['csv'] = csv_path

        if 'json' in self.enabled_formats:
            json_path = self._generate_and_save_json(report_data)
            generated_files['json'] = json_path

        # Summary
        logger.info("=" * 70)
        logger.info("REPORT GENERATION COMPLETE")
        logger.info("=" * 70)

        for format_name, file_path in generated_files.items():
            logger.info(f"  {format_name.upper()}: {file_path}")

        return generated_files

    def _generate_and_save_html(self, report_data: ReportData) -> Path:
        """Generate and save HTML report"""

        logger.info("Generating HTML report...")

        # Generate HTML content
        html_content = self.html_gen.generate(report_data)

        # Generate filename
        filename = self.html_gen.generate_filename('html', report_data.report_date)
        output_path = self.html_gen.get_output_path(filename)

        # Save file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"HTML report saved: {output_path} ({len(html_content):,} bytes)")

        # Archive copy
        self.html_gen.save_to_historical(filename, html_content)

        return output_path

    def _generate_and_save_csv(self, report_data: ReportData) -> Path:
        """Generate and save CSV report"""

        logger.info("Generating CSV report...")

        # Generate CSV content
        csv_content = self.csv_gen.generate(report_data)

        # Generate filename
        filename = self.csv_gen.generate_filename('csv', report_data.report_date)
        output_path = self.csv_gen.get_output_path(filename)

        # Save file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(csv_content)

        logger.info(f"CSV report saved: {output_path} ({len(csv_content):,} bytes)")

        # Archive copy
        self.csv_gen.save_to_historical(filename, csv_content)

        return output_path

    def _generate_and_save_json(self, report_data: ReportData) -> Path:
        """Generate and save JSON report"""

        logger.info("Generating JSON report...")

        # Generate JSON content
        json_content = self.json_gen.generate(report_data)

        # Generate filename
        filename = self.json_gen.generate_filename('json', report_data.report_date)
        output_path = self.json_gen.get_output_path(filename)

        # Save file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(json_content)

        logger.info(f"JSON report saved: {output_path} ({len(json_content):,} bytes)")

        # Archive copy
        self.json_gen.save_to_historical(filename, json_content)

        return output_path

    def get_report_summary(self, report_data: ReportData) -> str:
        """
        Get a text summary of the report

        Args:
            report_data: Report data

        Returns:
            Text summary
        """
        exec_summary = report_data.get_executive_summary()

        summary_lines = []
        summary_lines.append("=" * 70)
        summary_lines.append("WEEKLY STOCK ANALYSIS SUMMARY")
        summary_lines.append("=" * 70)
        summary_lines.append(f"Report Date: {exec_summary['report_date'].strftime('%Y-%m-%d %H:%M')}")
        summary_lines.append(f"Stocks Analyzed: {exec_summary['total_stocks_analyzed']}")
        summary_lines.append(f"Recommendations: {exec_summary['total_recommendations']} total")
        summary_lines.append("")

        summary_lines.append("Tier Breakdown:")
        for tier in ['large_cap', 'mid_cap', 'small_cap']:
            tier_sum = exec_summary['tier_summaries'][tier]
            tier_config = exec_summary['tier_config'][tier]

            summary_lines.append(
                f"  {tier}: {tier_config} selected from "
                f"{tier_sum['passed_filters']} that passed filters "
                f"(avg score: {tier_sum['average_score']:.1f})"
            )

        summary_lines.append("")
        summary_lines.append("Overall Statistics:")
        overall = exec_summary['overall_stats']
        summary_lines.append(f"  Average Composite: {overall['average_composite']:.1f}/100")
        summary_lines.append(f"  Average Technical: {overall['average_technical']:.1f}/100")
        summary_lines.append(f"  Average Fundamental: {overall['average_fundamental']:.1f}/100")
        summary_lines.append(f"  Passed All Filters: {overall['total_passed_filters']}")

        summary_lines.append("")
        summary_lines.append("Recommendations:")
        for rec, count in exec_summary['recommendations'].items():
            if count > 0:
                summary_lines.append(f"  {rec}: {count}")

        summary_lines.append("=" * 70)

        return "\n".join(summary_lines)
