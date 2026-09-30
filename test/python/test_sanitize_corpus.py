import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import pikepdf


PLUGIN_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = PLUGIN_ROOT / "script" / "sanitize_corpus.py"


class SanitizeCorpusTest(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.before_directory = Path(self.temporary_directory.name) / "before"
        self.after_directory = Path(self.temporary_directory.name) / "after"
        self.before_directory.mkdir()
        self.after_directory.mkdir()

    def test_overwrites_output_and_records_before_after_evidence(self):
        input_path = self.before_directory / "sample.PDF"
        output_path = self.after_directory / "sample.PDF"
        pdf = pikepdf.Pdf.new()
        pdf.add_blank_page(page_size=(200, 200))
        pdf.save(input_path)
        output_path.write_bytes(b"stale output")

        result = subprocess.run(
            [sys.executable, SCRIPT_PATH, self.before_directory, self.after_directory],
            capture_output=True,
            check=False,
            text=True,
        )

        self.assertEqual(0, result.returncode, result.stderr)
        with pikepdf.open(output_path, attempt_recovery=False) as sanitized_pdf:
            self.assertEqual(1, len(sanitized_pdf.pages))

        report = json.loads(
            (self.after_directory / "sanitization-report.json").read_text()
        )
        self.assertEqual("sanitized", report["files"][0]["status"])
        self.assertEqual("sample.PDF", report["files"][0]["file"])
        self.assertEqual(
            hashlib.sha256(input_path.read_bytes()).hexdigest(),
            report["files"][0]["input_sha256"],
        )
        self.assertEqual(
            hashlib.sha256(output_path.read_bytes()).hexdigest(),
            report["files"][0]["output_sha256"],
        )
        self.assertIn("javascript", report["policy"])


if __name__ == "__main__":
    unittest.main()
