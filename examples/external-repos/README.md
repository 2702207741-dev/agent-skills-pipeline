# External Repository Examples

These directories are verified consumer fixtures. They demonstrate integration
shape without claiming that an unrelated maintainer has adopted the project.

| Example | Skills | Gate | Purpose |
|---|---:|---|---|
| [`python-library`](python-library/) | 1 | quality + release | Minimal OSS library with a repository-owned review skill and pinned workflow |

Every example is copied into a fresh temporary directory by
`scripts/check_external_adoption.py`. The test runs the portable gate, verifies
deterministic artifacts and Action outputs, and confirms that a tampered skill
fails closed.

Real adopters will be added only when their public repository, pinned Action
workflow, and maintainer consent can be verified.
