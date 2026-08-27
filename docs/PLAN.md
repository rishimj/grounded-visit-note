# Grounded Visit Note — Global Plan

Canonical architecture for this repo. Assignment brief: [BRIEF.md](BRIEF.md). Samples: [transcript_01.txt](transcript_01.txt), [transcript_02.txt](transcript_02.txt).

**Implement backend orchestration first**, then stitcher, then FastAPI job routes, then the React note UI.

## Product

Clinician uploads a visit transcript. The app returns a **SOAP visit note**. Click a bullet to highlight the transcript lines it came from. Every signed-looking claim must be grounded in a quote that actually appears in the file.

No real patient data. Gemini Flash via `GEMINI_API_KEY` in `.env` (never commit `.env`).

## Architecture

Two pipelines, one UI. Parse will grow; stitch should not.

```
upload → disk → parse graph → features.json → stitcher → note.json → UI note + transcript
```

| Layer | Role | Volatility |
| --- | --- | --- |
| FastAPI | Thin HTTP. Save file, run parse, run stitch, return note. | Low |
| Parse (LangGraph) | `ingest` → `extract_features` (Gemini) → `verify_quotes`. More validators later. | High |
| Stitch | Deterministic `features.json` → SOAP `VisitNote`. No LLM. | Low |
| UI | Same page: upload + note pane + transcript. Renders `VisitNote` only. | Low |
| Disk | `data/uploads/{id}/transcript.txt`, `features.json`, `note.json`. DB later. | Swap later |

Stack: FastAPI + LangGraph + `google-genai` (Gemini Flash) + Vite React later. Parse runs **in-process** (no worker queue in MVP).

## Parse graph (orchestration — build this first)

Ends at a verified **feature inventory**. Does **not** write the letter.

**State:** `job_id`, `file_path`, `raw_text`, `lines` (1-based file rows), `features[]`, `verification`, `errors`.

1. **ingest** — Read the saved `.txt`. Split on newlines; number lines `1…N`. Prefix `LINE n:` when sending to Gemini (hint only).
2. **extract_features** — One structured Gemini call. Output `Feature[]` (schema below).
3. **verify_quotes** — Each `quote.text` must be a substring of `raw_text` (whitespace-normalized, max ~300 chars). Recompute `line_numbers` from where the span was found (do not trust the model’s line counts). Set `grounded`. `reason` is audit-only and is never evidence.

Later parse nodes (same inventory out): quote repair, support check, contradictions. Stitch does not change.

Do **not** regex-parse speaker labels in MVP. File line numbers are enough for citations.

### Feature inventory (`features.json`)

```
Feature:
  section: subjective | objective | assessment | plan
  feature_type: (see lists)
  text: clinician-facing bullet
  quotes: [{ text, line_numbers: int[] }]
  reason: why these quotes support text (not shown in the note body)
  uncertain: bool
  kind: medication | finding | plan | deferred | other
  grounded: bool   # set by verify_quotes
```

**Subjective:** `problem`, `hpi`, `pertinent_negative`, `current_meds_reported`, `otc_and_supplements`, `pmh_fh_sh`, `other_concern`

**Objective:** `vital`, `exam`, `result_mentioned`

**Assessment:** `impression`, `rationale` — only if the clinician said it; do not invent diagnoses

**Plan:** `med_start`, `med_stop`, `med_change`, `order`, `follow_up`, `precaution`, `deferred`

Omit empty types. Do not pad SOAP.

### Extract prompt (sketch)

```
You extract a grounded SOAP feature inventory from a clinical visit transcript.

Return JSON only: { "features": [ Feature, ... ] }.
Each Feature has section, feature_type, text, uncertain, kind,
  quotes: [{ text, line_numbers }],
  reason: one or two sentences why these quotes support text (not a restatement; not a SOAP finding; no doses only in reason).

Rules:
- Use only the transcript. Omit feature types that do not appear.
- quote.text must be an exact substring. line_numbers are the file lines that contain that span (transcript is sent with LINE n: prefixes as a hint).
- Assessment: only impressions the clinician stated.
- Conflicts: keep the latest resolved plan; still record clinically relevant corrections (stopped a drug, stop OTC).
- Deferred issues are plan.deferred, never treated-as-done.
- Medications: name, dose, frequency, start/stop/continue only when spoken. Unsure dose → uncertain=true.

Allowed feature_type by section: (lists above)

Transcript:
---
{numbered_raw_text}
---
```

Use Gemini `response_mime_type=application/json` + Pydantic `response_schema`.

## Stitcher (after orchestration)

`stitch_note(features, lines) -> VisitNote`. Separate module, not a graph node, no LLM. Must not invent clinical content.

```
VisitNote:
  sections: [{ id, heading, items: [{ text, citations, uncertain, grounded }] }]
  citations: [{ quote, line_numbers, offsets }]
```

- Section order: S → O → A → P. Omit empty sections.
- Within a section: fixed `feature_type` order, then original order.
- Item `text` = feature `text`. No `feature_type` or `reason` in the body.
- Include only `grounded` features in the note (MVP).
- Persist `note.json`. Re-stitch from `features.json` without re-calling Gemini.

## FastAPI (after stitch)

- `POST /api/jobs` — multipart upload → disk → parse → `features.json` → stitch → `note.json` → `{ job_id, note, lines }`
- `GET /api/jobs/{id}` — read disk, no re-parse

## UI (last)

One page: file upload, loading copy, SOAP **note** (headings + bullets), numbered transcript. Click bullet → highlight cited lines. Do not render parse internals.

## Validation (samples in this folder)

**transcript_01 (Alvarez):** headaches in S; BPs/exam in O; pressure–headache link in A only if spoken; amlodipine 5 mg / stop Advil / labs / 4-week BP log in P; knee `deferred`; metformin dose `uncertain`.

**transcript_02 (Marcus):** thin S/O; plan is the note (no running 2 weeks, brace for running, PT, PRN return). No invented full workup.

## Out of MVP

Speaker regex, paste/sample dropdown, queue, database, streaming, in-note edit, LLM letter-writer, rendering feature schema in the UI.

## Implementation order

1. Backend orchestration: disk ingest, LangGraph, Gemini extract, `verify_quotes`, write `features.json`
2. Stitcher → `note.json`
3. FastAPI job endpoints
4. React note UI
5. Iterate parse validators without changing stitch/UI contracts
