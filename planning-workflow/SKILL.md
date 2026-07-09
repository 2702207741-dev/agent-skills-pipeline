---
name: planning-workflow
description: Use when the user asks to plan a project, roadmap, migration, refactor, release, investigation, multi-step implementation, risky change, or execution sequence and needs phases, dependencies, risks, validation gates, rollback, owners, or next actions.
version: 1.0.0
metadata:
  tags: [planning, roadmap, sequencing, workflow]
  related_skills: [agent-security-guard, cross-model-verification, git-workflow-for-agents, observability-workflow]
---

# Planning Workflow

## Overview

A good plan reduces risk without ceremony. Convert a goal into scope, phases, tasks, dependencies, gates, rollback, and next action.

## When to Use

| Use When | Don't Use When |
|----------|----------------|
| The user says "plan", "roadmap", "implementation plan", "migration plan", "release plan", or "break this down" | One-step edit with no sequencing or rollback risk |
| Work spans multiple files, systems, sessions, days, data stores, or deploy stages | Requirements are too vague; use `requirements-clarifier` first |
| A risky change needs validation gates, rollback points, owner handoffs, or rollout | The user asks to debug a concrete failure now; use `systematic-debugging` |
| The user wants phases, dependencies, task ordering, or an execution checklist | The user only asks for code review findings; use `code-review-workflow` |
| A migration, refactor, release, investigation, or roadmap must be executable before work starts | The user explicitly asks to skip planning and accepts unmanaged risk |

## Phase 0 Benchmark Decision

Type: Technique with planning judgment. Adopt Superpowers `writing-plans`: exact paths, bite-sized tasks, commands with expected output, no placeholders, self-review against the spec. Adopt GStack habits: challenge scope, identify architecture/test/performance/security gaps, keep unresolved decisions visible, and require gates for risky work. Omit save-to-doc, telemetry, browser, and commit rules.

## Planning Gate

```
No clear goal/scope -> use requirements-clarifier.
No evidence/work surface -> add discovery before implementation.
No gate -> no "ready to execute" claim.
No rollback for risky work -> mark blocked or discovery-first.
Sensitive/destructive boundary -> load agent-security-guard.
```

## The Process

```
goal -> evidence -> risk -> phases -> gates -> tasks -> review -> handoff
```

### Step 1: Establish the Planning Frame

**Expected Output:** `objective=<one sentence>, scope=<in>, non_goals=<out>, constraints=<list>, unknowns=<blocking|assumed|deferred>`

Define what the plan may solve. Pull from the request, requirements, issue, design doc, diff, logs, or release goal.

```bash
git status --short
git rev-parse --show-toplevel
rg -n "requirement|acceptance|scope|non-goal|TODO|FIXME|migration|release|rollback|flag" .
```

Frame format:

```markdown
Objective:
In scope:
Non-goals:
Constraints:
Known unknowns:
```

**If fails:**
- Objective or scope is unclear -> use `requirements-clarifier`.
- Scope covers unrelated systems -> split into separate plans.
- One-step edit -> produce a short checklist, not a phased plan.

### Step 2: Inventory Evidence and Work Surface

**Expected Output:** `artifacts=<paths>, work_surface=<files|systems>, dependencies=<internal|external>, test_surfaces=<commands|manual>`

Plan from evidence. Identify what exists, what changes, what depends on it, and how success is observed.

```bash
git diff --name-status
git diff --stat
rg --files
rg -n "describe\\(|it\\(|test\\(|pytest|playwright|cypress|go test|cargo test|health|metric|alert" .
```

Evidence table:

```markdown
| Area | Evidence | Plan impact |
|------|----------|-------------|
| <module/system> | <file/log/doc> | <task/risk/gate> |
```

**If fails:**
- No evidence -> add a discovery phase with explicit output.
- Too much surface -> narrow to affected paths, APIs, data, and tests.
- Test surface is missing -> plan verification before implementation.

### Step 3: Classify Plan Shape and Risk

**Expected Output:** `plan_type=<implementation|migration|refactor|release|investigation|roadmap>, risk=<low|medium|high>, mode=<checklist|phased|discovery>`

Choose the smallest plan shape that controls risk.

| Signal | Plan shape |
|--------|------------|
| Single safe change | Checklist |
| Multiple files/dependencies | Phased implementation |
| Unknown root cause | Investigation plan |
| Data, schema, compatibility, rollout | Migration/release |
| Product scope or timeline | Roadmap with decision gates |
| Security, secrets, tenant, payment, shell, destructive action | Safety-gated |

Risk scale:

| Risk | Meaning |
|------|---------|
| Low | Local, reversible, covered by fast checks |
| Medium | Cross-module, user-visible, or test gaps exist |
| High | Data loss, security, money, downtime, migration, external dependency, irreversible action |

