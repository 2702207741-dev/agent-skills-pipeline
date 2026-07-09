---
name: systematic-debugging
description: Use when the user asks to debug a failing test, runtime error, crash, flaky behavior, regression, misconfiguration, build failure, deployment failure, performance anomaly, or wrong output. Use when the task says "debug this", "why does this fail", "find root cause", "fix this bug", or "this used to work".
version: 1.0.0
metadata:
  tags: [debugging, defects, regression, workflow]
  related_skills: [agent-security-guard, cross-model-verification, incident-retro-workflow, observability-workflow]
---

# Systematic Debugging

## Overview

Debugging is evidence work: reproduce, trace root cause, change one variable, and verify the original failure path before claiming success.

## When to Use

| Use When | Don't Use When |
|----------|----------------|
| The user says "debug this", "why does this fail", "find root cause", "fix this bug", or "this used to work" | The user asks only for a broad code review with no concrete symptom; use `code-review-workflow` |
| A test, build, command, service, UI path, job, or integration fails with an error, crash, timeout, bad output, or flaky result | The cause is already proven and the user only asks for implementation |
| A regression appears after recent code, config, dependency, data, environment, or deployment changes | The task is only to design tests from scratch; use `test-design-workflow` |
| A previous fix failed, made the symptom move, or revealed a different failure | The user wants an incident narrative after service is restored; use `incident-retro-workflow` |
| The failure crosses API, database, CI, model-tool, or browser-backend boundaries | No artifact, symptom, log, reproduction step, or affected behavior is available |

## Phase 0 Benchmark Decision

Type: Technique. Adopt the Superpowers/Hermes pattern: no fix before root cause, trace bad values backward, replace timing guesses with condition waits, add defense-in-depth after proof, and stop after repeated failed fixes to reassess architecture.

## Root-Cause Gate

```
No root-cause evidence -> no final fix claim.
No reproduction or bounded limitation -> no root-cause claim.
Three failed fix attempts -> stop changing code and reassess the model.
```

Mitigation is allowed only when the user needs containment. Label it `mitigation`, keep investigating, and do not present it as the fix.

## The Process

```
symptom -> reproduce -> localize -> trace -> hypothesize -> patch -> verify -> report
   |          |           |        |          |           |        |         |
   v          v           v        v          v           v        v         v
signal     command     boundary  source   falsifier   minimal  original  residual
```

### Step 1: Capture the Failure Contract

**Expected Output:** `symptom=<observable failure>, expected=<behavior>, actual=<behavior>, artifact=<command|log|screenshot|trace>, environment=<known|unknown>`

Start with the exact failure, not a theory:

```bash
git status --short
git branch --show-current
git rev-parse --show-toplevel
```

Collect the command, log, stack trace, input, state, environment, commit, and expected behavior.

Useful capture commands:

```bash
git log --oneline -n 10
git diff --stat
git diff --name-status
rg -n "error message|exception class|failing symbol|route name" .
```

**If fails:**
- No repo or artifact -> ask for the failing command, log, or affected file and mark the state `blocked: missing symptom`.
- Log is huge -> extract the first failure, stack top, stack bottom, and any repeated causal line.
- Failure is production-only -> collect safe logs and config facts first; do not invent local certainty.

### Step 2: Reproduce or Bound the Failure

**Expected Output:** `repro=<always|intermittent|not reproduced>, command=<exact command>, runs=<N>, failing signal=<line|assertion|status>`

Run the smallest known reproduction. Prefer one test, one request, one build target, or one job step.

Common commands:

```bash
python -m pytest tests/path/test_file.py::test_name -q
npm test -- path/to/test.spec.ts
pnpm test path/to/test.spec.ts
go test ./path/to/package -run TestName -count=1
cargo test test_name -- --nocapture
```

For flaky behavior, measure before editing:

```bash
for i in {1..20}; do python -m pytest tests/path/test_file.py::test_name -q || break; done
for i in {1..20}; do npm test -- path/to/test.spec.ts || break; done
```

**If fails:**
- Cannot reproduce locally -> compare environment, dependencies, feature flags, data, time, timezone, locale, credentials, and network access.
- Reproduction takes too long -> make a narrower harness or log the limitation before proceeding.
- Failure disappears -> preserve the last known failing signal; do not claim fixed.

### Step 3: Localize the Suspect Boundary

**Expected Output:** `boundary=<component A -> component B>, narrowed=<file|function|config|data>, rejected=<hypotheses>`

Identify where expected state turns into bad state. Change one variable at a time.

