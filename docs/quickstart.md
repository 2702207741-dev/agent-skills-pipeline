# Five-Minute Quickstart

This path installs one real skill into an isolated Codex home, diagnoses the
installed state, replays a hash-bound success case, and leaves machine-readable
evidence. It does not require provider API keys or write to your normal agent
configuration.

## Prerequisites

- Git
- Python 3.10 through 3.14
- macOS, Linux, or Windows PowerShell / Command Prompt

## 1. Clone

```bash
git clone https://github.com/2702207741-dev/agent-skills-pipeline.git
cd agent-skills-pipeline
```

## 2. Preview

```bash
./our-skills quickstart \
  --platform codex \
  --target-root "$PWD/.quickstart-home"
```

The command shows the exact source, destination, and file additions. It does not
write without `--apply`.

## 3. Install, Diagnose, and Run

```bash
./our-skills quickstart \
  --platform codex \
  --target-root "$PWD/.quickstart-home" \
  --apply
```

This single command:

1. previews installation of `code-review-workflow`;
2. installs it under `.quickstart-home/.codex/skills/`;
3. runs strict marketplace doctor checks;
4. replays the recorded success execution against the current `SKILL.md` hash;
5. writes `.quickstart-home/.our-skills-quickstart-run.json`.

Expected final lines:

```text
[PASS] 5/5 - Returned severity-ordered code review findings...
[OK] Quickstart complete at .../.quickstart-home
```

On Windows without a Unix-like shell, use:

```bat
our-skills.cmd quickstart --platform codex --target-root .quickstart-home --apply
```

## 4. Inspect or Roll Back

```bash
./our-skills doctor \
  --platform codex \
  --target-root "$PWD/.quickstart-home" \
  --skill code-review-workflow \
  --strict

./our-skills rollback \
  --platform codex \
  --target-root "$PWD/.quickstart-home" \
  --skill code-review-workflow \
  --apply
```

The audit log is retained at `.quickstart-home/.our-skills-audit/events.jsonl`.

For a production target, retain and inspect a content-bound plan before writing:

```bash
./our-skills install --platform codex --target-root ~ --plan-output install-plan.json
./our-skills install --platform codex --target-root ~ --apply-plan install-plan.json
```

The apply step rejects altered or stale source, destination, platform, or target
state. Its transaction ID can roll back every operation as one unit.

## Time Budget

| Step | Typical time |
|---|---:|
| Clone | 1 minute |
| Preview | under 10 seconds |
| Install and doctor | under 30 seconds |
| Replay one skill | under 5 seconds |
| Inspect evidence | 1-2 minutes |

The replay is deterministic recorded execution evidence, not a claim that a
live model was called. To use the installed skill with Codex, start Codex with
the isolated target as its home or install into your normal Codex target only
after reviewing the preview.
