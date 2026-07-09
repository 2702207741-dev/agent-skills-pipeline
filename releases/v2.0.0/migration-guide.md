# Migration Guide: v1.5.0 to v2.0.0

## Scope

v2.0.0 is a local platform milestone. It does not require public tags, remote release publishing, or GitHub Release creation. Public publishing is intentionally deferred until v3.0.0.

## Maintainer Actions

1. Treat `skills.json` as the source of truth for skill lifecycle metadata.
2. Regenerate platform reports after registry, graph, benchmark, or platform-matrix changes:

```bash
python scripts/generate_platform_reports.py
```

3. Verify reports are current before committing:

```bash
python scripts/generate_platform_reports.py --check
```

4. Use the marketplace doctor to diagnose platform installs:

```bash
python scripts/marketplace.py doctor --platform codex --target-root <target-root>
```

5. Run the full local platform gate:

```bash
python scripts/verify_release.py
```

## User-Facing Changes

- `marketplace.py list` now reads the local marketplace index and shows status plus quality score.
- `marketplace.py doctor` diagnoses source metadata, dependencies, platform paths, trigger metadata, and installed versions.
- `reports/quality-dashboard.md` gives maintainers a quick skill health view.
- `reports/skill-graph-report.md` gives maintainers a visual dependency graph and stage coverage view.

## Deprecation Workflow

Deprecated skills must set:

- `status: deprecated`
- `deprecated: true`
- `replaced_by`: replacement skill name, or `null` only when there is no replacement
- `migration_path`: a concrete user migration note

Active skills must keep `deprecated: false`, `replaced_by: null`, and `migration_path: null`.

## Verification

Migration is complete when `verify_release.py` passes, platform reports are current, marketplace doctor passes in strict mode after install, and release generation emits all v2 platform report sidecars.
