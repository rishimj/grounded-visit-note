# Label schema

Each `cases/<id>/labels.json` is a checklist, not a full note.

```json
{
  "id": "01_alvarez",
  "title": "Short title",
  "tags": ["meds", "deferred"],
  "must_include": [
    {
      "id": "headaches",
      "section": "subjective",
      "feature_type": "problem",
      "any": ["headache"],
      "uncertain": false
    }
  ],
  "must_not": [
    {
      "id": "restart_lisinopril",
      "section": "plan",
      "pattern": "resume.{0,20}lisinopril"
    }
  ],
  "must_not_section": ["assessment"],
  "required_sections": ["plan"],
  "min_sections": 1,
  "grounding": { "all_note_items_grounded": true }
}
```

## Matching

- `any`: every string must appear in **one** item (or feature) `text`, case-insensitive.
- `pattern`: regex against that same text (must_include and must_not). If `must_not` omits `section`, the concatenated note is also searched.
- `section` / `feature_type` / `uncertain`: extra filters when set. `feature_type` is checked on parse `Feature` rows; note items use `section` + `text` + `uncertain`.
- `must_not_section`: fail if that SOAP section has any items.
- Grounding: citation `quote` must be found in the transcript via `find_span`.
