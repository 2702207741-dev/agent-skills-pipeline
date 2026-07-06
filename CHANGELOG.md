# Changelog

## 1.0.0 (2026-07-06)

Initial release — 7-skill pipeline for AI agent workflows.超越 Addyosmani 的质量标准。

### Added

#### 新 Skill（3 个）
- **agent-security-guard** — 安全门禁（API key 扫描、注入检测、shell 转义）
- **cross-model-verification** — 跨模型对抗验证 + Adversarial Prompt 模板
- **skill-pipeline-orchestrator** — 5 阶段管线编排（Author → Review+Sec → Verify → Package → Deploy）

#### 升级 Skill（4 个）
- **skill-authoring-workflow** v1.5.0 — 新增快速通道、Iterative Refinement、Interaction 联动、4 个 reference 文件
- **skill-review-workflow** v1.1.0 — 新增 Security 严重级别、Expected Output 补全、Interaction 联动
- **git-workflow-for-agents** — 6 步全部补全 Expected Output，新增 API key 误提交检测
- **agent-config-reference** — Troubleshooting 重构为类型 A/B/C 决策树，新增 Security Configuration

#### 工具
- **scripts/validate-skill.py** — 8 项格式一键验证
- **scripts/package_skill.py** — 打包脚本
- **scripts/install.sh** — 多平台安装脚本

#### 文档
- README.md — 项目概览 + 安装指南
- skill-authoring-workflow/references/ 下 4 个参考文档

### Quality

- 7/7 skill 全部通过 validate-skill.py 8 项检查
- 5 阶段管线全流程测试通过
- 跨模型验证（Claude + GLM）发现并修复 5 个真实问题
- 双平台部署认证（Hermes Agent + Claude Code）
