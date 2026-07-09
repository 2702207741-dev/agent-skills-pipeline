---
name: code-review-workflow
description: Use when the user asks to review code, a diff, pull request, patch, branch, implementation, or change set for bugs, regressions, security risks, data loss, concurrency issues, performance problems, maintainability risks, API contract drift, or missing tests. Do NOT use for reviewing SKILL.md quality; use skill-review-workflow for skill files.
version: 1.0.0
metadata:
  tags: [code-review, pr-review, quality, technique]
  related_skills: [agent-security-guard, cross-model-verification, git-workflow-for-agents, systematic-debugging, test-design-workflow]
---

# Code Review Workflow

## Overview

Review code to find behavior risk before merge. Read the whole diff, trace changed behavior outside edited lines, and report issues that can fail users, data, security, tests, or maintenance. Output findings first, ordered by severity, with evidence, failure mode, and the smallest actionable fix

## When to Use

| Use When | Don't Use When |
|----------|----------------|
| The user says "review this PR", "code review", "check my diff", "look for bugs", "pre-landing review", or "is this safe to merge" | The artifact is a `SKILL.md` quality review; use `skill-review-workflow` |
| A branch, patch, pull request, commit range, or uncommitted diff needs review before merge | The user asks to implement fixes immediately instead of review; clarify whether to review first or fix |
| Code touches auth, money, billing, data deletion, migrations, shell commands, LLM output, concurrency, caching, release, or CI/CD | The user only wants formatting, naming, copyediting, or style polish |
| Tests changed and need review for false confidence, missing negative paths, or regression gaps | The user wants a test plan from scratch; use `test-design-workflow` |
| A previous implementation needs an independent safety pass before deployment | No code, diff, commit, or design artifact is available |

## Phase 0 Benchmark Decision

Type: Technique. Adopt the GStack/Hermes review pattern: review against merge-base, run critical categories first, read consumers outside the diff, and back every claim with evidence. Omit platform preambles, telemetry, Greptile handling, and default auto-fix behavior.

## The Process

```
scope -> diff -> changed behavior -> risk passes -> tests -> findings -> decision
   |       |            |                |          |          |
   v       v            v                v          v          v
artifact  base       call/data flow    severity   coverage   merge signal
```

### Step 1: Establish Review Scope

**Expected Output:** `scope=<branch|diff|files>, base=<branch|commit|none>, files=<N>, mode=<read-only|fix-after-review>`

Run the narrowest commands that match the artifact:

```bash
git status --short
git branch --show-current
git rev-parse --show-toplevel
```

If reviewing a branch against a base branch:

```bash
git fetch origin main --quiet
DIFF_BASE=$(git merge-base origin/main HEAD)
git diff --stat "$DIFF_BASE"
git diff --name-status "$DIFF_BASE"
```

If the base branch is not `main`, replace it with the PR base. With GitHub CLI: `gh pr view --json baseRefName,headRefName` and `gh pr diff`.

**If fails:**
- `fatal: not a git repository` -> no repository context -> ask for the diff or repo path.
- `origin/main` missing -> base unknown -> run `git branch -a` and ask which base to use.
- Patch only -> review patch text as static artifact and label execution confidence limited.

### Step 2: Read the Whole Diff Before Commenting

**Expected Output:** `diff read: <files>, <insertions>/<deletions>, high-risk files=<list>`

Read the complete diff before forming findings:

```bash
git diff "$DIFF_BASE"
git diff "$DIFF_BASE" -- path/to/file
git show --stat --oneline HEAD
```

For large diffs, chunk by file:

```bash
git diff --name-only "$DIFF_BASE"
git diff "$DIFF_BASE" -- path/to/high-risk-file
```

Classify files before deep review:

| File signal | Review stance |
|-------------|---------------|
| `migrations/`, `schema`, `sql`, `models` | Data safety |
| `auth`, `session`, `token`, `permission` | Security |
| `queue`, `worker`, `lock`, `cache`, `retry`, `async` | Race and idempotency |
| `prompt`, `llm`, `agent`, `tool`, `parser` | Trust boundary |
| `.github/workflows`, `release`, `install`, `package` | Supply-chain and CI/CD |
| tests only | False confidence and missing assertions |

**If fails:** diff too large -> review by risk-ranked file groups; generated files dominate -> review generator or source input.

### Step 3: Trace Behavior Outside Edited Lines

**Expected Output:** `touched behavior=<entrypoints>, consumers=<files>, unchecked assumptions=<list>`

Search before claiming a change is complete:

```bash
rg -n "newStatus|NewEnumValue|changedFunction|featureFlag" .
rg -n "dangerouslySetInnerHTML|html_safe|eval\\(|exec\\(|shell=True" .
```

For a changed function or exported symbol:

