# our-skills v4.0.0

v4.0.0 is the external-adoption release of Agent Skills Pipeline. It turns the
repository from a governed first-party skill system into reusable OSS
maintenance infrastructure that another repository can run without copying
project-internal scripts.

## Highlights

- A cross-platform `our-skills` command provides quickstart, doctor, verify,
  marketplace, replay, and maintenance-demo workflows.
- A five-minute isolated quickstart installs one skill, runs strict diagnostics,
  replays hash-bound evidence, and leaves the user's normal agent home untouched.
- The root composite GitHub Action validates a repository-owned `skills.json`,
  rejects unsafe or inconsistent inputs, and emits a deterministic artifact,
  manifest, checksum, and machine-readable gate report.
- A clean external Python-library fixture exercises the public Action contract,
  including path traversal, tampered metadata, and deterministic-build cases.
- An executable issue-to-PR-review-to-release-gate demo records the complete
  maintainer path and checks its output against a committed regression oracle.
- The ecosystem roadmap defines repository conformance, signed registry
  exchange, transactional installation, evidence portability, and governance.

## Trust and Evidence

- 14 active first-party skills, with registry and frontmatter versions checked.
- 42 skill-level RigorBench traces covering success, failure, and boundary cases.
- 12 Codex maintenance records covering PR review, issue triage, release, and
  security or code-quality audit workflows.
- GitHub OIDC keyless signing through Cosign, SLSA-style provenance, SBOM,
  checksums, and GitHub artifact attestation in the release workflow.
- CodeQL, OpenSSF Scorecard, Dependabot, secret-scanning configuration, custom
  dangerous-command policy, and redaction regressions.

## Verify

From a fresh clone:

```bash
./our-skills verify
./our-skills doctor
./our-skills demo --check
```

Windows users can run the same commands through `our-skills.cmd`.

## Compatibility and Migration

No first-party skill was removed or renamed. The official skill count remains
14, and existing installer destinations remain supported. See
`migration-guide.md` and `compatibility.md` in this directory for the public
interface and platform details.

## Release Assets

The retained archive contains:

- `our-skills-v4.0.0.zip`
- `our-skills-v4.0.0.manifest.json`
- `our-skills-v4.0.0.sha256`
- `our-skills-v4.0.0.sbom.json`
- `our-skills-v4.0.0.provenance.json`
- `our-skills-v4.0.0.sig`
- marketplace, quality-dashboard, skill-graph, and model-eval report sidecars

The GitHub `Supply Chain` workflow additionally publishes a
`our-skills-v4.0.0.sigstore.json` identity bundle, SLSA provenance, and a GitHub
artifact attestation for the tagged source commit.
