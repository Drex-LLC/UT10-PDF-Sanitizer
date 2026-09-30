#!/usr/bin/env python3

import argparse
import os
import sys

import pikepdf

MINIMUM_PIKEPDF_VERSION = (10, 15)


def build_sanitizer():
    installed_version = tuple(int(part) for part in pikepdf.__version__.split(".")[:2])
    if installed_version < MINIMUM_PIKEPDF_VERSION:
        raise RuntimeError("pikepdf 10.15 or newer is required")

    return (
        pikepdf.sanitize.Sanitizer()
        .remove_javascript()
        .remove_external_access()
        .remove_attachments()
        .remove_multimedia()
        .remove_thumbnails()
        .remove_private_app_data()
        .remove_collection()
        .remove_web_capture()
    )


def sanitize_pdf(input_path, output_path):
    if os.path.realpath(input_path) == os.path.realpath(output_path):
        raise ValueError("input and output paths must be different")

    with pikepdf.open(
        input_path,
        attempt_recovery=False,
        suppress_warnings=True,
    ) as pdf:
        page_count = len(pdf.pages)
        build_sanitizer().apply(pdf)
        pdf.save(
            output_path,
            compress_streams=True,
            object_stream_mode=pikepdf.ObjectStreamMode.generate,
            recompress_flate=True,
        )

    with pikepdf.open(
        output_path,
        attempt_recovery=False,
        suppress_warnings=True,
    ) as verified_pdf:
        if len(verified_pdf.pages) != page_count:
            raise ValueError("sanitization changed the page count")


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Remove active and auxiliary content from a PDF."
    )
    parser.add_argument("input_pdf")
    parser.add_argument("output_pdf")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    try:
        sanitize_pdf(args.input_pdf, args.output_pdf)
        return 0

    except Exception as exc:
        message = str(exc).replace("\n", " ")[:1000]
        print(
            f"PDF sanitization failed: {type(exc).__name__}: {message}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
