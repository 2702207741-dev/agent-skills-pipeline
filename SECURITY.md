# Security Policy

## Reporting

Report suspected vulnerabilities privately to the repository maintainer before opening a public issue. If GitHub private vulnerability reporting is enabled, use that channel first. Include the affected skill, script, platform, and reproduction details.

## Security Gates

Every contribution must pass:

- `python scripts/security_scan.py`
- `python scripts/review_bot.py --all --check`
- `python scripts/marketplace.py doctor --platform codex --target-root <tmp> --strict`

## Prohibited Content

- Live credentials, API keys, passwords, tokens, or private keys
- Unreviewed destructive shell commands
- Hidden external network dispatch
- Regulated data in examples, fixtures, replay traces, screenshots, or reports

## External Model Dispatch

External model evaluation must use redaction gates and must not send private repository context unless the data classification allows it and the user approves.
