# Compatibility Table: v3.0.0

| Surface | Status | Notes |
|---|---|---|
| Hermes Agent | Supported | Marketplace index includes category-aware install paths |
| Claude Code | Supported | Third-party spec keeps frontmatter portable |
| Codex | Supported | Doctor verifies installed versions and trigger metadata |
| Cursor Skills | Supported | Docs distinguish skills from always-loaded rules |
| Third-party skills | Proposed/active/deprecated lifecycle | Intake schema, review checklist, CLA, and security gates required |
| Multi-model evaluation | Replay-supported | Codex, Claude, Gemini, and local model rows are evaluated through deterministic replay |
| GitHub Release | Published by maintainer request | Tag and release assets are expected to point at the verified v3.0.0 source tree |

## Public Entry Points

- `docs/index.html`
- `docs/third-party-skill-spec.md`
- `examples/task-library.json`
- `examples/replay-dataset.json`
- `reports/model-eval-report.md`
- `reports/quality-dashboard.md`
- `reports/skill-graph-report.md`
- `releases/v3.0.0/RELEASE_NOTES.md`

## Release Sidecars

v3.0.0 release generation emits the v2 platform sidecars plus:

- `our-skills-v3.0.0.model-eval-report.json`
