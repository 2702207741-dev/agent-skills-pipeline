# Documentation Consumer Fixture

This repository-shaped fixture proves that the public Action also applies to a
documentation-only project. It intentionally omits `schema_version`; the v1
contract treats a missing value as version 1 for backward compatibility.

```bash
./our-skills verify --workspace examples/external-repos/documentation-site
```
