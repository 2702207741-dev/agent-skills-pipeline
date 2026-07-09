---
name: requirements-clarifier
description: Use when the user gives a vague product, feature, bug, workflow, automation, refactor, migration, UI, API, integration, or policy request and needs scope, acceptance criteria, constraints, non-goals, assumptions, tradeoffs, open questions, or a build-ready contract.
version: 1.0.0
metadata:
  tags: [requirements, clarification, acceptance-criteria, scope]
  related_skills: [agent-security-guard, cross-model-verification, observability-workflow]
---

# Requirements Clarifier

## Overview

Clarify enough to build safely without stalling. Convert vague intent into actor, goal, scope, assumptions, open questions, and pass/fail criteria.

## When to Use

| Use When | Don't Use When |
|----------|----------------|
| The user says "requirements", "acceptance criteria", "clarify", "scope", or "turn this into a spec" | Scope, data, UX, constraints, and criteria are already clear |
| A product, feature, UI, API, CLI, integration, automation, refactor, migration, or policy request is vague | The user only asks for code review; use `code-review-workflow` |
| A bug report lacks expected behavior, impact, inputs, reproduction, or done criteria | The failure is reproducible and needs root cause; use `systematic-debugging` |
| Planning, tests, implementation, or review depends on unstated assumptions | The user asks for a rough prototype and accepts assumption risk |
| Security, privacy, tenant, money, destructive action, or permissions are unclear | The task is pure test design with a stable contract |

## Phase 0 Benchmark Decision

Type: Technique with Pattern judgment. Adopt Superpowers/GStack habits: inspect context, ask only decision-changing questions, prefer one at a time, offer 2-3 options when direction matters, name assumptions/non-goals, and self-review for ambiguity, scope, and YAGNI. Omit write-doc, browser, telemetry, YC, and commit steps.

## Clarification Gate

```
No actor/goal/outcome -> no implementation plan.
No observable acceptance criteria -> no "ready to build" claim.
Blocking conflict unresolved -> ask before proceeding.
Low-risk unknown -> state a reversible assumption and continue.
Sensitive/destructive boundary unclear -> load agent-security-guard.
```

## The Process

```
request -> context -> ambiguity -> questions -> assumptions -> criteria -> options -> contract
```

### Step 1: Capture the Raw Request and Context

**Expected Output:** `raw_request=<quote>, source=<chat|issue|diff|doc>, artifact=<path|none>, mode=<clarify|assume|ask>`

Preserve the user's wording before translating it. Inspect context so questions are not generic.

```bash
git status --short
git rev-parse --show-toplevel
rg -n "TODO|FIXME|acceptance|requirement|user story|must|should|out of scope|non-goal" .
```

**If fails:**
- No repo/artifact -> clarify from conversation and label `artifact=none`.
- Missing file, issue, or ticket -> ask for it or proceed with `mode=assume`.
- Search is huge -> narrow to changed files, docs, tests, routes, or modules.

### Step 2: Restate Actor, Goal, Outcome, and Current State

**Expected Output:** `actor=<who>, goal=<capability>, outcome=<observable value>, current=<baseline>, success_signal=<metric|state|text>`

Translate into a behavior sentence:

```markdown
As <actor>, when <context>, I want <capability>, so that <outcome>.
Current state: <what happens now>.
Success signal: <observable result>.
```

Use specific nouns: role not "users", measurable effect not "better", visible state or latency not "seamless".

**If fails:**
- Actor is missing -> infer likely actor and mark it as an assumption.
- Outcome is only "make it better" -> ask what improves for whom.
- Current state is unknown for a bug -> use `systematic-debugging` before finalizing criteria.

### Step 3: Classify Ambiguity and Risk

**Expected Output:** `blocking_questions=<N>, assumptions=<N>, risk=<low|medium|high>, security=<yes|no>`

Separate blockers from safe assumptions.

| Missing or unclear | Default action |
|--------------------|----------------|
| Actor, goal, expected behavior, affected object | Ask before planning |
| Data model, API contract, migration, compatibility | Ask or inspect code |
| Auth, tenant, secret, payment, destructive action, shell, privacy | Load `agent-security-guard` |
| UI state, copy, color, sort, empty state | Assume reversible default |
| Performance, reliability, rollout, monitoring | State target or use `observability-workflow` |
| Test oracle or regression path | Use `test-design-workflow` after criteria exist |

**If fails:**
- Everything feels blocking -> rank by architecture, data, security, and test impact.
- Nothing feels blocking -> check hidden permissions, data-loss, and compatibility.
- Risk is high and no security skill is available -> pause and ask a safety question.

### Step 4: Ask Only Blocking Questions

