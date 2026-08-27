# Frontend API contract

Base URL: `http://localhost:8000`. CORS: `http://localhost:5173`. No auth. Interactive spec at `http://localhost:8000/docs` once the server is up.

Parse is **synchronous** and can take **30–90s**. The frontend should call `POST .../parse` with a long timeout, show loading, then call stitch. Do not poll; there is no job-progress stream in MVP.

`lines` is a JSON array of strings. Display line number `n` is **1-based** and equals `lines[n - 1]`. Citation `line_numbers` use that same 1-based scheme.

Never render parse internals (`feature_type`, `reason`, `features.json`). UI uses `status`, `lines`, and `note` only.

## Types

```
JobStatus = "uploaded" | "parsed" | "stitched" | "failed"

Citation = {
  quote: string,                 // exact transcript span
  line_numbers: number[],        // 1-based, sorted unique
  offsets: { start: number, end: number }  // 0-based, end exclusive, into "\n".join(lines)
}

NoteItem = {
  id: string,                    // stable, e.g. "s-1", "p-3"
  text: string,                  // SOAP bullet
  citations: Citation[],
  uncertain: boolean,
  grounded: boolean              // always true in MVP note items
}

NoteSection = {
  id: "subjective" | "objective" | "assessment" | "plan",
  heading: string,               // "Subjective" | "Objective" | "Assessment" | "Plan"
  items: NoteItem[]
}

VisitNote = { sections: NoteSection[] }   // empty sections omitted; order S → O → A → P
```

Error bodies:

- `400` / `404` / `409`: `{ "detail": string }` (FastAPI default)
- `502` parse failure: `{ "job_id": string, "status": "failed", "errors": string[] }`

## Endpoints

**`POST /api/jobs`** — upload transcript.

- Request: `multipart/form-data`, field name **`file`**, `.txt` only.
- `201`: `{ "job_id": "<uuid>", "status": "uploaded", "lines": string[] }`
- `400`: empty file, not `.txt`, or unreadable text.

Show `lines` as the numbered transcript immediately.

**`POST /api/jobs/{job_id}/parse`** — run LangGraph (Gemini). Body empty.

- `200`: `{ "job_id": string, "status": "parsed", "grounded_count": number, "feature_count": number }`
- `404` unknown job. Re-parse is allowed: overwrites `features.json`, clears `note.json`, status back to `parsed`.
- `502`: Gemini/schema error as above.

Do **not** expect `features` or `note` here. Then call stitch.

**`POST /api/jobs/{job_id}/stitch`** — build SOAP from persisted features. Body empty.

- `200`: `{ "job_id": string, "status": "stitched", "note": VisitNote, "lines": string[] }`
- `404` unknown job; `409` if not yet parsed. Re-stitch from existing features is allowed and returns `200`.
- Click a `NoteItem`: display `citations[].quote`; highlight `citations[].line_numbers` in `lines`. Optional finer highlight via `offsets` into `"\n".join(lines)`.

**`GET /api/jobs`** — list persisted jobs, newest first.

- `200`: `{ "jobs": [ { "job_id": string, "status": JobStatus, "created_at": string, "updated_at": string } ] }`
- Timestamps are ISO-8601 UTC.

**`GET /api/jobs/{job_id}`** — restore a job (no Gemini). Use on refresh / reopen.

- `200`: `{ "job_id": string, "status": JobStatus, "lines": string[], "note": VisitNote | null, "errors": string[], "created_at": string, "updated_at": string }`
- `note` is `null` unless `status === "stitched"`.
- `404` unknown job.

**Not in MVP (do not call):** `GET .../features`, `GET .../items/{item_id}`, websocket/SSE, delete job.

## Frontend call sequence

1. `POST /api/jobs` with file → render `lines`, keep `job_id`.
2. `POST /api/jobs/{id}/parse` (long timeout, loading copy).
3. `POST /api/jobs/{id}/stitch` → render `note.sections`.
4. On bullet click, use that item’s `citations` from the in-memory `note` (or refetch `GET /api/jobs/{id}`).
5. On page load with a known id, `GET /api/jobs/{id}` only.

## Run backend

From `backend/` (with repo-root `.env` containing `GEMINI_API_KEY`):

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
