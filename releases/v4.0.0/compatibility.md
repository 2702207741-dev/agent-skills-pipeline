# Compatibility Table: v4.0.0

| Surface | Status | Evidence or requirement |
|---|---|---|
| Python | Supported | Python 3.10 or newer; project scripts use the standard library |
| Linux | Supported | `./our-skills`, Bash installer, and GitHub-hosted Action verification |
| macOS | Supported | `./our-skills`; installer remains dry-run-first |
| Windows | Supported | `our-skills.cmd` and Python entry point |
| Codex | Supported | Marketplace paths, strict doctor checks, and quickstart replay |
| Claude Code | Supported | Platform matrix and marketplace installer mapping |
| Cursor | Supported | Platform matrix and marketplace installer mapping |
| Hermes | Supported | Platform matrix and marketplace installer mapping |
| External GitHub repository | Supported | Root composite Action and verified Python-library consumer fixture |
| GitHub Release | Supported | Tag must match `skills.json`; signed assets attach through the release workflow |

## Public Action Contract

The v4 Action validates a repository-owned registry and emits deterministic
release evidence. Consumers should pin a full commit SHA for production and may
use `v4.0.0` when they intentionally follow the immutable release tag.

## Release Evidence

The retained directory contains artifact, manifest, checksum, SBOM, local
provenance, local-integrity signature, marketplace index, quality dashboard,
skill graph, and model-evaluation sidecars. The GitHub release workflow adds
identity-backed Sigstore and attestation evidence for the tagged commit.

## Known Limits

- Multi-model scoring uses deterministic replay adapters rather than live API
  calls, so release verification needs no provider secrets.
- The external consumer fixture proves interface portability, not independent
  third-party adoption.
- Remote registry federation and transactional dependency resolution remain
  roadmap work.
