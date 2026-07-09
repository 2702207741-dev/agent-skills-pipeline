# Compatibility Table: v2.0.0

| Surface | Status | Install Path | Doctor Coverage |
|---|---|---|---|
| Hermes Agent | Supported | `~/.hermes/skills/<category>/<name>/SKILL.md` | Source metadata, category path, dependencies |
| Claude Code | Supported | `~/.claude/skills/<name>/SKILL.md` | Source metadata, path shape, dependencies |
| Codex | Supported | `~/.codex/skills/<name>/SKILL.md` | Source metadata, installed version, dependencies |
| Cursor Skills | Supported | `~/.cursor/skills/<name>/SKILL.md` | Source metadata, path shape, dependencies |
| Cursor Rules | Limited | `~/.cursor/rules/<name>.md` | Documented as limited; large skills should stay in Cursor Skills |

## Platform Artifacts

| Artifact | Purpose |
|---|---|
| `marketplace/index.json` | Local marketplace index for list/install/update/rollback/doctor workflows |
| `reports/quality-dashboard.json` | Machine-readable quality and risk dashboard |
| `reports/quality-dashboard.md` | Maintainer-readable quality dashboard |
| `reports/skill-graph-report.json` | Machine-readable graph, island, cycle, and stage coverage report |
| `reports/skill-graph-report.md` | Maintainer-readable visual graph report |

## Release Sidecars

`scripts/create_release.py` emits these v2 platform sidecars in addition to the v1.5 trusted-distribution files:

- `our-skills-v2.0.0.marketplace-index.json`
- `our-skills-v2.0.0.quality-dashboard.json`
- `our-skills-v2.0.0.skill-graph-report.json`

`scripts/verify_release.py` verifies that these sidecars enumerate every registered skill, show no isolated graph nodes, show no hard dependency cycles, and show no missing stage coverage.