**Expected Output:** `questions=<1-3>, reason=<decision each answer changes>, stop=<yes|no>`

Ask only when the answer changes implementation, data, UX, security, tests, rollout, or review. Ask one at a time; in async summaries, list at most three.

Question format:

```markdown
Question: <specific choice or short open question>
Why it matters: <implementation/test/security decision affected>
Default if unanswered: <reversible assumption or "blocked">
```

Prefer concrete options:

```markdown
Who can export reports? A) Admins B) Admins+analysts C) Project members
```

**If fails:**
- You wrote more than three questions -> keep only the ones that change work.
- Generic question -> replace with context-grounded options.
- User cannot answer -> pick a reversible default or mark `stop=yes` if irreversible.

### Step 5: Build Assumptions, Constraints, and Non-Goals

**Expected Output:** `assumptions=<table>, constraints=<list>, non_goals=<list>, reversibility=<safe|risky>`

Assumption log:

```markdown
| Assumption | Why safe | Rollback trigger |
|------------|----------|------------------|
| <default> | <evidence or low blast radius> | <signal that invalidates it> |
```

Constraints: platform, browser, OS, API version, retention, auth, tenant, localization, accessibility, budget, dependency, migration, rollout, compatibility.

Non-goals prevent scope creep:

```markdown
Non-goals:
- Does not redesign <adjacent system>.
- Does not migrate historical data beyond <named scope>.
- Does not change public API except <explicit change>.
```

**If fails:**
- Assumption cannot be rolled back -> promote it to a blocking question.
- Constraint conflicts with goal -> ask which wins.
- Non-goals remove core value -> revise scope; do not bury the tradeoff.

### Step 6: Produce Acceptance Criteria and Edge Cases

**Expected Output:** `criteria=<numbered pass/fail checks>, edge_cases=<list>, oracle=<how verified>`

Acceptance criteria must be observable. Use Given/When/Then or direct pass/fail.

```markdown
1. Given <state>, when <actor action>, then <visible/API/DB/event/log result>.
2. Given <invalid or denied case>, when <action>, then <error and unchanged state>.
3. Given <boundary>, when <action>, then <expected limit behavior>.
```

Cover categories that apply:

| Category | Include when |
|----------|--------------|
| Success | Main promised behavior |
| Failure | Invalid input, denied auth, dependency failure |
| Boundary | Empty, null, duplicate, min/max, time, pagination |
| Permission | Roles, tenants, ownership, secrets |
| Data | Persistence, rollback, idempotency, migration |
| Compatibility | API, CLI flags, config, old clients |
| Observability | Logs, metrics, alerts, health |
| Rollout | Feature flags, fallback, manual checks |

**If fails:**
- Criterion says "works" or "better" -> replace with status, value, state, text, event, or metric.
- Only success criteria exist -> add failure and boundary criteria.
- No oracle exists -> use `observability-workflow` or state manual verification explicitly.

### Step 7: Present Options and Tradeoffs When Direction Matters

**Expected Output:** `options=<2-3>, recommendation=<one>, tradeoff=<why>`

Present options only when multiple valid directions remain. Lead with a recommendation.

```markdown
| Option | Best when | Cost | Risk | Recommendation |
|--------|-----------|------|------|----------------|
| A | <context> | <effort> | <risk> | <yes/no> |
| B | <context> | <effort> | <risk> | <yes/no> |
```

Do not create fake choices. If one option dominates, say why and move to the contract.

**If fails:**
- Options differ only in wording -> collapse them.
- Recommendation is missing -> choose based on user goal, risk, and existing patterns.
- User picked an option that breaks constraints -> restate the conflict and ask for override.

### Step 8: Handoff the Clarified Contract

**Expected Output:** `ready=<yes|with-assumptions|blocked>, brief=<implementation contract>, open_items=<blocking|assumed|deferred>`

Finish with a contract a planner, implementer, tester, or reviewer can use directly.

```markdown
Goal:
Scope:
Non-goals:
Assumptions:
Constraints:
Acceptance criteria:
Edge cases:
Test hooks:
Risks:
Open questions:
Next skill:
```

Ready states:

| State | Meaning |
|-------|---------|
| `ready=yes` | No blocking questions remain |
| `ready=with-assumptions` | Unknowns are reversible and logged |
| `ready=blocked` | A decision is required before planning |

**If fails:**
- Handoff lacks criteria -> return to Step 6.
- Handoff contains hidden assumptions -> return to Step 5.
- Next step is multi-step or risky -> use `planning-workflow`.

## Bad/Good Clarification Patterns

### Pattern 1: Question Flood

**Bad:**
```markdown
Who is the user? What page? What colors? Which DB? What framework? How should errors work? Any tests? Any deadline?
```