```bash
rg -n "functionName\\(" .
rg -n "existingValue1|existingValue2|newValue" .
rg -n "\\bcase\\b|switch|if .*status|allowed|valid|include|exclude" path/to/relevant/dir
```

Read each consumer that branches, filters, serializes, validates, displays, or persists the value. If search is noisy, search sibling values, route names, JSON keys, database columns, and fixtures.

### Step 4: Run Risk Passes in Severity Order

**Expected Output:** `findings grouped by Security, Critical, Nit, or explicit no-finding result`

Use this order. Stop style commentary until these passes are complete.

#### Pass 1: Security

Check for exploitable or sensitive failures:

```bash
git diff "$DIFF_BASE" | rg -n "password|secret|api[_-]?key|token|Bearer|private_key|sk-|AKIA|xox"
git diff "$DIFF_BASE" | rg -n "eval\\(|exec\\(|os\\.system|subprocess\\..*shell=True|curl .*\\| bash"
git diff "$DIFF_BASE" | rg -n "dangerouslySetInnerHTML|html_safe|raw\\(|v-html|mark_safe"
```

Flag:
- Auth bypass, missing authorization check, tenant isolation failure.
- Secret exposure in code, tests, logs, CI, release manifests, screenshots, or prompts.
- Shell injection, unsafe deserialization, remote script execution.
- LLM output used as a command, URL fetch target, SQL fragment, email address, file path, or tool argument without validation.
- SSRF, XSS, path traversal, open redirect, CSRF, unsafe CORS.

If a Security finding appears, load `agent-security-guard`.

#### Pass 2: Critical Correctness

Flag likely user-visible failure:

- Data loss, double write, migration without rollback, non-idempotent retry.
- Read-check-write race without unique constraint, lock, compare-and-swap, or transaction.
- Status transition not guarded by old status.
- New enum/status not handled by all consumers.
- Changed API contract without caller/client update.
- Error swallowed, partial failure reported as success, or background job silently drops work.
- Timezone, pagination, off-by-one, empty input, duplicate input, or stale cache bug.

Commands:

```bash
rg -n "transaction|lock|unique|retry|idempot|upsert" .
rg -n "try:|except|catch \\(|rescue|finally|return null|return None|console\\.error" .
```

#### Pass 3: Tests and Verification

Use `test-design-workflow` when review becomes test planning. Here, answer whether tests prove changed behavior.

```bash
git diff "$DIFF_BASE" -- '*test*' '*spec*' '__tests__/*'
rg -n "changedFunction|newStatus|newEndpoint|newFlag" test tests spec specs __tests__ 2>/dev/null
```

Flag:
- No regression test for fixed bug.
- Only happy path for auth, parsing, migration, or payment logic.
- Test asserts implementation detail but not user-visible behavior.
- Snapshot updated without behavior assertion.
- Mock hides the integration boundary that broke.

#### Pass 4: Maintainability, Performance, and Release

Flag only real future risk:

```bash
git diff "$DIFF_BASE" | rg -n "for .*await|Promise\\.all|sleep|setTimeout|SELECT \\*|N\\+1|TODO|FIXME"
git diff "$DIFF_BASE" -- .github/workflows package.json pyproject.toml Cargo.toml go.mod
```

Look for:
- O(n*m) lookup on hot path, missing eager load, unbounded query, unbounded retry.
- New dependency without lockfile or supply-chain consideration.
- CI path, artifact name, tag format, or publish target mismatch.
- Documentation that describes changed behavior but was not updated.

### Step 5: Write Findings, Not Vibes

**Expected Output:** `findings-first review with severity, evidence, failure mode, fix, tests`

Finding format:

```markdown
- Security: <short title>
  Evidence: `<file>:<line>` or `<diff hunk>`
  Failure mode: <what breaks, who is affected, how it can happen>
  Fix: <smallest actionable change>
  Test: <test or verification that would catch it>
```

Use `Critical:` for user-visible bugs, data loss, migration failures, release breakage, or incorrect results. Use `Nit:` for non-blocking readability or maintainability. Do not include praise before findings.

If no issues:

```markdown
No findings.

Residual risk: <unrun tests, unavailable environment, large generated files, or "none identified">
Decision: approve
```

Decision labels: `request changes` for Security/Critical, `approve with nits` for Nit only, `approve` for no findings, `blocked` for missing artifact/base/context.

### Step 6: Verify Before Final Claim

**Expected Output:** `review confidence=<high|medium|low>, tests=<run|not run>, unresolved=<N>`

Before final output, check your own claims:

- If you say "handled elsewhere", cite the file that handles it.
- If you say "tests cover it", cite the test file and assertion.
- If you say "safe because input is constrained", cite the constraint.
- If you cannot verify, say `unverified`, not `probably`.

Optional commands:

```bash
npm test
pytest -q
go test ./...
cargo test
```

