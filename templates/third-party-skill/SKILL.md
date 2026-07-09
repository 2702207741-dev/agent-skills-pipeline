---
name: third-party-example-skill
description: Use this template when proposing a portable third-party skill with documented triggers, safe execution rules, examples, and verification evidence.
version: 0.1.0
---

# Third-Party Example Skill

## When to Use

Use this skill when the user request clearly matches the trigger described in the frontmatter and the required resources are available.

## Workflow

1. Confirm the request matches the documented trigger.
2. Read only the resources needed for the task.
3. Follow the safest documented execution path.
4. Produce a concise result with evidence and known limits.

## Safety

- Do not expose secrets.
- Do not run destructive commands without an explicit safety gate.
- Do not send private context to external services unless the skill declares that behavior and the user approves.

## Verification Checklist

- Frontmatter name, description, and version are valid.
- The skill has at least one success, failure, and boundary example.
- `python scripts/review_bot.py --all --check` passes.
