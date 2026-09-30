# Discourse PDF Sanitizer

This Discourse plugin sanitizes every `.pdf` attachment before Discourse stores it. It is disabled by default and fails closed: if the sanitizer is unavailable, times out, or cannot parse a PDF, the upload is rejected and the original file is not stored.

## What it removes

The sanitizer uses pikepdf's maintained sanitization API to remove:

- JavaScript actions
- actions that access the network or filesystem, including ordinary external links
- embedded files and PDF portfolio behavior
- sound, video, Flash, and 3D content
- page thumbnails, embedded search indexes, private application data, and web-capture data

Standard page content, document metadata, annotations, and AcroForm/XFA form data remain. Sanitization rewrites the file and invalidates existing digital signatures. See [SECURITY.md](SECURITY.md) for the exact threat model and limitations.

## Deployment

Requirements:

- a supported Discourse installation
- Python 3.11 or newer
- enough local temporary space for the input and rewritten PDF

Install the Python dependency into the plugin-local virtual environment:

```sh
cd /var/www/discourse/plugins/discourse-pdf-sanitizer
python3 -m venv .venv
.venv/bin/python -m pip install --disable-pip-version-check --no-cache-dir -r requirements.txt
script/verify
```

For a standard Docker deployment, the hosting provider should run the virtual-environment creation and dependency installation during every container rebuild. If the environment must live elsewhere, set `DISCOURSE_PDF_SANITIZER_PYTHON` to the Python executable's absolute path for the web and Sidekiq processes.

Before enabling the plugin:

1. Add `pdf` to Discourse's `authorized_extensions` site setting.
2. Run `script/verify` as the same operating-system user that runs Discourse.
3. Restart the web and Sidekiq processes.
4. Enable `discourse_pdf_sanitizer_enabled` in the admin site settings.
5. Upload a benign PDF and confirm that it can be downloaded and opened.

`discourse_pdf_sanitizer_timeout_seconds` controls the per-file wall-clock timeout. Direct S3 PDFs at or above Discourse's 100 MB local-download boundary are rejected because they cannot pass through the local sanitizer.

## Testing

Run the dependency and generated-fixture suite:

```sh
script/verify
```

Run the Discourse-side specs from the Discourse root:

```sh
bin/rspec plugins/discourse-pdf-sanitizer/spec
```

To test real PDFs, place files expected to succeed in `spec/fixtures/pdf_corpus/accepted/` and files expected to be rejected in `spec/fixtures/pdf_corpus/rejected/`. PDFs in those directories are intentionally gitignored so private samples are not committed accidentally. Then run `script/verify` again.

To retain sanitized copies for visual comparison:

```sh
.venv/bin/python script/sanitize_corpus.py \
  spec/fixtures/pdf_corpus/accepted \
  spec/fixtures/pdf_corpus/output
```

Compare the originals and outputs visually, verify text search and form behavior that your community relies on, and scan the outputs with the malware scanner used by your hosting provider.

## Operations

Failures are returned to uploaders as a generic rejection and logged with the prefix `[discourse-pdf-sanitizer]`. Do not enable Discourse's upload debug mode in production merely to troubleshoot this plugin; use the Rails logs instead.

The plugin does not provide a public controller or route. It runs synchronously in the existing Discourse upload pipeline so an unsanitized file is never committed to the upload store.
