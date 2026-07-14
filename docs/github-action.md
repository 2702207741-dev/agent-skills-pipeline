# Reusable GitHub Action

The repository root is a composite GitHub Action that validates agent skills in
another repository and optionally produces a deterministic release bundle. It
uses only Python's standard library and pinned GitHub-maintained Actions.

## Minimal Consumer Workflow

```yaml
name: Agent skill gate

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  skills:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<FULL_COMMIT_SHA>
        with:
          persist-credentials: false
      - uses: 2702207741-dev/agent-skills-pipeline@<FULL_COMMIT_SHA>
        with:
          mode: all
```

Replace both placeholders with reviewed immutable commits. Verified Python,
JavaScript, and documentation fixtures live in `examples/external-repos/` and
run across Ubuntu, Windows, and macOS.

## Consumer Registry

The machine-readable contract is
[`schemas/external-skills.schema.json`](../schemas/external-skills.schema.json).

```json
{
  "schema_version": 1,
  "project": "my-project-skills",
  "version": "1.0.0",
  "skills": [
    {
      "name": "my-review-workflow",
      "path": "skills/my-review-workflow",
      "version": "1.0.0"
    }
  ]
}
```

Every `SKILL.md` must synchronize `name` and `version`, include a 20-1024
character description, and contain `When to Use` and `Verification Checklist`
sections. The gate rejects traversal, symlinks, oversized files, secret-like
material, and unmarked dangerous-command examples.

`schema_version` defaults to `1` when omitted for compatibility. Any explicit
value other than `1` fails until a new version is documented and implemented.

## Inputs

| Input | Default | Purpose |
|---|---|---|
| `workspace` | `.` | Repository-relative directory containing the registry. |
| `registry` | `skills.json` | Registry path within the workspace. |
| `mode` | `all` | `quality`, `release`, or both. |
| `output-directory` | `.our-skills-dist` | Verified release output directory. |
| `upload-artifact` | `true` | Upload release evidence when release mode runs. |
| `artifact-name` | `our-skills-release` | Workflow artifact display name. |

## Outputs

- `interface-version` (`1` for this additive Action contract)
- `status` and `skill-count`
- `report-path`
- `artifact-path`
- `manifest-path`
- `checksum-path`

Release mode builds a reproducible zip with fixed timestamps, records every
entry digest in the manifest, writes a SHA-256 sidecar, and reopens the archive
to verify names and hashes before success. A consumer may feed the resulting zip
into its own OIDC attestation or signing job.

The metadata follows GitHub's composite Action contract documented at
<https://docs.github.com/en/actions/reference/workflows-and-actions/metadata-syntax>.
