# Ecosystem Review Checklist

Use this checklist for first-party and third-party skill changes.

## Required Gates

- Registry and frontmatter are synchronized.
- Skill format validation passes.
- Fixture and replay coverage include success, failure, and boundary cases.
- Security scan passes with no unreviewed secrets or dangerous commands.
- Graph report has no isolated skills, hard cycles, or missing stages.
- Marketplace index and quality dashboard are current.
- Multi-model replay evaluation is current.
- Marketplace doctor passes after install.

## Contribution Review

- The skill has a clear owner and lifecycle status.
- The trigger description is precise and does not leak workflow procedure.
- External network use, destructive actions, and data handling are documented.
- Examples are safe to replay.
- Migration notes exist for deprecated or replaced behavior.

## Reviewer Decision

Approve only when all automated gates pass and the manual safety review finds no unresolved high-risk behavior.
