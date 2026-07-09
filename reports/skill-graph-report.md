# Skill Graph Report: v3.0.0

- Nodes: 14
- Edges: 39
- Isolated skills: none
- Hard cycles: 0
- Missing stages: none

```mermaid
graph TD
  skill_authoring_workflow["skill authoring workflow"]
  skill_review_workflow["skill review workflow"]
  agent_security_guard["agent security guard"]
  cross_model_verification["cross model verification"]
  skill_pipeline_orchestrator["skill pipeline orchestrator"]
  git_workflow_for_agents["git workflow for agents"]
  agent_config_reference["agent config reference"]
  code_review_workflow["code review workflow"]
  systematic_debugging["systematic debugging"]
  test_design_workflow["test design workflow"]
  requirements_clarifier["requirements clarifier"]
  planning_workflow["planning workflow"]
  observability_workflow["observability workflow"]
  incident_retro_workflow["incident retro workflow"]
  skill_review_workflow -->|hard| skill_authoring_workflow
  agent_security_guard -->|hard| skill_review_workflow
  skill_pipeline_orchestrator -->|hard| agent_config_reference
  skill_pipeline_orchestrator -->|hard| agent_security_guard
  skill_pipeline_orchestrator -->|hard| cross_model_verification
  skill_pipeline_orchestrator -->|hard| git_workflow_for_agents
  skill_pipeline_orchestrator -->|hard| skill_authoring_workflow
  skill_pipeline_orchestrator -->|hard| skill_review_workflow
  agent_config_reference -->|hard| skill_authoring_workflow
  code_review_workflow -->|hard| agent_security_guard
  code_review_workflow -->|hard| cross_model_verification
  code_review_workflow -->|hard| git_workflow_for_agents
  code_review_workflow -->|hard| systematic_debugging
  code_review_workflow -->|hard| test_design_workflow
  systematic_debugging -->|hard| agent_security_guard
  systematic_debugging -->|hard| cross_model_verification
  systematic_debugging -->|hard| incident_retro_workflow
  systematic_debugging -->|hard| observability_workflow
  test_design_workflow -->|hard| agent_security_guard
  test_design_workflow -->|hard| cross_model_verification
  test_design_workflow -->|hard| observability_workflow
  test_design_workflow -->|hard| requirements_clarifier
  requirements_clarifier -->|hard| agent_security_guard
  requirements_clarifier -->|hard| cross_model_verification
  requirements_clarifier -->|hard| observability_workflow
  planning_workflow -->|hard| agent_security_guard
  planning_workflow -->|hard| cross_model_verification
  planning_workflow -->|hard| git_workflow_for_agents
  planning_workflow -->|hard| observability_workflow
  observability_workflow -->|hard| agent_security_guard
  observability_workflow -->|hard| cross_model_verification
  observability_workflow -->|hard| incident_retro_workflow
  incident_retro_workflow -->|hard| agent_security_guard
  incident_retro_workflow -->|hard| cross_model_verification
```

| Skill | Stages | Dependencies | Dependents | Risk |
|---|---|---|---|---|
| skill-authoring-workflow | author | none | agent-config-reference, skill-pipeline-orchestrator, skill-review-workflow | low |
| skill-review-workflow | review | skill-authoring-workflow | agent-security-guard, skill-pipeline-orchestrator | low |
| agent-security-guard | security | skill-review-workflow | code-review-workflow, incident-retro-workflow, observability-workflow, planning-workflow, requirements-clarifier, skill-pipeline-orchestrator, systematic-debugging, test-design-workflow | low |
| cross-model-verification | verify | none | code-review-workflow, incident-retro-workflow, observability-workflow, planning-workflow, requirements-clarifier, skill-pipeline-orchestrator, systematic-debugging, test-design-workflow | low |
| skill-pipeline-orchestrator | package, deploy | agent-config-reference, agent-security-guard, cross-model-verification, git-workflow-for-agents, skill-authoring-workflow, skill-review-workflow | none | low |
| git-workflow-for-agents | git | none | code-review-workflow, planning-workflow, skill-pipeline-orchestrator | low |
| agent-config-reference | configure | skill-authoring-workflow | skill-pipeline-orchestrator | low |
| code-review-workflow | code-review | agent-security-guard, cross-model-verification, git-workflow-for-agents, systematic-debugging, test-design-workflow | none | low |
| systematic-debugging | debugging | agent-security-guard, cross-model-verification, incident-retro-workflow, observability-workflow | code-review-workflow | low |
| test-design-workflow | testing | agent-security-guard, cross-model-verification, observability-workflow, requirements-clarifier | code-review-workflow | low |
| requirements-clarifier | requirements | agent-security-guard, cross-model-verification, observability-workflow | test-design-workflow | low |
| planning-workflow | planning | agent-security-guard, cross-model-verification, git-workflow-for-agents, observability-workflow | none | low |
| observability-workflow | observability | agent-security-guard, cross-model-verification, incident-retro-workflow | planning-workflow, requirements-clarifier, systematic-debugging, test-design-workflow | low |
| incident-retro-workflow | incident-retro | agent-security-guard, cross-model-verification | observability-workflow, systematic-debugging | low |
