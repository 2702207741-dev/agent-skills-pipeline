---
name: test-design-workflow
description: Use when the user asks to design, add, improve, or review tests for a feature, bug fix, API, CLI, UI, integration, migration, or security boundary. Use when test scope, success/failure/boundary cases, fixtures, mocks, automation level, or regression confidence must be chosen.
version: 1.0.0
metadata:
  tags: [testing, test-design, regression, quality]
  related_skills: [agent-security-guard, cross-model-verification, observability-workflow, requirements-clarifier]
---

# Test Design Workflow

## Overview

Good tests protect behavior, not implementation trivia. Extract the contract, map risk to the lowest proving level, design cases, then prove each regression catches its defect.

## When to Use

| Use When | Don't Use When |
|----------|----------------|
| The user says "add tests", "design tests", "test plan", "coverage gap", "regression test", or "what should we test" | A failing test or bug still needs root-cause investigation; use `systematic-debugging` first |
| A feature, bug fix, API, CLI, UI flow, migration, or integration needs automated or manual coverage | The user only asks to run an existing test command with no design decision |
| Code review finds missing tests, weak assertions, over-mocking, snapshot churn, or happy-path-only coverage | The artifact is a broad code review; use `code-review-workflow` |
| Behavior has validation rules, permissions, money/data risk, time/order sensitivity, compatibility, or external systems | There is no behavior contract, requirement, diff, bug report, or user path to test |
| Existing tests are brittle, slow, flaky, broad, or tied to implementation details | The user wants browser QA report-only exploration; use the local QA skill if available |

## Phase 0 Benchmark Decision

Type: Technique. Adopt the Superpowers/GStack pattern: behavior-first tests, red proof before confidence, user-path evidence for QA, local style matching, and verification before coverage claims.

## Test Design Gate

```
No behavior contract -> no test design.
No expected result -> no test case.
No failure proof for a regression test -> no confidence claim.
```

If the contract is vague, load `requirements-clarifier` before inventing tests.

## The Process

```
contract -> risk -> level -> cases -> fixtures -> style -> fail proof -> report
    |        |       |        |         |         |          |          |
    v        v       v        v         v         v          v          v
behavior  blast   pyramid  matrix    boundary  patterns   red/green  residual
```

### Step 1: Extract the Behavior Contract

**Expected Output:** `contract=<observable behavior>, actor=<user|system>, input=<data>, output=<result>, invariant=<must hold>`

Name the behavior before choosing test mechanics. Pull it from requirements, bug report, diff, PR, route, CLI help, API schema, or existing tests.

```bash
git status --short
git diff --name-status
git diff --stat
rg -n "TODO|FIXME|acceptance|should|must|error|permission|validation" .
```

Contract format: `when <actor> does <action> with <input/state>, system returns <output/state>; invariant=<must hold>; risk=<who is hurt>`.

**If fails:**
- No contract -> ask for acceptance criteria or use `requirements-clarifier`.
- Only implementation detail exists -> translate it to user-visible behavior before testing.
- Bug fix has no repro -> use `systematic-debugging` to capture the failing path first.

### Step 2: Map Risk to Test Level

**Expected Output:** `levels=<unit|integration|contract|e2e|manual>, rationale=<risk and feedback speed>`

Choose the lowest level that proves the contract without hiding the boundary that can fail.

| Risk signal | Prefer |
|-------------|--------|
| Pure function, parser, validator, state reducer | Unit |
| DB query, transaction, cache, job, filesystem | Integration |
| API request/response, CLI contract, SDK compatibility | Contract or integration |
| Auth, billing, checkout, onboarding, critical UI workflow | E2E plus lower-level tests |
| Migration, data repair, idempotency, rollback | Integration plus dry-run checklist |
| Visual-only CSS or copy | Component/screenshot/manual |
| External service | Contract fake plus one safe smoke test |

Detect local test surfaces:

```bash
rg --files -g "*test*" -g "*spec*" -g "__tests__/**"
rg --files | rg "pytest|vitest|jest|playwright|cypress|package.json|pyproject.toml|go.mod|Cargo.toml"
```

**If fails:**
- No test framework -> propose the smallest harness and a manual fallback.
- E2E is too slow -> cover logic lower down and keep one smoke path.
- Boundary is mocked away -> move the test outward until that boundary is exercised.

### Step 3: Build the Case Matrix

**Expected Output:** `cases=<success/failure/boundary/regression table>, expected_results=<specific assertions>`

Design cases before writing code. Cover success, failure, boundary, and regression cases per behavior change.

