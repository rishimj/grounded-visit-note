---
name: grounded-visit-note
description: >-
  Implements the Grounded Visit Note app (FastAPI, LangGraph parse graph,
  deterministic SOAP stitcher, Gemini Flash, click-to-source UI). Use when
  working in this repo, building orchestration, stitching notes, visit
  transcripts, SOAP features, or anything described in docs/PLAN.md.
---

# Grounded Visit Note

Follow [docs/PLAN.md](../../../docs/PLAN.md). Brief and samples live in [docs/](../../../docs/).

## Non-negotiables

- **Parse ≠ stitch.** LangGraph produces grounded `features.json`. A separate Python stitcher builds the SOAP `VisitNote`. Do not write the letter inside the extract prompt or the graph.
- **Ground in code.** `verify_quotes` must find each quote in the file and recompute line numbers. `reason` is audit-only, never evidence.
- **UI renders the note only**, not feature types or parse debug.
- **Disk now, DB later:** `data/uploads/{id}/transcript.txt`, `features.json`, `note.json`.
- **Never commit `.env` or API keys.**

## Build order

1. Orchestration (ingest → extract_features → verify_quotes)
2. Stitcher
3. FastAPI `/api/jobs`
4. React two-pane note UI

## Stack

FastAPI, LangGraph in-process, `google-genai` / Gemini Flash, Vite React. No speaker-label regex in MVP.

## Full schema, prompt, and validation facts

See [docs/PLAN.md](../../../docs/PLAN.md).
