#!/usr/bin/env python3

import argparse
from pathlib import Path
import sys

from sanitize_pdf import sanitize_pdf


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Sanitize a directory of PDFs and retain the outputs for review."
    )
    parser.add_argument("input_directory", type=Path)
    parser.add_argument("output_directory", type=Path)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    input_directory = args.input_directory.resolve()
    output_directory = args.output_directory.resolve()

    if not input_directory.is_dir():
        print(f"Input directory does not exist: {input_directory}", file=sys.stderr)
        return 2
    if input_directory == output_directory:
        print("Input and output directories must be different", file=sys.stderr)
        return 2

    pdfs = sorted(path for path in input_directory.rglob("*.pdf") if path.is_file())
    if not pdfs:
        print(f"No PDFs found in {input_directory}", file=sys.stderr)
        return 2

    failures = 0
    for input_path in pdfs:
        relative_path = input_path.relative_to(input_directory)
        output_path = output_directory / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            sanitize_pdf(input_path, output_path)
            print(f"PASS {relative_path}")
        except Exception as exc:
            failures += 1
            output_path.unlink(missing_ok=True)
            print(f"FAIL {relative_path}: {type(exc).__name__}: {exc}", file=sys.stderr)

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