| Case type | Include when | Example assertion |
|-----------|--------------|-------------------|
| Success | Main promised behavior | returns 201 and persists one record |
| Failure | Invalid input, denied auth, dependency error | returns 400 with field error |
| Boundary | empty, null, min/max, duplicate, timezone, pagination | page 2 starts after page 1 |
| State transition | status, retry, idempotency, concurrency | duplicate webhook does not double charge |
| Regression | Known bug was fixed | old failing input returns expected result |
| Compatibility | API/CLI/config used by callers | old flag still works with warning |
| Security | auth, tenant, secret, shell, SSRF, LLM output | tenant data is isolated |

Case row format:

```markdown
| ID | Behavior | Setup | Action | Expected | Level |
```

**If fails:**
- Matrix has only success cases -> add at least one failure and one boundary case.
- Expected result says "works" -> replace with exact status, value, state, or visible text.
- Security boundary appears -> load `agent-security-guard` for adversarial cases.

### Step 4: Choose Fixtures, Mocks, and Oracles

**Expected Output:** `fixtures=<data>, mocks=<boundary only>, oracle=<how correctness is known>`

Fixtures must reveal behavior. Mock only boundaries you do not own or cannot make deterministic.

Rules:

- Use the smallest data that triggers the behavior.
- Name data by meaning.
- Prefer nearby factories/builders.
- Assert response, state, row, event, file, stdout, UI text, or metric.
- Avoid snapshots unless they are the contract.

Search local patterns:

```bash
rg -n "factory|fixture|beforeEach|setup|mock|stub|snapshot|assert|expect" tests test spec __tests__ 2>/dev/null
rg -n "describe\\(|it\\(|test\\(|expect\\(|assert" .
```

**If fails:**
- Mock returns exactly what the assertion expects -> use real code or assert boundary call.
- Snapshot changed without targeted assertion -> add a direct assertion or reject it.
- Fixture is huge -> shrink it until each field has a reason.

### Step 5: Match Local Test Style

**Expected Output:** `style=<framework>, command=<narrow test command>, new_file=<path|none>`

Read 2-3 nearby tests. Match imports, naming, setup, teardown, assertions, and file location.

```bash
rg --files | rg "(test|tests|spec|__tests__)"
rg -n "changedFunction|newEndpoint|newStatus|featureFlag" tests test spec __tests__ src app lib 2>/dev/null
```

Framework command examples:

```bash
python -m pytest tests/path/test_file.py::test_name -q
npm test -- path/to/file.test.ts
pnpm test path/to/file.spec.ts
go test ./path/to/package -run TestName -count=1
cargo test test_name -- --nocapture
```

**If fails:**
- No nearby tests -> use the closest same-layer pattern and state the gap.
- Existing tests are poor -> match the harness but improve assertions.
- User asked for plan only -> output file paths, cases, and commands without editing tests.

### Step 6: Write or Specify the Tests

**Expected Output:** `tests=<files|plan>, assertions=<behavior assertions>, command=<narrow command>`

For implementation tasks, write tests in red-green style:

```
write test -> run narrow command -> confirm expected failure -> implement/fix -> rerun
```

For planning or review tasks, specify the exact test file, setup, action, assertion, and command.

Test body checklist: name behavior and condition; create only needed state; perform the real action; assert the contract; for failures assert error and unchanged state; name the boundary value.

**If fails:**
- Test passes before the change -> it does not prove the new behavior; adjust the case.
- Test errors from setup -> fix setup before trusting red/green.
- Test needs many unrelated mocks -> reconsider design or test at a different level.

### Step 7: Prove the Test Can Catch the Bug

**Expected Output:** `failure_proof=<red observed|mutation observed|not possible>, evidence=<command output>`

Regression tests need proof. Use one safe method:

1. Run before fix if the bug is still present.
2. Temporarily revert the fix, run the test, restore the fix.
3. Temporarily mutate the guarded condition, run the test, restore it.
4. If none is safe, state why and lower confidence.

Commands:

```bash
git diff -- path/to/file
python -m pytest tests/path/test_file.py::test_name -q
npm test -- path/to/file.test.ts
```

**If fails:**
- Cannot safely mutate/revert -> record `failure_proof=not possible` and residual risk.
- Wrong failure reason -> fix until it fails for the intended behavior.
- Red proof missing but final claims say "regression protected" -> rewrite claim.

### Step 8: Verify Scope and Report Residual Risk

**Expected Output:** `coverage=<cases covered>, commands=<run/not run>, residual=<untested risks>`

Run the narrow test, then the smallest wider suite:

