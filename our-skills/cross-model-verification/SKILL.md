---
name: cross-model-verification
description: Use when correctness matters more than speed, when working on high-stakes changes (production, security, data migration), or any time the first model's confidence feels unverified. Use when the user says "换个模型检查", "cross-model", "cross-validation", "second opinion", or "verify with another model".
---

# Cross-Model Verification

## Overview

A single model shares blind spots with itself—fresh context from a different architecture catches them. This skill orchestrates the second-opinion workflow: collect the artifact, generate an adversarial prompt, dispatch to a second model, diff the results, and report findings classified by severity.

## The Process

```
Collect → Adversarial Prompt → Dispatch → Diff → Report
   │            │                  │         │        │
   ▼            ▼                  ▼         ▼        ▼
 Artifact   "Find issues"      Which      Compare   Severity
 isolation  NOT "is it good"   model?     outputs   labels
```

### Step 1: Collect

Isolate the smallest reviewable unit. Strip your reasoning—handing over conclusions biases the reviewer toward agreement.

```
What to review?
  │
  ├── Code diff / PR → paste the diff
  ├── Architecture decision → 3-5 sentence proposal + constraints
  └── Assertion → the claim + supporting evidence (distinct from your CLAIM)
```

**Rule:** The unit must be small enough that a reviewer can hold it in one read. If it's a 500-line PR, decompose first.

### Step 2: Adversarial Prompt

Framing decides the answer. Always "find issues", never "is it good".

```
Adversarial review. Find what is wrong with this artifact.
Assume the author is overconfident. Look for:
- Unstated assumptions
- Edge cases not handled
- Hidden coupling or shared state
- Ways the contract could be violated
- Existing conventions this might break
- Failure modes under unexpected input

Do NOT validate. Do NOT summarize. Find issues, or state
explicitly that you cannot find any after thorough examination.

ARTIFACT: <paste artifact>
CONTRACT: <paste contract or constraints>
```

**Do NOT pass your CLAIM.** The reviewer must independently determine whether the artifact satisfies the contract.

### Step 3: Dispatch

```
Which model?
  │
  ├── CLI tool (gemini, codex) →
  │     ├── which gemini / which codex
  │     ├── gemini --version / codex --version
  │     ├── Confirm invocation with user
  │     └── Pipe via stdin (never inline -p with untrusted artifact)
  │
  ├── Same session model only → Degraded self-review
  │     └── 同模型不构成 cross-model，必须标记 degraded
  │
  ├── Web interface → Manual (user pastes)
  │
  └── None available → Degraded self-review
        └── Write ARTIFACT + CONTRACT as fresh self-prompt
        └── Walk Steps 1-5 with hard mental separator
        └── Flag result as degraded
```

**Shell escaping (load-bearing):** Artifacts contain `$(...)`, backticks, quotes. Inline arguments truncate or execute embedded shell.

```bash
# Write to temp file, pipe via stdin
echo "$PROMPT" > /tmp/cross-model-prompt.md
gemini --approval-mode plan -p "" < /tmp/cross-model-prompt.md

# Read-only sandbox for codex (prevents artifact injection from executing)
codex exec --sandbox read-only -C <repo-path> - < /tmp/cross-model-prompt.md
```

### Step 4: Diff

The reviewer's output is data, not verdict. You are still the orchestrator.

```
For each finding:
  ├── Contract misread? → Fix contract, re-classify
  ├── Valid + actionable? → Change it, re-loop
  ├── Valid trade-off? → Document explicitly
  └── Noise? → Note it, move on
```

### Step 5: Report

```
═══ Cross-Model Verification ═══
  模型 A: <name>
  模型 B: <name>

  发现:
  [Critical] <finding> — 必须修复
  [Required] <finding> — 建议修复
  [Optional] <finding> — 可改进
  [FYI] <finding> — 供参考

  结论: approve / request changes / needs discussion
```

## Failure / Degraded Strategy

```
Second model unavailable?
  │
  ├── CLI tool missing → Ask user to install, or use degraded
  │
  ├── Artifact too large → Decompose and review in chunks
  │
  ├── Timeout / no response → Re-dispatch with same prompt (retry once)
  │
  └── None available → Degraded self-review
        ├── Write ARTIFACT + CONTRACT as fresh self-prompt
        ├── Walk Steps 1-5 with hard mental separator
        ├── Flag result explicitly as "degraded" in output
        └── Never claim "cross-verified" if only self-reviewed
```

**Degraded self-review protocol:**
1. Close any open tabs with the artifact—you must come back cold.
2. Rewrite the adversarial prompt as a self-prompt, strip any "I found X" from it.
3. Set a 5-minute timer. If you finish early, you didn't try hard enough.
4. In the output, prefix every finding with `[degraded]` to remind downstream consumers this wasn't cross-validated.

**When to abort rather than degrade:**
- High-stakes change (production migration, security auth) AND no second model AND the artifact is > 500 lines → Escalate to human review, don't fake verification.

## When to Use

| Use When | Don't Use When |
|----------|----------------|
| 用户说"换个模型检查""cross-model""second opinion" | 简单问题不需要二次验证（如 typos、格式调整） |
| 高风险变更：production、安全、数据迁移 | 用户只是问"这个对不对"（先用自己的判断） |
| 第一个模型的输出看起来太自信但缺乏证据 | 时间紧迫、需要立即执行（cross-model 增加延迟） |
| 审查结果中的 Critical 项需要二次确认 | 唯一能用的模型和当前模型架构相同（无多样性优势） |
| coding agent 完成复杂任务后验证方案正确性 | 已有明确答案的事实性问题（如查文档） |

## Verification Checklist

- [ ] Artifact 已隔离为最小可审查单元
- [ ] Adversarial prompt 使用"find issues"而非"is it good"
- [ ] 未将个人判断或 CLAIM 传入 prompt
- [ ] 通过 stdin 传递 artifact（不使用 -p 内联参数）
- [ ] 所有发现已分类（Critical/Required/Optional/FYI）
- [ ] 结论明确：approve / request changes / needs discussion

## Interaction with Other Skills

- **skill-review-workflow**: skill-review 的审查结果可送入本 skill 做二次验证。skill-review 发现 Critical 问题时自动触发。
- **agent-security-guard**: 安全相关发现（API key、shell 注入）优先用 agent-security-guard 专项检测，本 skill 负责一般性逻辑审查。
