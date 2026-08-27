# Eval set

Checklist labels for the Grounded Visit Note pipeline. Extract wording varies, so cases score **facts** (must include / must not / section shape / grounding), not gold SOAP text.

## Layout

| Path | Role |
| --- | --- |
| `cases/*/transcript.txt` | Synthetic visit |
| `cases/*/labels.json` | Checklist for the stitched note (and features, when present) |
| `cases/*/gold_features.json` | Optional gold `Feature[]` for offline verify+stitch |
| `fixtures/` | Contract fixtures (ungrounded quotes dropped, etc.) |
| `scorer.py` | Deterministic matchers |
| `run_eval.py` | CLI |
| `out/` | Local reports (gitignored) |

## Run

From the repo root:

```bash
# verify + stitch only (no Gemini)
PYTHONPATH=backend python evals/run_eval.py --offline

# full parse graph (needs GEMINI_API_KEY)
PYTHONPATH=backend python evals/run_eval.py --pipeline
```

Writes `evals/out/latest.json`. Pytest: `backend/tests/test_evals.py` always runs offline cases; pipeline tests skip without an API key.

## Scores

- **recall** — fraction of `must_include` facts found
- **safety_ok** — no `must_not` / `must_not_section` hits (dose errors and invented workups fail here even if recall is high)
- **grounded_ok** — every note citation is a substring of the transcript file
