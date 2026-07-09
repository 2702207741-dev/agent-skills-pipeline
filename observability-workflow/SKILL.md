---
name: observability-workflow
description: Use when the user asks to add, design, review, or troubleshoot observability for a service, job, API, UI flow, pipeline, release, incident gap, or system and needs logs, metrics, traces, alerts, dashboards, SLOs, health checks, instrumentation, or runbooks.
version: 1.0.0
metadata:
  tags: [observability, metrics, logs, tracing, alerts]
  related_skills: [agent-security-guard, cross-model-verification, incident-retro-workflow]
---

# Observability Workflow

## Overview

Observability makes failures diagnosable before users explain them. Design signals from journeys and failure modes, then prove they fire with safe success and failure checks.

## When to Use

| Use When | Don't Use When |
|----------|----------------|
| The user says "observability", "monitoring", "metrics", "logs", "traces", "alerts", "dashboard", "SLO", "health check", or "instrumentation" | The task only fixes a known bug with no signal changes; use `systematic-debugging` |
| A service, API, job, queue, pipeline, UI flow, release, or dependency needs health or failure visibility | No running behavior or failure mode exists |
| An incident, test gap, review finding, or release plan shows missing signals | The user only wants generic definitions of logs, metrics, traces, or SLOs |
| The user asks to review alert quality, dashboard usefulness, telemetry cost, or noisy paging | The work is only acceptance-criteria clarification; use `requirements-clarifier` |
| A validation gate in a plan needs logs, metrics, traces, alerts, or manual checks | The request is a broad incident retro with no instrumentation change |

## Phase 0 Benchmark Decision

Type: Technique with safety judgment. Adopt GStack canary/benchmark habits: baseline first, compare current behavior, tie checks to user-visible health, and report degraded/broken states. Every signal needs owner, action, validation, and stale-risk handling. Omit browser, telemetry, and long-running monitors.

## Observability Gate

```
No journey or failure mode -> no signal design.
No owner/action -> no paging alert.
No privacy/cardinality review -> no log field/metric label.
No verification path -> no "observable" claim.
No runbook for urgent alert -> no production pager.
```

## The Process

```
journey -> failure -> current signals -> signal map -> privacy -> alerts -> dashboard -> proof
```

### Step 1: Name the Journey, Dependency, and Failure Mode

**Expected Output:** `target=<journey|service|job|api|ui|pipeline>, failure_modes=<list>, impact=<user|data|ops>, severity=<low|medium|high>`

Start from what must be diagnosable. Identify journey, boundary, dependency, and failure outcome before choosing tools.

```bash
git status --short
rg -n "route|handler|controller|worker|queue|cron|job|pipeline|health|retry|timeout|error" .
rg -n "incident|postmortem|retro|SLO|SLA|runbook|dashboard|alert" .
```

Failure-mode row:

```markdown
| Failure mode | User impact | Detection goal | Triage question |
|--------------|-------------|----------------|-----------------|
| <what breaks> | <who notices> | <how fast> | <first question to answer> |
```

**If fails:**
- No failure mode -> use `requirements-clarifier`.
- Bug is not understood -> use `systematic-debugging` first.
- Impact includes auth, secrets, payment, privacy, or destructive action -> use `agent-security-guard`.

### Step 2: Inventory Existing Signals and Blind Spots

**Expected Output:** `existing=<logs|metrics|traces|alerts|dashboards>, blind_spots=<list>, owners=<team|none>`

Find what exists before adding noise.

```bash
rg -n "logger|log\\.|console\\.|metric|counter|histogram|gauge|statsd|prometheus|otel|OpenTelemetry|span|trace|health|ready|live|alert|dashboard|runbook" .
rg --files | rg "grafana|prometheus|datadog|newrelic|opentelemetry|otel|alert|dashboard|runbook|slo|monitor"
```

Inventory table:

```markdown
| Signal | Location | What it proves | Gap |
|--------|----------|----------------|-----|
| <log/metric/span/alert> | <file/tool> | <diagnostic value> | <missing context> |
```

**If fails:**
- No existing signals -> design minimal signals around the critical failure mode.
- Too many signals -> keep those tied to triage questions.
- No owner -> mark alerts dashboard-only until owner exists.

### Step 3: Build the Signal Map

**Expected Output:** `signal_map=<failure->log/metric/trace/health>, coverage=<success|failure|latency|saturation>`

Map each failure mode to the smallest useful signal set.

| Need to know | Prefer | Notes |
|--------------|--------|-------|
| What happened once | Structured log | Stable identifiers and error class |
| How often/how bad | Metric | Counter, histogram, gauge, or ratio |
| Where time went | Trace/span | Propagate correlation and spans |
| Is it up now | Health check | Separate liveness from readiness |
| Should someone act | Alert | Tie to impact, SLO burn, or durable symptom |
| What to inspect | Dashboard | Order by triage flow |

