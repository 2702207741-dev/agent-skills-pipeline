---
name: incident-retro-workflow
description: Use when the user asks to write, review, analyze, or improve an incident retro, postmortem, outage review, rollback review, timeline, impact summary, RCA, factor analysis, or corrective action plan after an incident, customer-impacting bug, deploy failure, data issue, or security-adjacent event.
version: 1.0.0
metadata:
  tags: [incident, retrospective, postmortem, reliability]
  related_skills: [agent-security-guard, cross-model-verification]
---

# Incident Retro Workflow

## Overview

Incident retros turn painful evidence into safer systems. Build a sourced timeline, quantify impact, separate triggers from factors, and create verified actions that reduce recurrence, detection time, or response time.

## When to Use

| Use When | Don't Use When |
|----------|----------------|
| The user says "incident retro", "postmortem", "outage review", "rollback review", "RCA", "timeline", or "corrective actions" | The incident is still active and needs mitigation |
| An incident, customer-impacting bug, deploy failure, data issue, or reliability regression needs analysis | A bug has no reproduction or root-cause evidence; use `systematic-debugging` |
| Alerts, logs, tickets, deploys, traces, metrics, or chat need to become a factual retro | No artifact, timeline, symptom, or affected behavior exists |
| Follow-up work needs owners, dates, verification, and risk reduction | The task only adds telemetry; use `observability-workflow` |
| A draft retro needs review for blame, unsupported claims, weak actions, or missing impact | Security, privacy, tenant, abuse, or legal exposure lacks review |

## Phase 0 Benchmark Decision

Type: Technique with safety judgment. Use blameless habits: facts before interpretation, explicit uncertainty, impact before causes, people-neutral language, and evidence-tied actions.

## Retro Gate

```
Incident active -> no final retro.
No evidence or timeline -> no root-cause claim.
Person-blame language -> rewrite to system/process factors.
No owner/date/verification -> invalid action item.
Security/privacy/legal exposure -> use agent-security-guard.
```

## The Process

```
stabilize -> evidence -> timeline -> impact -> factors -> actions -> review -> handoff
```

### Step 1: Confirm Stabilization, Scope, and Retro Mode

**Expected Output:** `status=<resolved|mitigated|ongoing>, incident=<name>, severity=<sev>, scope=<systems/users/time>, retro_mode=<draft|final|blocked>`

Confirm whether the system is restored, mitigated, or still failing. Name the incident, window, affected systems, audience, and draft/final mode.

```bash
git status --short
rg -n "incident|outage|rollback|postmortem|retro|SEV|severity|customer impact|data loss|deploy|runbook|mitigation|resolved" .
```

Record:

```markdown
Incident:
Status:
Start/end:
Affected systems/users:
Retro mode:
```

**If fails:**
- `status=ongoing` -> stop final retro work; produce a containment note.
- Scope is unclear -> ask for start time, end time, affected system, and user impact.
- Security, privacy, tenant, abuse, legal, or personnel-sensitive facts appear -> use `agent-security-guard`.

### Step 2: Collect Evidence and Label Confidence

**Expected Output:** `evidence=<logs|metrics|traces|tickets|deploys|chat>, gaps=<list>, confidence=<low|medium|high>`

Collect primary artifacts first: alerts, metrics, traces, logs, deploy records, channel timestamps, tickets, status updates, runbooks, commits, and customer reports.

```bash
rg -n "error|timeout|exception|rollback|deploy|migration|alert|SLO|SLA|health|metric|trace|log|status page|customer report" .
git log --oneline --decorate -n 30
git diff --name-status
```

Evidence table:

```markdown
| Evidence | Source | Timezone | Proves | Confidence |
|----------|--------|----------|--------|------------|
```

**If fails:**
- Only anecdotes exist -> mark `confidence=low`; do not claim root cause.
- Evidence conflicts -> keep both versions with source and timestamp.
- Artifacts contain secrets, PII, customer data, or personnel data -> redact before quoting.

### Step 3: Build a Factual Timeline

**Expected Output:** `timeline=<ordered events>, detection=<source>, mitigation=<action>, resolution=<time>, unknowns=<list>`

Use absolute timestamps with timezone. Separate detection, acknowledgement, diagnosis, mitigation, recovery, customer communication, and post-recovery checks.

```markdown
| Time | Event | Source | Confidence |
|------|-------|--------|------------|
```

Rules:
- Include `detected`, `acknowledged`, `mitigation started`, `mitigated`, `resolved`, and `verified`.
- Label inference as inference.
- Keep unknown time ranges visible.

**If fails:**
- Times lack timezone -> ask or label timezone as unknown.
- Events are out of order -> sort by absolute time and preserve source timestamps.
- Detection or resolution is missing -> add an open question instead of smoothing the narrative.

