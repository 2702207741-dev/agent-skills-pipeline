---
name: case-studies
description: 10-skill benchmark data from skill-authoring-workflow cross-model validation. Quality Scorecard calibration baseline for future skill scoring. Not a skill — internal reference only.
---

# Case Studies — 10-Skill Benchmark

> 10 个 skill 的实战数据，作为 Quality Scorecard 评分校准基准。
> 来源：skill-authoring-workflow 的 4 轮压测（#1-#4）+ 用户指定 5 个新方向（#5-#9）+ #10 补充。

---

## 汇总总览

| # | Skill | 类型 | 风格 | 得分 | 大小 | 压测方向 |
|---|-------|------|------|------|------|---------|
| 1 | hermes-category-reference | Reference | 快速通道 | 42/50 | 8.7K | 快速通道·分类一致性 |
| 2 | context-read-first | Discipline | 完整 6 阶段 | 45/50 | 6.3K | Iron Law 操作阻断型 |
| 3 | convert-video-to-gif | Technique | Addyosmani | 49/50 | 9.2K | 跨平台 OS 差异 |
| 4 | debug-stuck-python | Technique | Addyosmani | 49/50 | 8.9K | 多分支决策树 |
| 5 | python-test-selection | Pattern | 完整 6 阶段 | 46/50 | 14.0K | Pattern 模型·首次填充 |
| 6 | conventional-commits-reference | Reference | 快速通道 | 42/50 | 6.0K | Reference 模型·一致性 |
| 7 | env-file-security | Discipline | 完整 6 阶段 | 48/50 | 8.5K | Iron Law 检测阻断型 |
| 8 | rest-api-design | Pattern | 完整 6 阶段 | 46/50 | 14.5K | Pattern·Worked Examples 双视角 |
| 9 | prompt-injection-defense | Technique | Addyosmani | 45/50 | 8.0K | 安全类 Discipline vs Technique |
| 10 | cg-extraction-workflow | Technique | 完整 6 阶段 | 42/50 | 9.3K | 引擎识别·多分支 |

**均值：44.7/50 | 中位数：46/50 | 范围：42-49**

---

## 类型一致性

| 类型 | 次数 | 得分范围 | 均值 | 一致性 |
|------|------|---------|------|--------|
| Reference | 2 | 42-42 | 42 | ±0 完全一致 |
| Pattern | 2 | 46-46 | 46 | ±0 完全一致 |
| Discipline | 2 | 45-48 | 46.5 | ±3 基本一致 |
| Technique | 4 | 42-49 | 46.3 | ±7 最分散 |

**结论：** Reference 和 Pattern 得分完全一致——模板结构约束力最强。Technique 波动最大——结构差异天然大（教做不同的事）。

---

## 风格选择准确率

| 风格 | 触发次数 | 正确率 | 误判 |
|------|---------|--------|------|
| Hermes 原生（5 字段） | 6 | 100% | 0 |
| Addyosmani 极简（2 字段） | 3 | 100% | 0 |
| 快速通道 | 2 | 100% | 0 |

**结论：** 11 次分类/风格决策，0 次错误。Phase 0 决策树稳定。

---

## 修正后的 Token Budget（10 次实测）

| 类型 | 原定目标 | 实测均值 | 建议调整 | 证据 |
|------|---------|---------|---------|------|
| Reference | 2-10K | 7.4K | 5-10K | #1 8.7K + #6 6.0K |
| Discipline | 4-8K | 7.9K | 5-10K | #2 6.3K + #7 8.5K |
| Technique | 5-12K | 8.8K | 5-12K | #3 9.2K + #4 8.9K + #9 8.0K + #10 9.3K |
| Pattern | 3-8K | 14.3K | **8-14K** | #5 14.0K + #8 14.5K |

**Pattern 修正原因：** Recognition Guide + 四维度框架 + ≥2 完整 Worked Examples（含代码）+ 6 条 Boundary Conditions = 至少 12K。原 3-8K 目标不可能达到。

---

## 发现：Discipline 子模式

| 子模式 | Iron Law 句式 | 示例 |
|--------|-------------|------|
| **操作阻断型** | `"操作前没通过X → 不执行Y"` | agent-security-guard |
| **检测阻断型** | `"X 出现在状态中 → 阻断Y"` | env-file-security, context-read-first |

两种子模式 Iron Law 句式都适配，不需要额外模板。

---

## 发现：安全类 Discipline vs Technique

| | Discipline | Technique |
|--|------------|-----------|
| agent-security-guard | ✅ | |
| env-file-security | ✅ | |
| context-read-first | ✅ | |
| prompt-injection-defense | | ✅ |

**区分规则可靠：** "禁止/阻断/不X就不Y" → Discipline；"怎么检测/怎么防御/教" → Technique。

---

## Conciseness 维度修正

| 类型 | 当前 1-5 分标准 | 修正后标准 |
|------|--------------|-----------|
| Reference | <3K/3K-5K/5K-10K/10K-15K/>15K | <5K/5K-7K/7K-10K/10K-12K/>12K |
| Discipline | <3K/3K-5K/5K-10K/10K-15K/>15K | <5K/5K-7K/7K-10K/10K-12K/>12K |
| Technique | <3K/3K-5K/5K-10K/10K-15K/>15K | 保持不变（实测 8.8K 均值） |
| Pattern | <3K/3K-5K/5K-10K/10K-15K/>15K | <8K/8K-10K/10K-14K/>16K |

---

## 关键发现

1. **Reference/Pattern 得分一致性**：同类型得分完全一致，模板结构约束力强
2. **Technique 评分最大不确定性**：结构差异大，建议增加 Technique 子类型评分标准
3. **Discipline 子模式已确认**：操作阻断型 vs 检测阻断型，Iron Law 句式通用
4. **Conciseness 维度需要类型适配**：一刀切的评分标准导致 Pattern 类持续低分
5. **Quality Scorecard 总分 42-49 之间**，没有低于 40 的，说明基准偏宽松
