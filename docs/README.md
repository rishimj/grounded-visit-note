# Docs

| File | What |
| --- | --- |
| [PLAN.md](PLAN.md) | Global architecture and implementation order |
| [API.md](API.md) | HTTP contract for the frontend agent |
| [BRIEF.md](BRIEF.md) | Timed assignment brief |
| [transcript_01.txt](transcript_01.txt) | Primary sample (Alvarez) |
| [transcript_02.txt](transcript_02.txt) | Shorter sample (Marcus) |

Labeled eval cases (including copies of the samples plus harder visits) live in [`evals/`](../evals/). Run `PYTHONPATH=backend python evals/run_eval.py --offline` or `--pipeline`. See [evals/README.md](../evals/README.md).

Agents: project skill `.cursor/skills/grounded-visit-note/` and [AGENTS.md](../AGENTS.md).
