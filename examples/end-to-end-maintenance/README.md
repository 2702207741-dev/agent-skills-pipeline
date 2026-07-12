# Issue to Review to Release Gate Demo

This runnable fixture shows one complete OSS maintenance flow rather than a
diagram of one:

1. **Issue triage:** validate `issue.json` and reproduce the empty-input failure
   against `repository-before`.
2. **PR review:** inspect the changed files, reject unsafe execution primitives,
   and require the fixed unit suite in `repository-after` to pass.
3. **Release gate:** validate the repository-owned skill, build a deterministic
   release zip, and verify its manifest and checksum.

Run it through the unified command:

```bash
./our-skills demo --check
```

Or retain a machine-readable run report:

```bash
./our-skills demo --output ./demo-report.json
```

`expected-report.json` is the regression oracle. The demo fails if the issue no
longer reproduces before the patch, the fixed tests regress, unsafe code enters
the patch, the external skill contract fails, or the release artifact cannot be
verified.
