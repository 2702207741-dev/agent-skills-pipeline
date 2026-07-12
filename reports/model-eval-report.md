# Multi-Model Evaluation: v4.0.0

- Dataset: `examples/replay-dataset.json`
- Mode: deterministic replay of recorded agent traces
- Cases: 42

| Model | Provider | Mode | Status | Pass Rate | Failures |
|---|---|---|---|---:|---:|
| Codex | OpenAI | replay-adapter | enabled | 1.00 | 0 |
| Claude | Anthropic | replay-adapter | enabled | 1.00 | 0 |
| Gemini | Google | replay-adapter | enabled | 1.00 | 0 |
| Local Model | Local | replay-adapter | enabled | 1.00 | 0 |

Live API adapters can replace replay-only scoring later; this report is intentionally deterministic for CI.
