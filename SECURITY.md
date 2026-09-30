# Security policy and threat model

## Security boundary

PDFs are parsed in a separate Python process with:

- no shell interpolation
- Python isolated mode (`-I`)
- a wall-clock timeout and CPU limit
- an output-size limit matching Discourse's attachment limit
- temporary files created with operating-system restricted permissions

The upload hook is fail-closed. A parser error, missing dependency, timeout, abnormal process exit, empty output, or invalid output header rejects the upload. Direct S3 PDFs too large for Discourse to download locally are also rejected.

## Content policy

The plugin removes the active and auxiliary PDF features listed in the README. It intentionally preserves page content, metadata, forms, and most annotations to avoid silently destroying legitimate documents. External hyperlinks are removed as part of the no-network policy.

This is not a content-disarm-and-reconstruction system, malware scanner, redaction tool, or guarantee that a PDF parser has no vulnerabilities. PDF sanitization should be one layer in a defense-in-depth design. Managed deployments should also:

- serve uploads from a separate origin with restrictive response headers
- keep pikepdf, qpdf, Python, and Discourse patched
- scan uploads with the host's malware detection service
- enforce conservative upload-size and request-rate limits
- rasterize and rebuild PDFs when the requirement is “only visible page pixels may survive”

Encrypted PDFs are rejected because the service has no password with which to inspect them. Sanitization rewrites the PDF and invalidates existing digital signatures. Sanitization is not redaction: hidden or off-page page content may remain.

## Dependency updates

`requirements.txt` pins the complete Python dependency set deliberately. Review pikepdf and bundled qpdf release notes, run both test suites and the private PDF corpus, and visually compare representative output before changing the pins.

## Reporting a vulnerability

Report suspected vulnerabilities privately to the repository owner or hosting provider. Do not attach a live malicious PDF to a public issue. Include the Discourse revision, plugin revision, Python version, pikepdf version, and a minimal reproduction when it is safe to share one.
