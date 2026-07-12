# Codex Maintenance Evidence

This directory stores replayable evidence that Codex is used for maintenance work
in this repository, not only for static skill contracts.

`traces.json` contains twelve records across four real maintainer workflows:

- three PR-style change-set reviews;
- three CI issue-triage records;
- three release workflow gates; and
- three security or code-quality audits.

Each record includes the task, input prompt, skills used, agent behavior, files
read, fixed safe commands, recorded output excerpts, final output, maintainer
conclusion, and adoption status. Every referenced file is pinned to a Git blob
at an actual reachable commit. The checker confirms that the commit and blobs
remain available, then replays only a small allowlisted command set.

Some older repository changes were integrated through direct pushes rather than
GitHub pull requests. Those records deliberately use `pull_request_style_review`
and `commit_derived_reconstruction`; they do not invent PR numbers or claim a
verbatim human transcript. Adoption is demonstrated by a reachable main-history
commit, release tag, or passing repository gate.

Run the standalone evidence gate:

```bash
python scripts/check_maintenance_evidence.py
```

Validate only structure and provenance without rerunning commands:

```bash
python scripts/check_maintenance_evidence.py --no-replay
```

`python scripts/run_rigorbench.py` also replays this suite, so removing a record,
breaking its Git provenance, changing a command marker, or dropping one workflow
below three passing traces fails CI and one-command release verification.
