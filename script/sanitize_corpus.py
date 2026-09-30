#!/usr/bin/env python3

import argparse
import hashlib
import json
from pathlib import Path
import sys

import pikepdf

from sanitize_pdf import sanitize_pdf


SANITIZATION_POLICY = [
    "attachments",
    "external_access",
    "javascript",
    "multimedia",
    "page_thumbnails",
    "pdf_collections",
    "private_application_data",
    "web_capture_data",
]


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Sanitize a directory of PDFs and retain the outputs for review."
    )
    parser.add_argument("input_directory", type=Path)
    parser.add_argument("output_directory", type=Path)
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="Succeed and write an empty report when no input PDFs are present.",
    )
    return parser.parse_args(argv)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pdf_page_count(path):
    with pikepdf.open(path, attempt_recovery=False, suppress_warnings=True) as pdf:
        return len(pdf.pages)


def write_report(output_directory, results):
    report = {
        "policy": SANITIZATION_POLICY,
        "files": results,
    }
    report_path = output_directory / "sanitization-report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


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

    pdfs = sorted(
        path
        for path in input_directory.rglob("*")
        if path.is_file() and path.suffix.lower() == ".pdf"
    )
    if not pdfs and not args.allow_empty:
        print(f"No PDFs found in {input_directory}", file=sys.stderr)
        return 2

    failures = 0
    results = []
    for input_path in pdfs:
        relative_path = input_path.relative_to(input_directory)
        output_path = output_directory / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.unlink(missing_ok=True)
        try:
            sanitize_pdf(input_path, output_path)
            results.append(
                {
                    "file": relative_path.as_posix(),
                    "input_bytes": input_path.stat().st_size,
                    "input_sha256": sha256(input_path),
                    "output_bytes": output_path.stat().st_size,
                    "output_sha256": sha256(output_path),
                    "pages": pdf_page_count(output_path),
                    "status": "sanitized",
                }
            )
            print(f"PASS {relative_path}")
        except Exception as exc:
            failures += 1
            output_path.unlink(missing_ok=True)
            results.append(
                {
                    "file": relative_path.as_posix(),
                    "error": f"{type(exc).__name__}: {exc}",
                    "status": "failed",
                }
            )
            print(f"FAIL {relative_path}: {type(exc).__name__}: {exc}", file=sys.stderr)

    output_directory.mkdir(parents=True, exist_ok=True)
    write_report(output_directory, results)
    if not pdfs:
        print(f"No PDFs found in {input_directory}; wrote an empty report")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
