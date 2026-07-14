# Roadmap to an Agent Skill Ecosystem

## Position

`our-skills` is moving from a maintained first-party collection to an
infrastructure layer for repositories that want agent behavior governed like
software. The intended ecosystem is not a central prompt dump. It is a set of
portable contracts for discovery, quality evidence, distribution, policy,
installation, lifecycle, and trust.

The v4.0.0 release proves the first external-adoption boundary:

- another repository owns its registry and skill files;
- a pinned GitHub Action validates and packages them;
- the same gate runs locally through one CLI;
- artifacts are deterministic, inspectable, and ready for identity attestation;
- an end-to-end maintenance scenario reaches a release decision with replayable
  evidence.

## Ecosystem Layers

| Layer | Current contract | Ecosystem direction |
|---|---|---|
| Authoring | `SKILL.md` frontmatter and behavioral sections | Versioned portable skill schema and compatibility profiles |
| Registry | Repository-owned `skills.json` | Federated indexes with signed snapshots and namespace ownership |
| Quality | Static validation, fixtures, replay, maintenance evidence | Pluggable evaluators with comparable evidence envelopes |
| Security | Policy regressions, CodeQL, Scorecard, secret scanning | Shared policy packs, trust roots, revocation, and transparency feeds |
| Distribution | Deterministic archive, manifest, checksum, SBOM, provenance | Sigstore-attested registry objects and content-addressed mirrors |
| Installation | Hashed plans, staged transactions, doctor, transaction rollback, hash-chained audit | Resolver API with dependency constraints and portable transactions |
| Lifecycle | Owner, status, deprecation, replacement, migration | Cross-registry advisories and automated migration proposals |
| Adoption | External fixture and reusable Action | Verified adopter catalog and conformance badges |

## Federation Model

Each repository remains authoritative for its source and release policy. A
future federated registry should ingest only signed, schema-valid snapshots and
index content by digest. Federation must not let the central service silently
rewrite a maintainer's artifact or ownership metadata.

A registry record should minimally bind:

- namespace, name, version, owner, and source repository;
- content digest and immutable artifact location;
- schema and platform compatibility versions;
- dependency constraints and lifecycle state;
- quality, security, replay, and maintainer evidence digests;
- builder, signer, provenance, revocation, and advisory references.

## Adoption Phases

### Phase 1: Repository Conformance

- Stabilize the external `skills.json` schema.
- Publish immutable Action releases and a compatibility policy.
- Keep Python, JavaScript, and documentation-only consumer fixtures green.
- Keep conformance tests green on GitHub-hosted Linux, Windows, and macOS runners.

**Exit:** three unrelated repositories can adopt the gate without copying
project-internal scripts.

### Phase 2: Signed Registry Exchange

- Define a signed registry snapshot and content-addressed artifact API.
- Verify Sigstore identity, SLSA provenance, schema, policy, and revocation at
  ingestion time.
- Add read-only remote discovery to `our-skills list` and `doctor`.

**Exit:** a consumer can discover and verify a remote skill without trusting the
registry transport.

### Phase 3: Transactional Marketplace

- Keep resolving dependencies and compatibility constraints before writing.
- Extend the implemented hashed plan and staged transaction model to remote
  packages.
- Make rollback and audit records portable across machines.
- Publish security advisories and deprecation migrations.

**Exit:** install, update, and rollback remain recoverable across a dependency
graph and a failed operation.

### Phase 4: Evidence Network

- Standardize replay and maintainer-workflow evidence envelopes.
- Accept evaluator plugins while retaining raw provenance and scoring policy.
- Compare trigger precision, behavioral regressions, security posture, and
  external adoption without collapsing them into one opaque score.

**Exit:** maintainers can explain why a skill is trusted, what changed, and
which repositories have independently exercised it.

## Governance

- Schema, policy, and protocol changes use public proposals and compatibility
  windows.
- Namespace ownership and transfer are auditable.
- Revocation never deletes historical evidence; it marks trust state and reason.
- Scores expose their inputs and cannot replace maintainer judgment.
- Adopters are listed only with verifiable repository evidence and consent.
- The registry service is replaceable; source repositories and content digests
  remain the durable trust anchors.

## Near-Term Work

1. Capture 12 redacted observed Codex maintenance sessions across the four
   workflow families and three outcome classes.
2. Run the composite Action in consented real third-party OSS pull requests.
3. Publish a versioned external registry JSON Schema and compatibility policy.
4. Add optional GitHub OIDC attestation for consumer-built release bundles.
5. Define signed remote index snapshots and a read-only discovery prototype.

## Codex for OSS Narrative

The project does not merely use Codex to edit files. It turns Codex-relevant
maintenance behavior into reviewable contracts, preserves observed and
reconstructed maintenance evidence as distinct classes, and gives other OSS
repositories a low-cost quality and release gate.
The infrastructure claim is therefore testable: clone, run the quickstart,
execute the maintenance demo, or consume the pinned Action from another
repository and inspect the resulting evidence.