**If fails:**
- Risk is high and rollback is unknown -> add discovery and rollback design first.
- Plan type is mixed -> split by independent outcomes.
- Security boundary appears -> load `agent-security-guard`.

### Step 4: Decompose into Phases with Entry and Exit Criteria

**Expected Output:** `phases=<ordered table>, entry=<criteria>, exit=<criteria>, gate=<verification>`

A phase is not a topic. It needs a start reason and done proof.

```markdown
| Phase | Goal | Entry criteria | Work | Exit criteria | Gate |
|-------|------|----------------|------|---------------|------|
| 0 Discovery | <unknown resolved> | <needed context> | <reads/probes/spike> | <decision/evidence> | <review/check> |
| 1 Build | <behavior> | <contract ready> | <tasks> | <tests pass> | <command> |
```

Rules:
- Use discovery phase for unknowns that would change architecture or scope.
- Put irreversible work after a checkpoint.
- Keep each phase shippable, reversible, or marked not shippable.
- Do not mix unrelated outcomes in one phase.

**If fails:**
- Phase has no exit criteria -> add status, test, artifact, decision, or visible proof.
- Phase depends on a later phase -> reorder or split.
- Exit criteria require unavailable signals -> use `observability-workflow`.

### Step 5: Map Dependencies, Risks, Gates, and Rollback

**Expected Output:** `risk_table=<risk/mitigation/gate>, validation=<commands>, rollback=<points>`

Every risky plan needs proof and an undo/stop path.

```markdown
| Risk | Trigger | Mitigation | Gate | Rollback |
|------|---------|------------|------|----------|
| <risk> | <when it appears> | <prevention> | <proof> | <undo/stop> |
```

Check: data loss, schema drift, auth/tenant leak, secrets, shell/destructive command, downtime, performance, compatibility, flaky tests, external service, migration order, manual steps, stale assumptions.

Validation gates must name exact evidence:

```markdown
Gate: `python -m pytest tests/path -q` -> selected tests pass.
Gate: staging health check returns 200 for `/health`.
Gate: migration dry run reports `0 destructive changes`.
```

**If fails:**
- Risk lacks mitigation -> add task or reduce scope.
- Gate says "verify manually" -> specify what to click, inspect, or observe.
- Rollback impossible -> mark high risk and require approval before execution.

### Step 6: Define Concrete Tasks and Sequencing

**Expected Output:** `tasks=<ordered checklist>, parallel=<yes|no>, commands=<with expected output>, owner=<agent|user|external>`

Tasks are execution units. They must name files, action, expected result, and verification.

Task format:

```markdown
- [ ] P1.T1 <imperative task title>
  - Files: <exact paths or "discover in P0.T1">
  - Do: <specific change or investigation>
  - Verify: `<command>` -> <expected output>
  - Depends on: <task id|none>
```

Sequencing rules:
- Write or identify tests before implementation when behavior changes.
- For migrations, stage expand -> backfill -> switch -> contract unless local pattern differs.
- Group tasks by dependency, not by file type.
- Mark parallel lanes only when they share no write targets or ordering dependency.

**If fails:**
- Task says "handle edge cases" or "add tests" -> replace with exact cases or test files.
- File path is unknown -> make discovery a task, not a guess.
- Two tasks can conflict on the same file -> sequence them or merge them.

### Step 7: Review the Plan Before Execution

**Expected Output:** `review=<pass|revise|blocked>, gaps=<list>, confidence=<low|medium|high>`

Run self-review before claiming readiness.

Review checks:
- Coverage: every requirement maps to a phase/task/gate.
- Placeholder scan: no `TBD`, `TODO`, "later", "appropriate", "etc.", "similar to".
- Consistency: task names, paths, APIs, and types agree across phases.
- Tests: success, failure, boundary, regression, and security cases exist when relevant.
- Risk: high-risk actions have rollback and gate.
- Staleness: plan matches current branch, diff, and artifact state.

```bash
rg -n "TBD|TODO|later|appropriate|etc\\.|similar to|handle edge|add tests" .
git status --short
```

**If fails:**
- Missing coverage -> add or revise tasks.
- Placeholder remains -> replace with exact action, file, command, or decision.
- Confidence is low on high-risk work -> use `cross-model-verification`.

### Step 8: Handoff Execution and Update Loop

**Expected Output:** `ready=<yes|with-assumptions|blocked>, next_action=<task id>, update_rule=<when plan changes>, residual=<risks>`

End with an executable, updateable plan.

```markdown
Objective:
Scope/non-goals:
Assumptions:
Phases:
Tasks:
Gates:
Rollback:
Open decisions:
Next action:
Status: ready=<yes|with-assumptions|blocked>
```

Update rule:

```markdown
After each gate, update: completed, evidence, changed assumptions, new risks, next action.
If a gate fails, stop execution and revise the plan before continuing.
```