If tests are unavailable or too expensive, do not pretend. State what was reviewed statically.

## Bad/Good Review Patterns

### Pattern 1: Style Before Safety

**Bad:**
```markdown
Looks good overall. Maybe rename `x` to `request`.
```

**Good:**
```markdown
- Critical: duplicate webhook delivery can charge twice
  Evidence: `billing/webhook.ts:88` checks `event.id` then inserts outside a transaction.
  Failure mode: concurrent retries both pass the check and create two invoices.
  Fix: add a unique index on `event_id` and treat duplicate-key as success.
  Test: concurrent delivery test for the same event id.
```

### Pattern 2: Trusting LLM Output

**Bad:**
```markdown
The model usually returns JSON, so parsing is fine.
```

**Good:**
```markdown
- Security: LLM URL can trigger SSRF
  Evidence: `fetcher.ts:51` passes `model.url` directly to `fetch`.
  Failure mode: prompt injection can make the model request `http://169.254.169.254`.
  Fix: parse URL, require https, and allowlist hostnames before fetch.
```

## Rationalization Table

| Rationalization | Why it fails |
|-----------------|--------------|
| "The diff is small, so risk is low" | A one-line auth, SQL, cache, or status transition change can be the highest-risk part of a release. |
| "Tests passed, so review can be shallow" | Tests prove only what they assert. Review still checks missing paths, unsafe assumptions, and boundary drift. |
| "I know this codebase, no need to read call sites" | Familiarity creates blind spots. New enum values, new callers, and changed contracts require fresh search. |
| "It is probably handled elsewhere" | Probably is not evidence. Cite the handler or report residual risk. |
| "The reviewer should be balanced" | Code review is not a compliment sandwich. Findings first; praise is usually noise. |

## Red Flags

- You are about to comment after reading only the changed lines.
- You are writing "looks good overall" before deciding whether there are findings.
- You found a new enum/status/type but have not searched sibling values.
- You see auth, tenant, secret, shell, SQL, LLM, or migration changes and treat them as ordinary refactors.
- You cannot name the user-visible failure mode for a finding.
- You are relying on "probably", "usually", "should be fine", or "tests likely cover this".
- You are reviewing a SKILL.md file with this skill instead of `skill-review-workflow`.
- You are about to edit code during review even though the user asked only for review.

## Common Pitfalls

| Symptom | Root cause | Fix |
|---------|------------|-----|
| Review reports only style nits | Safety passes were skipped or run after readability | Run Security and Critical passes first; style can wait |
| Finding says "could be wrong" but gives no path | The reviewer did not trace call sites or data flow | Add exact evidence, failure mode, and smallest fix |
| New enum works in one screen but breaks another | Only edited file was read | Search sibling enum values and read all consumers |
| Security issue is downgraded because "internal only" | Trust boundary was assumed | Treat internal inputs as hostile unless code enforces the boundary |
| Tests were mentioned but not inspected | Coverage inferred from file names | Open the test and cite the assertion, or call it unverified |
| Fix recommendation is bigger than the bug | Reviewer optimized for elegance | Recommend the smallest safe change; move refactor to Nit |
| No-finding review hides uncertainty | Missing context was not stated | Add residual risk: tests not run, base unknown, or environment unavailable |

## Verification Checklist

- [ ] Review surface declared: branch, base, files, and read-only or fix mode.
- [ ] Complete diff or risk-ranked file chunks were read before findings.
- [ ] Changed behavior was traced outside edited lines.
- [ ] Security pass completed for auth, secrets, shell, XSS, SSRF, LLM output, and unsafe external dispatch.
- [ ] Critical pass completed for data loss, races, migrations, enum completeness, contracts, and error handling.
- [ ] Tests were inspected for changed behavior; missing tests are explicit.
- [ ] Every finding has severity, evidence, failure mode, fix, and verification.
- [ ] Output is findings first, ordered Security, Critical, then Nit.
- [ ] No speculative language remains without an `unverified` label.
- [ ] Final decision is `request changes`, `approve with nits`, `approve`, or `blocked`.

## Interaction with Other Skills

| Related Skill | Trigger During Review | Handoff |
|---------------|----------------------|---------|
| **agent-security-guard** | Security finding, secret exposure, dangerous shell, risky git or deploy operation | Load for deeper safety scan |
| **test-design-workflow** | Review finds missing or weak tests | Convert gaps into success, failure, boundary, and regression tests |
| **systematic-debugging** | A finding requires reproducing a failure | Switch from review to reproduce, isolate, fix, verify |
| **cross-model-verification** | High-risk diff or reviewer uncertainty remains | Ask for independent adversarial pass |
| **git-workflow-for-agents** | Review result needs commit, branch, PR, or push handling | Use git workflow after review, never as a substitute for review |
