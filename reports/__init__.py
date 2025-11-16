"""
Reports Package - Weekly Stock Analysis Reports

Generates consolidated weekly reports in multiple formats:
- HTML: Professional, formatted reports
- CSV: Excel-compatible for analysis
- JSON: Programmatic access
"""

from reports.weekly_report import WeeklyReportOrchestrator
from reports.report_generator import ReportData

__all__ = ['WeeklyReportOrchestrator', 'ReportData']