### Step 4: Quantify Impact and Blast Radius

**Expected Output:** `impact=<users/systems/data/business>, duration=<start/end>, severity=<label>, blast_radius=<scope>`

Quantify user harm, data correctness, availability, latency, toil, support load, SLA/SLO effect, and communications. Do not invent numbers.

```markdown
| Dimension | Value | Evidence | Notes |
|-----------|-------|----------|-------|
| Users affected | <count/percent/unknown> | <source> | <segment> |
| Duration | <start-end> | <source> | <impact window> |
| Data impact | <none/loss/corruption/delay/unknown> | <source> | <status> |
| Business/SLO impact | <value/unknown> | <source> | <breach/no breach> |
```

**If fails:**
- Impact is unknown -> state the missing artifact that would prove it.
- Severity label conflicts with measured impact -> use measured impact and note mismatch.
- Data loss, privacy, payment, auth, tenant, or destructive action appears -> use `agent-security-guard`.

### Step 5: Identify Triggers and Contributing Factors

**Expected Output:** `factors=<trigger|latent|detection|response|process|test|observability>, root_cause_claim=<supported|unsupported|not_single>`

Prefer contributing factors over a single root cause unless evidence proves one dominant cause.

| Category | Question |
|----------|----------|
| Trigger | What changed or happened immediately before impact? |
| Latent condition | What existing weakness made the trigger harmful? |
| Guardrail gap | What test, review, deploy gate, flag, or rollback missed it? |
| Detection gap | Why was it detected then, not earlier? |
| Response gap | What slowed mitigation, communication, or recovery? |
| Ownership gap | What unclear owner, doc, or decision path mattered? |

```markdown
| Factor | Category | Evidence | Link to impact | Confidence |
|--------|----------|----------|----------------|------------|
```

**If fails:**
- Explanation says "human error" -> rewrite as the system/process condition that allowed the action.
- Cause is asserted without evidence -> demote to hypothesis and add an open question.
- Factors point to missing tests or signals -> use `test-design-workflow` or `observability-workflow`.

### Step 6: Create Corrective Actions with Verification

**Expected Output:** `actions=<owner/due/verification>, prevention=<list>, detection=<list>, response=<list>, residual_risk=<list>`

Every action must reduce recurrence, detection time, impact, or response time. Each needs owner, due date, linked factor, and closure proof.

```markdown
| ID | Action | Type | Owner | Due | Verify | Linked factor |
|----|--------|------|-------|-----|--------|---------------|
```

Action rules:
- Use concrete verbs: add, remove, block, alert, test, document, migrate, rehearse, automate.
- Verify with a test, alert evidence, dashboard query, runbook link, deploy check, review evidence, or dry run.
- Track residual risk when action is deferred.

**If fails:**
- Action has no owner, due date, or verification -> mark invalid and revise.
- Action says "improve monitoring", "add tests", or "document better" -> convert to exact signal, case, file, runbook, or gate.
- Action spans teams, releases, or risky sequencing -> use `planning-workflow`.

### Step 7: Review the Retro for Quality and Safety

**Expected Output:** `review=<pass|revise|blocked>, gaps=<list>, safety=<clear|needs-redaction>, confidence=<low|medium|high>`

Review before publication. The draft must be factual, blameless, specific, and actionable.

```bash
rg -n "blame|fault|careless|negligent|human error|TBD|TODO|unknown|probably|obvious|just add|monitoring later|add tests" .
```

Checks:
- Timeline has sources, timestamps, timezone, and unknowns.
- Impact is quantified or explicitly unknown.
- Trigger, symptom, factors, and root-cause claims are separated.
- People are not blame anchors.
- Actions link to factors and have owner, due date, and verification.
- Sensitive data is redacted; open questions are separate from conclusions.

**If fails:**
- Blame language remains -> rewrite around system condition, decision context, guardrail, or process gap.
- Unsupported certainty remains -> lower confidence or add evidence.
- Sensitive facts remain -> redact or route through `agent-security-guard`.

### Step 8: Handoff Follow-up and Learning Loop

**Expected Output:** `status=<ready|with-gaps|blocked>, retro=<summary>, follow_up=<tracking plan>, next_skill=<none|planning|observability|testing|debugging>`

Finish with a publishable retro and trackable follow-up.

```markdown
Incident:
Status:
Impact:
Timeline:
Contributing factors:
What went well:
What went poorly:
Corrective actions:
Open questions:
Residual risk:
Follow-up:
Status: ready=<ready|with-gaps|blocked>
```