**Good:**
```markdown
Question: Can non-admin project members export reports?
Why it matters: decides permission checks, API errors, and tests.
Default if unanswered: admins only.
```

### Pattern 2: Vague Acceptance Criteria

**Bad:**
```markdown
The dashboard should load fast and show useful errors.
```

**Good:**
```markdown
Given the report API times out, when the dashboard loads, then it shows "Report unavailable", logs `report_fetch_timeout`, and leaves cached data visible.
```

### Pattern 3: Hidden Assumption

**Bad:**
```markdown
I'll assume this only affects web users.
```

**Good:**
```markdown
Assumption: mobile is out of scope because no mobile route references this endpoint. Rollback trigger: user confirms mobile consumes it.
```

## Rationalization Table

| Rationalization | Why it fails |
|-----------------|--------------|
| "I'll just start; details will emerge" | Guesses become architecture, tests, and migration work that is costly to unwind. |
| "The user said use best judgment" | Best judgment means explicit assumptions, not invisible decisions. |
| "This is obvious" | Obvious to one agent can be wrong for the product, users, or constraints. |
| "Acceptance criteria are bureaucracy" | Criteria prove planning, testing, and review mean the same thing. |
| "Asking questions slows us down" | Asking the one blocking question is faster than building the wrong thing. |
| "Non-goals sound negative" | Non-goals prevent surprise scope and agent wandering. |

## Red Flags

- You are about to plan or code without actor, goal, outcome, and current state.
- You wrote more than three clarifying questions at once.
- A question would not change implementation, tests, UX, security, or rollout.
- Criteria use "works", "better", "nice", "easy", or "seamless".
- You assumed permissions, tenant behavior, destructive behavior, or data retention.
- Non-goals are missing for a broad feature, migration, refactor, or automation.
- You cannot name how each criterion will be verified.
- Tradeoffs are hidden inside one chosen path.
- You are treating `ready=with-assumptions` as the same as `ready=yes`.

## Common Pitfalls

| Symptom | Root cause | Fix |
|---------|------------|-----|
| Long questionnaire | Blockers and low-risk defaults are mixed | Ask only questions that change implementation, tests, UX, security, or rollout |
| Plan changes direction later | Actor, current state, or outcome was inferred silently | Restate fields and mark assumptions before planning |
| Tests cannot be designed | Criteria are not observable | Rewrite as state, status, text, event, row, file, or metric |
| User says result is out of scope | Non-goals and constraints were implicit | Add non-goals, constraints, and scope boundary before handoff |
| Security issue appears late | Sensitive boundary was treated as ordinary ambiguity | Route through `agent-security-guard` immediately |
| Contract feels too heavy | Decorative detail beats decision detail | Keep goal, scope, assumptions, criteria, risks, next step |
| "Ready" claim is disputed | Open, assumed, and deferred items are mixed | Separate `blocking`, `assumed`, and `deferred` |

## Verification Checklist

- [ ] Trigger scope covers vague product, feature, bug, workflow, automation, refactor, migration, UI, API, integration, and policy requests.
- [ ] Actor, goal, outcome, current state, and success signal are named.
- [ ] Ambiguity is split into blocking questions, assumptions, and deferred items.
- [ ] No more than three questions are asked at once; each names the decision it changes.
- [ ] Assumptions include why they are safe and what would invalidate them.
- [ ] Constraints and non-goals are explicit.
- [ ] Acceptance criteria are observable pass/fail checks.
- [ ] Failure, boundary, permission, data, compatibility, observability, and rollout cases are considered.
- [ ] Tradeoffs are presented when multiple valid approaches remain.
- [ ] Handoff ends with `ready=yes`, `ready=with-assumptions`, or `ready=blocked`.
- [ ] Next skill is selected after the contract is clear enough.

## Interaction with Other Skills

| Related Skill | Trigger | Handoff |
|---------------|---------|---------|
| **planning-workflow** | Multi-step implementation, migration, rollout, or refactor planning | Provide goal, scope, artifacts, criteria, risks, open questions |
| **test-design-workflow** | Criteria exist and tests need design | Provide criteria, edge cases, oracles, risk |
| **systematic-debugging** | Bug lacks reproduction, current state, or root cause | Clarify expected behavior, then isolate failure |
| **code-review-workflow** | Review needs requirements baseline | Provide criteria, non-goals, assumptions |
| **agent-security-guard** | Secrets, auth, tenant, shell, payment, privacy, or destructive actions appear | Pause and require safety framing |
| **observability-workflow** | Completion lacks signals | Define logs, metrics, traces, alerts, or manual checks |
| **cross-model-verification** | Requirements remain high-risk, ambiguous, or disputed | Request adversarial review of gaps and assumptions |
