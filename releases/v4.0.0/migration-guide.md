# Migration Guide: v3.0.0 to v4.0.0

v4.0.0 adds public adoption interfaces around the existing governed skill
system. It does not remove or rename any of the 14 first-party skills.

## Maintainer Upgrade

1. Pull the v4.0.0 source and run `./our-skills verify`.
2. Use `./our-skills doctor` as the normal repository health entry point.
3. Keep installation in dry-run mode until the displayed diff is reviewed;
   add `--apply` only when the target is correct.
4. Use `./our-skills demo --check` to exercise the issue-to-release workflow.
5. Verify downloaded release assets with the checksum, Sigstore bundle, SLSA
   provenance, and GitHub attestation described in `docs/slsa-provenance.md`.

## External Repository Adoption

Pin the reusable Action to an immutable full commit SHA or the v4.0.0 tag after
reviewing the release:

```yaml
- uses: 2702207741-dev/agent-skills-pipeline@v4.0.0
  with:
    mode: all
```

Production consumers should prefer a full commit SHA. The Action reads the
consumer repository's registry and skill files, not this repository's internal
registry. Its output contract is documented in `docs/github-action.md`.

## Compatibility Notes

- Project version advances from 3.0.0 to 4.0.0.
- Individual skill versions remain unchanged because their behavioral contracts
  did not receive breaking changes in this milestone.
- `skills.json` remains the source of truth for project and skill versions.
- Historical v3.0.0 files remain immutable and installable for rollback.
- The legacy `.sig` sidecar remains a local integrity check; identity assurance
  comes from the release workflow's Sigstore bundle and GitHub attestation.

## Rollback

Repository users can return to the v3.0.0 tag or retained v3.0.0 archive.
Installed skills can be rolled back through `./our-skills rollback ... --apply`;
the marketplace audit log records install, update, and rollback operations.
