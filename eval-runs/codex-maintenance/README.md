# Codex Maintenance Evidence

This directory keeps reconstructed repository-history evidence separate from
redacted evidence captured during actual agent sessions.

`traces.json` contains twelve Git-pinned reconstructions across four maintainer
workflows:

- three PR-style change-set reviews;
- three CI issue-triage records;
- three release workflow gates; and
- three security or code-quality audits.

Each record includes the task, input prompt, skills used, agent behavior, files
read, fixed safe commands, recorded output excerpts, final output, maintainer
conclusion, and adoption status. Every referenced file is pinned to a Git blob
at an actual reachable commit. The checker confirms that the commit and blobs
remain available, then replays only a small allowlisted command set.

These repository changes were reconstructed from commits and commands. The
records deliberately use `commit_derived_reconstruction`; they do not invent PR
numbers, prompts, or verbatim session transcripts. Adoption is demonstrated by
a reachable main-history commit, release tag, or passing repository gate.

`live-traces.json` is the schema v2 observed-session channel. It begins with zero
records rather than relabeling reconstruction as live execution. Each accepted
record must retain the redacted maintainer request, redacted transcript digest,
agent and model identity, before/after commits, Git blobs, allowlisted command
output hashes, final output, and a human conclusion. Coverage is a 4-by-3 matrix:
PR review, issue triage, release workflow, and security audit, each with success,
failure, and boundary evidence.

Run the standalone evidence gate:

```bash
python scripts/check_maintenance_evidence.py
```

Validate only structure and provenance without rerunning commands:

```bash
python scripts/check_maintenance_evidence.py --no-replay
```

Validate the observed-session channel without requiring all twelve cells yet:

```bash
python scripts/check_live_maintenance_evidence.py --no-replay
```

Enforce the completed v4.1 acceptance gate:

```bash
python scripts/check_live_maintenance_evidence.py --require-coverage
```

Capture one already-redacted session draft safely; writes require `--apply`:

```bash
python scripts/capture_maintenance_evidence.py \
  --record path/to/record.json \
  --transcript path/to/redacted-transcript.txt
```

`python scripts/run_rigorbench.py` replays both channels. Reconstruction remains
a required baseline. Observed records are validated and reported independently;
the explicit `--require-coverage` gate prevents incomplete live evidence from
being presented as complete.
