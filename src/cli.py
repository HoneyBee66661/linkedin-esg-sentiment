# -*- coding: utf-8 -*-
"""
CLI entry point for LinkedIn ESG Sentiment pipeline.

Usage:
    linkedin-esg extract <input_path> [--out DIR] [--hiring-filter] [--company NAME]
    linkedin-esg process <csv_path> [--out DIR]
"""
import argparse
import sys
import logging
from pathlib import Path

from .extract import extract_pipeline
from .io_utils import load_csv, save_csv
from .quality_gate import quality_gate_and_normalize

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


def cmd_extract(args):
    """Extract posts from HTML files."""
    result = extract_pipeline(
        input_path=args.input_path,
        output_dir=args.out,
        exclude_hiring=args.hiring_filter,
        company_override=args.company,
    )
    print(f"RAW    : {result['raw_path']}")
    print(f"CLEAN  : {result['clean_path']}")
    print(f"POSTS  : {result['total_posts']}")
    print(f"COMPANY: {', '.join(result['companies'])}")


def cmd_process(args):
    """Apply quality gate to a clean CSV."""
    df = load_csv(args.csv_path)
    processed = quality_gate_and_normalize(df)
    out_path = args.out or Path(str(args.csv_path).replace("_offline_clean.csv", "_processed.csv"))
    save_csv(processed, out_path)
    print(f"PROCESSED: {out_path}")
    print(f"ROWS     : {len(processed)}")


def main():
    parser = argparse.ArgumentParser(
        description="LinkedIn ESG Sentiment Analysis Pipeline",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Extract command
    p_extract = subparsers.add_parser("extract", help="Extract posts from HTML files")
    p_extract.add_argument("input_path", help="HTML file or directory containing HTML files")
    p_extract.add_argument("--out", default="data", help="Output directory (default: data)")
    p_extract.add_argument(
        "--hiring-filter", action="store_true", default=True,
        help="Exclude hiring posts (default: True)",
    )
    p_extract.add_argument(
        "--no-hiring-filter", action="store_false", dest="hiring_filter",
        help="Do NOT exclude hiring posts",
    )
    p_extract.add_argument("--company", help="Override company name for all posts")
    p_extract.set_defaults(func=cmd_extract)

    # Process command
    p_process = subparsers.add_parser("process", help="Apply quality gate to CSV")
    p_process.add_argument("csv_path", help="Path to clean CSV file")
    p_process.add_argument("--out", help="Output path for processed CSV")
    p_process.set_defaults(func=cmd_process)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