```bash
rg -n "failingFunction|errorCode|configKey|envVar|routeName|tableName" .
rg -n "timeout|retry|cache|lock|transaction|feature flag|migration|schema" .
rg -n "process\\.env|os\\.environ|dotenv|config\\.|settings\\." .
```

Read both sides of the boundary: request/response, validation/defaults, transaction/query, fixture cleanup, working directory, env propagation, parsed model output, and allowlists.

**If fails:**
- Multiple boundaries look plausible -> add diagnostic logging at each boundary and run once.
- Search is noisy -> search sibling enum values, route names, JSON keys, table columns, and old error text.
- Boundary contains secrets or destructive operations -> load `agent-security-guard` before probing.

### Step 4: Trace Back to the Root Cause

**Expected Output:** `root_cause=<source condition>, evidence=<trace>, falsifier=<what would disprove it>`

Trace from the symptom to the source:

```
Where did the bad value appear?
  |
  +-- What code directly produced or accepted it?
        |
        +-- What called that code?
              |
              +-- What input, state, config, migration, dependency, or timing changed?
                    |
                    +-- Is this the earliest source that explains every symptom?
```

Instrumentation example:

```javascript
console.error("DEBUG boundary", {
  value,
  cwd: process.cwd(),
  env: process.env.NODE_ENV,
  stack: new Error().stack,
});
```

```bash
git log --oneline -- path/to/suspect_file
git blame -L 40,90 path/to/suspect_file
git show --stat HEAD
```

Root-cause statement format:

```markdown
Root cause: <source condition> causes <bad intermediate state>, which reaches <failure point>.
Evidence: <command/log/test/code path>.
Falsifier: <specific observation that would make this hypothesis false>.
```

### Step 5: Compare Against Working Patterns

**Expected Output:** `working_example=<file|none>, differences=<list>, chosen_delta=<minimal change>`

Find nearby code that already succeeds. Do not patch until differences are explained.

```bash
rg -n "similarFunction|sameEndpoint|sameStatus|sameEvent|sameConfig" .
rg -n "success case|happy path|known good|fixture|factory" tests src app lib .
```

Compare input shape, validation, state setup, dependency version, cleanup/order, and error handling. Record only differences that explain the observed failure.

**If fails:**
- No working example -> use docs, tests, schema, or old commit as the reference.
- Working example differs in many ways -> test one difference at a time.
- Reference contradicts current design -> pause and state the design mismatch before editing.

### Step 6: Test the Hypothesis with One Variable

**Expected Output:** `hypothesis=<one sentence>, test=<minimal observation>, result=<confirmed|rejected|inconclusive>`

Use the scientific loop: state one hypothesis, pick one observation that can disprove it, run the narrow reproduction, then mark the result confirmed, rejected, or inconclusive.

Bad experiment:

```bash
# Changes timeout, mock, fixture, and assertion at once.
npm test -- path/to/test.spec.ts
```

Good experiment:

```bash
# Only disables cache to test whether stale cache explains the failure.
DISABLE_CACHE=1 npm test -- path/to/test.spec.ts
```

**If fails:**
- Two attempts rejected -> revisit Step 3 and Step 4 instead of piling on guesses.
- Three attempted fixes failed -> stop and ask whether the architecture, test model, or requirement is wrong.
- The quickest action is a mitigation -> label it mitigation and continue root-cause work.

### Step 7: Patch the Root Cause, Not the Symptom

**Expected Output:** `fix=<minimal diff>, regression=<test|harness|manual path>, scope=<files changed>`

Before editing, create or identify the failing check:

```bash
python -m pytest tests/path/test_file.py::test_name -q
npm test -- path/to/test.spec.ts
go test ./path/to/package -run TestName -count=1
```

Patch rules:

- Change the earliest source that explains the failure.
- Keep the diff small; no unrelated cleanup.
- Add validation at each layer bad data crosses when the bug is caused by invalid input or unsafe state.
- Replace arbitrary sleeps with condition-based waits when the bug is timing-related.
- Add or update a regression test when the codebase has a test surface.

Condition wait pattern:

```javascript
await waitFor(() => state.ready === true, "state.ready");
```

Defense-in-depth layers: entry validation, domain invariant, environment guard, and safe forensic logging.

### Step 8: Verify and Report

**Expected Output:** `verified=<yes|no>, original_repro=<pass|fail|not available>, regressions=<pass|fail|not run>, residual=<list>`

Run the original failure path plus relevant regressions:

```bash
python -m pytest tests/path/test_file.py::test_name -q
npm test -- path/to/test.spec.ts
npm test
go test ./...
```

