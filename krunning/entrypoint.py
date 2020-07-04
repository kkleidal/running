import argparse
from typing import Dict

from .reports_gen import ReportGenerator, PDFReportsReportBuilder, reports


def report_main(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output", required=True, help="output path")
    subparsers = parser.add_subparsers(title="report", required=True)

    built_reports: Dict[str, ReportGenerator] = {}

    for name, report_cls in reports.items():
        report_parser = subparsers.add_parser(name)
        report_parser.set_defaults(report=name)

        report = report_cls()
        built_reports[name] = report
        report.build_parser(report_parser)

    parsed_args = parser.parse_args(args)
    report = built_reports[parsed_args.report]
    report_builder = PDFReportsReportBuilder()
    report.generate_report(parsed_args, report_builder)
    report_builder.write_to(parsed_args.output)