Signal row:

```markdown
| Failure mode | Log | Metric | Trace/span | Health | Alert | Dashboard |
|--------------|-----|--------|------------|--------|-------|-----------|
```

**If fails:**
- Signal answers no triage question -> remove it.
- Duplicate signal -> keep cheaper or clearer one.
- Failure needs user-visible proof -> add synthetic/manual check.

### Step 4: Design Logs with Privacy and Cardinality Controls

**Expected Output:** `logs=<events>, fields=<safe fields>, redactions=<list>, correlation=<request_id|trace_id|job_id>`

Logs explain decisions, not payloads.

Log event format:

```markdown
event=<stable_name>
level=<info|warn|error>
fields=<request_id, actor_id_hash, resource_id, status, duration_ms, error_class>
redact=<tokens, secrets, raw email, payload, PII>
sample=<none|rate|error-only>
```

Guardrails:
- Use stable event names.
- Include correlation IDs.
- Log error class and safe identifiers, not secrets or payloads.
- Avoid high-cardinality fields: raw URL, email, stack label, query text, unbounded exception.

**If fails:**
- Log contains secrets/PII -> remove or hash before emitting.
- Field cardinality is unbounded -> bucket, hash, or keep out of metric labels.
- Unknown volume -> sample success logs and keep error logs.

### Step 5: Design Metrics, SLOs, and Alerts

**Expected Output:** `metrics=<name/type/labels>, slo=<objective|none>, alerts=<condition/owner/action>`

Metrics quantify user impact and system health. Use RED for requests, USE for resources, and domain metrics for jobs/business flows.

Metric table:

```markdown
| Metric | Type | Labels | Why | Alert? |
|--------|------|--------|-----|--------|
| <name> | counter/histogram/gauge | <bounded labels> | <question answered> | <yes/no> |
```

Alert rule:

```markdown
Alert: <condition>
Pages when: <user impact or SLO burn>
Owner: <team/person>
Action: <runbook step>
Silence when: <maintenance/deploy/test>
```

Prefer:
- Error ratio over raw error count.
- Latency percentile plus request volume.
- Queue age over queue depth alone.
- SLO burn or sustained impact over one-sample spikes.

**If fails:**
- Alert has no owner/action -> make it dashboard-only.
- Threshold is guessed -> start with dashboard/baseline, not pager.
- Metric labels are unbounded -> redesign before shipping.

### Step 6: Design Traces, Dashboards, and Runbooks

**Expected Output:** `triage_flow=<ordered questions>, dashboard=<panels>, runbook=<actions>, trace_links=<correlation>`

Dashboards answer triage questions in order. Traces connect request/job paths.

Triage order:

```markdown
1. Is the user journey failing?
2. Which dependency or phase is failing?
3. Is it errors, latency, saturation, or data correctness?
4. What changed recently?
5. What action or rollback is recommended?
```

Dashboard outline:

```markdown
| Panel | Query/source | Answers | Drilldown |
|-------|--------------|---------|-----------|
| <panel> | <metric/log/trace> | <question> | <link/runbook> |
```

**If fails:**
- Dashboard is a wall of graphs -> reorder around triage flow.
- Trace lacks request/job correlation -> add propagation task.
- Runbook says "investigate" -> add checks and rollback/escalation.

### Step 7: Verify Signals with Success and Failure Paths

**Expected Output:** `verification=<commands|manual>, success_signal=<observed>, failure_signal=<observed>, gaps=<residual>`

A signal is not done until observed. Verify one success and one safe failure path.

```bash
rg -n "health|ready|live|metrics|trace|logger|alert|dashboard" .
```

Verification table:

```markdown
| Scenario | Action | Expected signal | Evidence |
|----------|--------|-----------------|----------|
| Success | <command/manual step> | <metric/log/span/panel> | <observed output> |
| Failure | <safe injected failure> | <alert/log/error metric> | <observed output> |
```

**If fails:**
- Failure injection is unsafe -> use staging, test double, dry run, or gap note.
- Signal does not appear -> fix instrumentation before claiming coverage.
- Alert fires but action is unclear -> revise alert text/runbook.

### Step 8: Handoff the Observability Contract

**Expected Output:** `ready=<yes|with-gaps|blocked>, contract=<signals/alerts/dashboards/runbooks>, residual=<risks>`

Finish with a contract implementers and responders can use.

```markdown
Target:
Failure modes:
Signals:
Privacy/cardinality controls:
Alerts:
Dashboards:
Runbooks:
Verification:
Residual gaps:
Status: ready=<yes|with-gaps|blocked>
```

Ready states:

| State | Meaning |
|-------|---------|
| `ready=yes` | Signals are designed and verification exists |
| `ready=with-gaps` | Gaps are explicit and non-blocking |
| `ready=blocked` | Missing owner, privacy approval, safe test, or failure-mode definition |