| State | Meaning |
|-------|---------|
| `ready` | Evidence, timeline, impact, factors, actions, and safety review are complete |
| `with-gaps` | Unknowns or residual risks are explicit and non-blocking |
| `blocked` | Missing evidence, active incident, unsafe disclosure, or invalid actions blocks publication |

**If fails:**
- Follow-up is not trackable -> add owners, dates, and verification artifacts.
- `ready` has open blockers -> downgrade to `with-gaps` or `blocked`.
- Actions need implementation sequencing -> use `planning-workflow`.

## Bad/Good Retro Patterns

### Pattern 1: Person Blame

**Bad:** `The deployer forgot to update config, causing the outage.`

**Good:** `The deploy path allowed config/code drift; no preflight check blocked the incompatible pair.`

### Pattern 2: Unsupported Root Cause

**Bad:** `Root cause: database overload.`

**Good:** `Contributing factor: checkout queries exceeded the pool after migration increased per-request queries from 2 to 9.`

### Pattern 3: Weak Action Item

**Bad:** `Add monitoring and more tests.`

**Good:** `A2: Add checkout 5xx ratio alert, owner=Payments, due=2026-07-15, verify=staging failure injection plus alert evidence.`

## Rationalization Table

| Rationalization | Why it fails |
|-----------------|--------------|
| "We already know what happened" | Memory loses timestamps, impact, uncertainty, and context. |
| "It was human error" | Human error names a symptom; prevention needs system factors. |
| "No customer complained" | Lack of reports is not proof of no impact. |
| "Just add monitoring" | Monitoring without owner, threshold, runbook, and test is noise. |
| "Action items can be broad" | Broad actions do not close because verification is undefined. |

## Red Flags

- You write the story before collecting artifacts.
- Timeline events lack timezone, source, or confidence.
- Impact says "minimal" or "no customer impact" without evidence.
- Root cause is a person, team, deploy, or tool with no latent factor.
- Actions lack owner, due date, verification, or linked factor.
- Actions target prevention but ignore detection, mitigation, and response.
- Open questions are hidden inside conclusions.
- Sensitive customer, security, personnel, or legal facts appear in the draft.

## Common Pitfalls

| Symptom | Root cause | Fix |
|---------|------------|-----|
| Retro reads like a story | Narrative was written before artifacts | Build the evidence table and timeline first |
| Team argues about root cause | Trigger, latent condition, and factors were collapsed | Split factors by category and evidence |
| Action items never close | Owner, due date, and verification were omitted | Reject actions without all three |
| Same incident repeats | Actions targeted symptoms, not guardrails | Link each action to a factor and risk reduction |
| Blame hides useful facts | Person-centered language makes disclosure unsafe | Rewrite around system condition and missing guardrail |
| No-impact claim is disputed | Impact was not reconciled | Compare metrics, tickets, status updates, and reports |

## Verification Checklist

- [ ] Description triggers on retros, postmortems, outage reviews, rollback reviews, timelines, RCA, and corrective actions.
- [ ] Incident status, scope, severity, time window, and retro mode are explicit.
- [ ] Evidence lists sources, timestamps/timezone, facts proved, gaps, and confidence.
- [ ] Timeline includes detection, acknowledgement, mitigation, resolution, verification, and unknowns.
- [ ] Impact quantifies users/systems/data/business/SLO or states exactly what is unknown.
- [ ] Symptoms, trigger, factors, and root-cause claims are separated.
- [ ] Language is blameless and avoids person-centered blame.
- [ ] Actions have owner, due date, verification, linked factor, and action type.
- [ ] Sensitive information is redacted or routed through `agent-security-guard`.
- [ ] Final status is `ready`, `with-gaps`, or `blocked` with residual risk named.

## Interaction with Other Skills

| Related Skill | Trigger | Handoff |
|---------------|---------|---------|
| **systematic-debugging** | Root cause is unknown or speculative | Reproduce and isolate before final claims |
| **observability-workflow** | Missing signals or runbooks contributed | Convert detection/triage gaps into signal design |
| **planning-workflow** | Actions span teams, releases, or risky sequencing | Turn actions into phases, gates, rollback, and owners |
| **test-design-workflow** | Missing tests or weak regression coverage contributed | Design success, failure, boundary, and regression tests |
| **code-review-workflow** | Review missed the failure or follow-up diff needs review | Audit guardrails, tests, rollback, and signals |
| **agent-security-guard** | Security, privacy, tenant, payment, secrets, legal, or destructive boundaries appear | Redact and safety-review before publishing |
| **cross-model-verification** | Findings are high-risk, disputed, or low-confidence | Review missing factors and weak actions |
| **requirements-clarifier** | Scope, impact, ownership, or closure criteria are vague | Clarify outcome and acceptance criteria |
