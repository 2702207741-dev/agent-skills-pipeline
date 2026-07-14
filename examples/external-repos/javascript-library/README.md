# JavaScript Library Consumer Fixture

This repository-shaped fixture proves that the public Action validates a
JavaScript project without inspecting or executing its application code. The
fixture owns one review skill, a small ESM module, and a Node test.

Run the project test with `node --test`, then run the portable gate from the
Agent Skills Pipeline repository:

```bash
./our-skills verify --workspace examples/external-repos/javascript-library
```
