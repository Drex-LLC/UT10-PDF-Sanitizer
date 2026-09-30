import importlib.util
from pathlib import Path
import tempfile
import unittest

import pikepdf


PLUGIN_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = PLUGIN_ROOT / "script" / "sanitize_pdf.py"
SPEC = importlib.util.spec_from_file_location("sanitize_pdf", MODULE_PATH)
SANITIZE_MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SANITIZE_MODULE)


class SanitizePdfTest(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.directory = Path(self.temporary_directory.name)

    def create_pdf(self, path, active=False, pages=1):
        pdf = pikepdf.Pdf.new()
        for _page_number in range(pages):
            pdf.add_blank_page(page_size=(200, 200))

        if active:
            attachment_path = path.with_suffix(".txt")
            attachment_path.write_text("embedded test payload")
            pdf.attachments["payload.txt"] = pikepdf.AttachedFileSpec.from_filepath(
                pdf, attachment_path
            )
            pdf.Root.OpenAction = pikepdf.Dictionary(
                S=pikepdf.Name.JavaScript,
                JS="app.alert('test')",
            )
            pdf.Root.AA = pikepdf.Dictionary(
                WC=pikepdf.Dictionary(
                    S=pikepdf.Name.URI,
                    URI="https://example.invalid/",
                )
            )
            pdf.Root.Collection = pikepdf.Dictionary(Type=pikepdf.Name.Collection)
            pdf.Root.PieceInfo = pikepdf.Dictionary(Test=pikepdf.Dictionary())
            pdf.pages[0].obj.Thumb = pdf.make_stream(b"not-an-image")
            rich_media = pdf.make_indirect(
                pikepdf.Dictionary(
                    Type=pikepdf.Name.Annot,
                    Subtype=pikepdf.Name.RichMedia,
                    Rect=pikepdf.Array([0, 0, 10, 10]),
                    RichMediaContent=pikepdf.Dictionary(),
                )
            )
            pdf.pages[0].obj.Annots = pikepdf.Array([rich_media])

        pdf.save(path)

    def test_removes_active_and_auxiliary_content(self):
        input_path = self.directory / "active.pdf"
        output_path = self.directory / "sanitized.pdf"
        self.create_pdf(input_path, active=True)

        SANITIZE_MODULE.sanitize_pdf(input_path, output_path)

        with pikepdf.open(output_path, attempt_recovery=False) as pdf:
            self.assertNotIn("/OpenAction", pdf.Root)
            self.assertNotIn("/AA", pdf.Root)
            self.assertNotIn("/Collection", pdf.Root)
            self.assertNotIn("/PieceInfo", pdf.Root)
            self.assertNotIn("/Thumb", pdf.pages[0].obj)
            self.assertEqual([], list(pdf.attachments.keys()))
            self.assertNotIn("/RichMediaContent", pdf.pages[0].obj.Annots[0])

    def test_preserves_page_count(self):
        input_path = self.directory / "clean.pdf"
        output_path = self.directory / "sanitized.pdf"
        self.create_pdf(input_path, pages=3)

        SANITIZE_MODULE.sanitize_pdf(input_path, output_path)

        with pikepdf.open(output_path, attempt_recovery=False) as pdf:
            self.assertEqual(3, len(pdf.pages))

    def test_rejects_malformed_input(self):
        input_path = self.directory / "malformed.pdf"
        output_path = self.directory / "sanitized.pdf"
        input_path.write_bytes(b"%PDF-1.7\nnot really a PDF")

        with self.assertRaises(pikepdf.PdfError):
            SANITIZE_MODULE.sanitize_pdf(input_path, output_path)

    def test_rejects_encrypted_input(self):
        input_path = self.directory / "encrypted.pdf"
        output_path = self.directory / "sanitized.pdf"
        pdf = pikepdf.Pdf.new()
        pdf.add_blank_page(page_size=(200, 200))
        pdf.save(input_path, encryption=pikepdf.Encryption(user="secret", owner="owner"))

        with self.assertRaises(pikepdf.PasswordError):
            SANITIZE_MODULE.sanitize_pdf(input_path, output_path)


class PrivateCorpusTest(unittest.TestCase):
    def test_rejected_private_corpus(self):
        corpus_root = PLUGIN_ROOT / "spec" / "fixtures" / "pdf_corpus"
        rejected = sorted(
            path
            for path in (corpus_root / "rejected").rglob("*")
            if path.is_file() and path.suffix.lower() == ".pdf"
        )

        with tempfile.TemporaryDirectory() as output_directory:
            for input_path in rejected:
                with self.subTest(expected="rejected", pdf=input_path.name):
                    output_path = Path(output_directory) / input_path.name
                    with self.assertRaises(Exception):
                        SANITIZE_MODULE.sanitize_pdf(input_path, output_path)


if __name__ == "__main__":
    unittest.main()
