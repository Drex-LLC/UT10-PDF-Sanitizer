# Private PDF corpus

Place real-world PDFs in one of these gitignored directories:

- `accepted/`: valid PDFs that must sanitize successfully
- `rejected/`: malformed or encrypted PDFs that must fail sanitization

Run `script/verify` after adding files. Do not commit confidential, licensed, or live malicious samples. Store such samples in your organization's approved restricted malware repository and copy them here only in an isolated test environment.