```bash
python -m pytest tests/path/test_file.py::test_name -q
python -m pytest tests/path -q
npm test -- path/to/file.test.ts
npm test
go test ./...
cargo test
```

Report format:

```markdown
Test design:
- Contract: <behavior>.
- Cases: <success/failure/boundary/regression/security>.
- Files/commands: <paths and commands>.
- Failure proof: <red/mutation/not possible>.
- Residual risk: <manual-only, external dependency, unrun suite, or none identified>.
```

Do not claim "covered" for cases not encoded in assertions or manual steps.

**If fails:**
- Narrow test fails -> fix the test or implementation before wider runs.
- Wider suite fails outside scope -> report it separately; do not claim full pass.
- Commands were not run -> mark `run/not run` and name the residual risk.

## Bad/Good Test Patterns

### Pattern 1: Implementation Detail

**Bad:**
```markdown
Assert `normalizePayload()` is called twice.
```

**Good:**
```markdown
Submit duplicate payloads and assert only one invoice row exists.
```

### Pattern 2: Happy Path Only

**Bad:**
```markdown
Test valid checkout returns success.
```

**Good:**
```markdown
Test valid checkout succeeds, declined card returns 402 without order creation, and duplicate webhook is idempotent.
```

## Rationalization Table

| Rationalization | Why it fails |
|-----------------|--------------|
| "Coverage went up, so tests are good" | Coverage measures lines, not behavior, assertions, or risk. |
| "The implementation is simple" | Simple branches still fail at boundaries, invalid input, and future changes. |
| "Snapshots cover it" | Snapshots catch broad text drift but rarely prove intended behavior. |
| "Mocking is faster" | A fast mock that hides the real boundary can prove the wrong system. |
| "E2E covers everything" | E2E is slow and brittle; it often misses exact edge cases. |

## Red Flags

- You are choosing a framework before naming the behavior.
- You are writing only happy-path tests for validation, auth, money, data, or migration.
- You are asserting private calls, CSS classes, or mock calls instead of observable behavior.
- You are adding a snapshot without a targeted assertion.
- You cannot explain how the new test would fail without the fix.
- You are mocking the same boundary where the bug happened.
- You say "covered" or "probably enough" without command evidence.
- You invent a new harness instead of matching local style.

## Common Pitfalls

| Symptom | Root cause | Fix |
|---------|------------|-----|
| Test passes before implementation | The test asserts existing behavior or a mock | Change setup/action/assertion until it fails for the missing behavior |
| Bug recurs despite a regression test | Test did not encode the original failing input or assertion | Recreate the exact precondition and assert the corrected observable result |
| Suite is slow and brittle | Too many broad E2E tests for low-level logic | Move logic cases down; keep one smoke path for workflow confidence |
| Test fails only in CI | Shared state, time, order, locale, env, or resource assumptions leaked | Isolate state, control time, avoid order dependency, and run repeat checks |
| Snapshot updates hide behavior drift | Snapshot became the oracle without intent | Add direct assertions for the contract or narrow the snapshot |
| Mock-heavy test misses integration bug | The mocked boundary was the failing boundary | Use fake server, test DB, or integration harness for that boundary |

## Verification Checklist

- [ ] Behavior contract names actor, input/state, action, expected result, and invariant.
- [ ] Test level is justified by risk and feedback speed.
- [ ] Case matrix includes success, failure, boundary, and regression when applicable.
- [ ] Security, permission, tenant, money, data-loss, and migration risks have explicit cases when present.
- [ ] Fixtures and mocks preserve the boundary being tested.
- [ ] Local test style and command were discovered before adding or recommending tests.
- [ ] Each test assertion checks observable behavior, not only implementation details.
- [ ] Regression test has red/mutation proof or an explicit confidence limitation.
- [ ] Narrow test command and relevant wider command are listed with run/not-run status.
- [ ] Residual untested risk is named instead of hidden.

## Interaction with Other Skills

| Related Skill | Trigger | Handoff |
|---------------|---------|---------|
| **requirements-clarifier** | Contract vague | Clarify inputs, outputs, invariants, done conditions |
| **systematic-debugging** | Bug lacks root cause | Reproduce, isolate, produce regression target |
| **code-review-workflow** | Diff needs test review | Convert review gaps into test cases |
| **observability-workflow** | Signals insufficient | Add logs, metrics, traces as test oracles |
| **agent-security-guard** | Security boundary present | Add adversarial security cases |
| **cross-model-verification** | Plan high-risk or uncertain | Independent adversarial review |