For flaky fixes, repeat the narrow check:

```bash
for i in {1..20}; do python -m pytest tests/path/test_file.py::test_name -q || break; done
```

Final report format:

```markdown
Root cause: <one sentence>.
Fix: <minimal change>.
Verification: <commands and results>.
Residual risk: <unrun tests, unavailable env, external dependency, or none identified>.
```

Do not say "fixed" if the original reproduction was not rerun. Say `best effort` or `not reproduced locally` with the evidence gathered.

## Bad/Good Debugging Patterns

### Pattern 1: Patch Before Reproduction

**Bad:**
```markdown
It is probably a timeout, so I increased the timeout and pushed the fix.
```

**Good:**
```markdown
Reproduced with `npm test -- checkout.spec.ts` 6/20 runs. The failure occurs before the payment mock emits `ready`. Replaced the fixed 100 ms sleep with a wait for the `ready` event and verified 20/20 runs.
```

### Pattern 2: Fixing Where the Error Appears

**Bad:**
```markdown
`user.id` is undefined in `renderProfile`, so I added `user?.id`.
```

**Good:**
```markdown
`user.id` becomes undefined when `loadSession()` accepts an expired token and returns `{ user: {} }`. The fix rejects expired sessions at `loadSession()` and adds a regression for the expired-token path.
```

## Rationalization Table

| Rationalization | Why it fails |
|-----------------|--------------|
| "The fix is obvious" | Obvious fixes often target the symptom; root cause proves where the change belongs. |
| "The test passed once" | A single pass does not prove a flaky failure is gone. Repeat the narrow check. |
| "No time to reproduce" | Skipping reproduction loses the only signal that proves success. Use mitigation language if containment is urgent. |
| "I changed several things to be safe" | Multiple changes destroy causality and can introduce hidden regressions. |

## Red Flags

- You are editing before running or bounding the failing path.
- You are using "probably", "likely", "maybe", or "should fix it" as evidence.
- You are changing two variables before rerunning the reproduction.
- You are adding sleeps, retries, null checks, or optional chaining without explaining the source condition.
- You are fixing the stack-frame where the error surfaced without tracing who supplied the bad value.
- You are ignoring the first error and debugging later cascading errors.
- You have tried two fixes already and are preparing a third without a sharper hypothesis.
- You have tried three fixes and still have no root cause.

## Common Pitfalls

| Symptom | Root cause | Fix |
|---------|------------|-----|
| Bug returns after a "small" patch | The patch masked the symptom instead of changing the source condition | Trace backward to the first bad value or state transition and patch there |
| Test passes locally but fails in CI | Environment, order, time, cache, path, dependency, or resource limit differs | Capture CI facts, reproduce the difference, and remove the hidden assumption |
| Flaky test gets slower but not stable | Arbitrary sleep guesses at timing | Wait for the actual condition with timeout and clear failure message |
| New fix breaks another path | Multiple variables changed or invariant was not understood | Revert experiments, isolate one hypothesis, and add a regression for both paths |
| Third fix attempt starts | Architecture or mental model may be wrong | Stop editing; summarize attempts, evidence, and the model that needs reassessment |

## Verification Checklist

- [ ] Failure contract records expected behavior, actual behavior, artifact, and environment.
- [ ] Original failure is reproduced, measured as flaky, or explicitly bounded as not reproducible.
- [ ] Suspect boundary is named and at least one alternative hypothesis is rejected.
- [ ] Root-cause statement explains source condition, bad intermediate state, and failure point.
- [ ] Any experiment changes one variable and has a result of confirmed, rejected, or inconclusive.
- [ ] Fix targets the root cause rather than only the visible symptom.
- [ ] Regression test, harness, or manual reproduction covers the original failure path.
- [ ] Verification reruns the original failure path and relevant wider tests when available.
- [ ] Residual risk states unrun tests, unavailable environments, external dependencies, or none identified.

## Interaction with Other Skills

| Related Skill | Trigger | Handoff |
|---------------|---------|---------|
| **test-design-workflow** | Need regression, boundary, or flaky-test coverage | Convert root cause into tests |
| **code-review-workflow** | Fix needs risk review before merge | Review the verified diff |
| **observability-workflow** | Logs, metrics, or traces are insufficient | Design durable signals |
| **incident-retro-workflow** | Production issue is restored | Build timeline and action items |
| **agent-security-guard** | Debugging touches secrets, auth, shell, production data, or LLM-tool boundaries | Gate the risky operation |
| **cross-model-verification** | Root cause remains uncertain or blast radius is high | Request adversarial pass |
