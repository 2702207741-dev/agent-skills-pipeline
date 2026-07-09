# RigorBench v1.3 Eval Runs

This directory stores replayable E2E evidence for the registered skills.

`traces.json` is the source file consumed by `scripts/run_rigorbench.py`. Each registered skill must keep at least three traces:

- `success`
- `failure`
- `boundary`

Each trace records the input prompt, triggered skill, resources read, execution steps, final output, and score. `skill_sha256` must match the current `SKILL.md` file for that skill. When a skill changes, update or recapture the affected traces before merging; stale hashes fail RigorBench so regressions are visible instead of silently hidden.

Run:

```bash
python scripts/run_rigorbench.py
```

For machine-readable output:

```bash
python scripts/run_rigorbench.py --json
```
