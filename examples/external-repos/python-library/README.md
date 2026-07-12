# External Python Library Example

This directory is a complete consumer fixture, not an adopter claim. It models
a small OSS Python library that owns one repository-specific agent skill and
uses the root `our-skills` GitHub Action as its quality and release gate.

The consumer contributes only:

- `skills.json`, a three-field registry contract;
- `skills/python-library-review/SKILL.md`, its local maintenance behavior;
- `.github/workflows/our-skills.yml`, one pinned Action step.

Run the same gate locally from the `our-skills` repository:

```bash
./our-skills doctor \
  --workspace examples/external-repos/python-library \
  --registry skills.json

./our-skills verify \
  --workspace examples/external-repos/python-library \
  --registry skills.json \
  --output .our-skills-dist
```

The release gate emits a deterministic zip, manifest, checksum, and JSON report.
The checked-in consumer workflow pins the Action to an immutable commit rather
than a mutable branch or tag.
