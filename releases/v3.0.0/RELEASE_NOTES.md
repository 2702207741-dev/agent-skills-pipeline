# our-skills v3.0.0

v3.0.0 is the ecosystem-ready release of Agent Skills Pipeline.

It packages 14 first-party agent skills with replayable evidence, security
gates, release provenance, marketplace installation, rollback, and contributor
automation.

## Highlights

- 14 active skills for skill engineering plus general maintainer workflows:
  code review, debugging, test design, requirements clarification, planning,
  observability, incident retros, git workflow, security, verification, and
  configuration.
- 42 replayable RigorBench traces covering success, failure, and boundary cases
  for every skill.
- One-command release verification through `python scripts/verify_release.py`.
- Dry-run-first marketplace installer with install, update, rollback, doctor,
  diff preview, and audit logs.
- Release artifact with manifest, checksum, SBOM, provenance, signature,
  marketplace index, quality dashboard, skill graph report, and model-eval
  sidecars.
- Public ecosystem entry points: docs site, example task library, replay
  dataset, third-party skill spec, review bot, issue templates, PR template,
  CLA, security policy, and contribution guide.

## Verification

```bash
python scripts/verify_release.py
```

The verification gate covers registry, format, fixtures, security, RigorBench,
graph, platform reports, example datasets, model evaluation, ecosystem assets,
release archive, publication readiness, packaging, marketplace installation,
update, rollback, and review-bot checks.

## Release Assets

The retained release directory includes:

- `our-skills-v3.0.0.zip`
- `our-skills-v3.0.0.manifest.json`
- `our-skills-v3.0.0.sha256`
- `our-skills-v3.0.0.sbom.json`
- `our-skills-v3.0.0.provenance.json`
- `our-skills-v3.0.0.sig`
- `our-skills-v3.0.0.marketplace-index.json`
- `our-skills-v3.0.0.quality-dashboard.json`
- `our-skills-v3.0.0.skill-graph-report.json`
- `our-skills-v3.0.0.model-eval-report.json`

## Known Boundaries

- Multi-model evaluation is deterministic replay, not live API scoring.
- The release signature is a SHA-256 signature over canonical provenance, not
  yet a Sigstore or hardware-backed identity.
- The marketplace is local-first; remote registry federation is future work.