**If fails:**
- Next action is vague -> pick the first task id and exact command/action.
- `ready=yes` has open blockers -> change to `ready=blocked`.
- Work is ready for code changes -> use `git-workflow-for-agents`.

## Bad/Good Planning Patterns

### Pattern 1: Milestone Without Exit Criteria

**Bad:**
```markdown
Phase 1: Build backend.
```

**Good:**
```markdown
Phase 1 exits when `POST /reports` returns 201, persists one row, and `pytest tests/reports -q` passes.
```

### Pattern 2: Risk Without Rollback

**Bad:**
```markdown
Run migration in production after tests pass.
```

**Good:**
```markdown
Run dry-run, snapshot tables, deploy expand-only schema, verify old/new callers, then switch reads.
```

### Pattern 3: Task Without Verification

**Bad:**
```markdown
- [ ] Add validation and update UI.
```

**Good:**
```markdown
- [ ] P2.T3 Add duplicate-name validation in `src/forms/project.ts`.
  - Verify: `npm test -- project-form.test.ts` -> duplicate name shows field error and submit is blocked.
```

## Rationalization Table

| Rationalization | Why it fails |
|-----------------|--------------|
| "The plan can be high level" | High-level plans hide files, tests, dependencies, and rollback. |
| "We'll figure tests out later" | Test design changes sequencing and sometimes architecture. |
| "It's just a refactor" | Refactors still break behavior, data shape, performance, and imports. |
| "Rollback is obvious" | Rollback is real only when named and possible after each gate. |
| "Discovery is not progress" | Discovery prevents committing to the wrong architecture or scope. |
| "Parallel work is faster" | Parallel tasks sharing files or assumptions conflict. |

## Red Flags

- You are planning before objective, scope, and non-goals are explicit.
- A phase has no entry criteria, exit criteria, or validation gate.
- A task lacks exact files, action, verification, or dependency.
- Plan contains `TBD`, `TODO`, "later", "appropriate", "etc.", or "similar".
- High-risk work has no rollback point.
- Migration work lacks expand/backfill/switch/contract thinking.
- Tests are deferred until after implementation without reason.
- Manual verification lacks specific observable steps.
- Plan says ready while blockers or unresolved decisions remain.

## Common Pitfalls

| Symptom | Root cause | Fix |
|---------|------------|-----|
| Plan is long but not executable | It describes themes, not tasks | Convert themes to task id, files, action, verify, dependency |
| Work starts then scope changes | Requirements were not clarified | Use `requirements-clarifier` before sequencing |
| Phase never finishes | Exit criteria are subjective | Add observable artifact, test, status, metric, or decision |
| Risk appears during execution | Dependencies and failure modes were not mapped | Add risk table before tasks |
| Rollback fails | Undo path was assumed | Define checkpoint, dry run, backup, feature flag, or revert point |
| Parallel tasks collide | Shared files or assumptions were ignored | Sequence conflicting tasks or assign one owner |
| Review rejects plan | Placeholders and unverified assumptions remain | Run Step 7 review and fix gaps before handoff |

## Verification Checklist

- [ ] Description triggers on project, roadmap, migration, refactor, release, investigation, multi-step implementation, and risky change planning.
- [ ] Objective, scope, non-goals, constraints, and unknowns are explicit.
- [ ] Evidence and work surface are inspected before sequencing.
- [ ] Plan shape and risk level are named.
- [ ] Phases have entry criteria, exit criteria, dependencies, and gates.
- [ ] Risks include mitigation, validation, and rollback.
- [ ] Tasks include exact files or discovery tasks, action, verification, and dependencies.
- [ ] Commands include expected output or manual checks name evidence.
- [ ] Placeholder scan and coverage review are complete.
- [ ] Handoff includes `ready=yes`, `ready=with-assumptions`, or `ready=blocked` and a concrete next action.

## Interaction with Other Skills

| Related Skill | Trigger | Handoff |
|---------------|---------|---------|
| **requirements-clarifier** | Goal, scope, criteria, or constraints are vague | Get build-ready contract before planning |
| **test-design-workflow** | Behavior changes need test strategy | Provide criteria, phases, risks, test surfaces |
| **systematic-debugging** | Investigation plan starts from an unreproduced failure | Reproduce and isolate before implementation tasks |
| **observability-workflow** | Gates need logs, metrics, traces, alerts, or health checks | Define signals as gates |
| **agent-security-guard** | Secrets, auth, tenant, shell, payment, privacy, or destructive actions appear | Add safety gate before execution |
| **cross-model-verification** | Plan is high-risk, disputed, or low-confidence | Request independent review of gaps and assumptions |
| **git-workflow-for-agents** | Plan execution changes files | Manage branch, staging, commits, sync, PR hygiene |
| **code-review-workflow** | Plan/implementation is ready for review | Use criteria, tasks, gates as review baseline |