**If fails:**
- Contract lacks verification -> return to Step 7.
- Paging alert lacks owner/runbook -> downgrade or mark blocked.
- Work is multi-step -> use `planning-workflow` to sequence implementation.

## Bad/Good Observability Patterns

### Pattern 1: Log Everything

**Bad:**
```markdown
Log full request and response payload for every checkout failure.
```

**Good:**
```markdown
Log `checkout_payment_failed` with request_id, order_id, provider, error_class, duration_ms, redacted actor_id.
```

### Pattern 2: Noisy Alert

**Bad:**
```markdown
Page when CPU is above 80% for one minute.
```

**Good:**
```markdown
Page when checkout error ratio exceeds 5% for 10 minutes and volume is above baseline; link rollback runbook.
```

### Pattern 3: Dashboard Wall

**Bad:**
```markdown
One dashboard with every service metric, no order.
```

**Good:**
```markdown
Panels ordered by triage: user failures, dependencies, latency, saturation, deploys, runbooks.
```

## Rationalization Table

| Rationalization | Why it fails |
|-----------------|--------------|
| "More logs are always better" | More logs create cost, privacy risk, and search noise. |
| "We'll tune alerts later" | Untuned alerts train responders to ignore pages. |
| "Dashboards are enough" | Dashboards do not wake an owner or explain action. |
| "Metrics prove everything" | Metrics show shape; logs and traces explain cases. |
| "This is internal only" | Internal telemetry can still leak secrets or user data. |
| "Manual checks are fine" | Manual checks must name steps and expected evidence. |

## Red Flags

- You add signals before naming failure modes and triage questions.
- Logs include raw payloads, tokens, emails, secrets, or unbounded error text.
- Metric labels include user id, raw URL, query text, exception message, or request id.
- Alert has no owner, runbook, action, or user-impact condition.
- Dashboard panels are ordered by data source instead of triage flow.
- Health check mixes liveness, readiness, and dependency correctness.
- You cannot simulate or observe success and failure signals.
- You claim an SLO without objective, window, source, and burn action.
- Instrumentation can fail silently because no test or smoke check covers it.

## Common Pitfalls

| Symptom | Root cause | Fix |
|---------|------------|-----|
| Logs are noisy and risky | Payloads and ad hoc messages replaced event design | Use stable events, safe fields, redaction, sampling |
| Metrics explode in cost | Labels have unbounded cardinality | Bound, bucket, hash, or remove labels |
| Alerts wake people for non-actionable symptoms | Condition is not tied to impact or ownership | Use SLO burn, sustained impact, owner, runbook |
| Dashboard cannot guide triage | Panels are grouped by source, not question | Reorder by impact, dependency, error, latency, saturation, change |
| Trace is incomplete | Correlation IDs are not propagated across boundaries | Add request/job/trace propagation and link logs to spans |
| Health check is misleading | Liveness, readiness, and dependency checks are mixed | Split checks and document what each proves |
| Incident repeats with no signal | Verification never injected safe failure | Add success/failure signal checks before closing |

## Verification Checklist

- [ ] Trigger scope covers logs, metrics, traces, alerts, dashboards, SLOs, health checks, instrumentation, runbooks.
- [ ] Critical journeys, dependencies, and failure modes are named.
- [ ] Existing signals and blind spots were inventoried.
- [ ] Signal map covers success, failure, latency, saturation, and dependency visibility.
- [ ] Logs have stable event names, safe fields, redaction, sampling, and correlation IDs.
- [ ] Metrics use correct type and bounded labels.
- [ ] Alerts tie to user impact, SLO burn, owner, action, and runbook.
- [ ] Dashboards answer triage questions in order.
- [ ] Health checks distinguish liveness, readiness, and dependency correctness.
- [ ] Success/failure paths have evidence or explicit residual gaps.

## Interaction with Other Skills

| Related Skill | Trigger | Handoff |
|---------------|---------|---------|
| **planning-workflow** | Work spans phases, services, or rollout gates | Sequence discovery, instrumentation, verification, release |
| **test-design-workflow** | Signals need automated or manual test cases | Convert success/failure signals into test cases |
| **systematic-debugging** | Failure mode is unknown or unreproduced | Reproduce and isolate before signal design |
| **incident-retro-workflow** | Incident showed missing or noisy signals | Convert actions into concrete observability changes |
| **agent-security-guard** | Telemetry may expose secrets, PII, auth, tenant, payment, shell, or destructive data | Review redaction and safety |
| **code-review-workflow** | Reviewing instrumentation diff quality | Check signal usefulness, privacy, cardinality, and tests |
| **cross-model-verification** | Design is high-risk or disputed | Ask for adversarial review of blind spots |
| **requirements-clarifier** | Journey, owner, SLO, or failure mode is vague | Clarify before design |
