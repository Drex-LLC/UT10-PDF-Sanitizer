#!/usr/bin/env python3

import sys
import pikepdf

def main():
    if len(sys.argv) != 3:
        print("Usage: sanitize_pdf.py <input_pdf> <output_pdf>",
        file=sys.stferr,
        )
        return 2
    input_path = sys.argv[1]
    output_path = sys.argv[2]

    try:
        with pikepdf.open(input_path) as pdf:
            pikepdf.sanitize.remove_javascript(pdf)
            pdf.save(output_path)
        with pikepdf.open(output_path) as pdf:
            _ = len(pdf.pages)
        return 0
    
    except Exception as exc:
        print(f"PDF sanitization failed: {type(exc).__name__}: {exc}", file=sys.stderr,)
        return 1

if __name__ == "__main__":
    sys.exit(main())
