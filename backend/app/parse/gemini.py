from __future__ import annotations

import os
import re
import time

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from app.models import ExtractFeature, ExtractPayload, Feature, Quote

LINE_PREFIX = re.compile(r"^LINE\s+\d+:\s*", re.IGNORECASE)

EXTRACT_PROMPT = """You extract a grounded SOAP feature inventory from a clinical visit transcript.

Return JSON only: {{ "features": [ Feature, ... ] }}.
Each Feature has section, feature_type, text, uncertain, kind,
  quotes: [{{ text, line_numbers }}]  (REQUIRED, at least one quote per feature).
Keep quote.text short (one phrase or clause). Do not write a reason field.

Rules:
- Use only the transcript. Omit feature types that do not appear. Extract ALL distinct findings, meds, vitals, exam, assessment, and plan items.
- quote.text must be an exact substring of the transcript line AFTER the LINE n: prefix. Never include "LINE n:" in quote.text.
- line_numbers are the file lines that contain that span (LINE n: is a hint).
- Assessment: only impressions the clinician stated. Do not invent diagnoses.
- Conflicts: keep the latest resolved plan; still record clinically relevant corrections (stopped a drug, stop OTC).
- Deferred issues are plan.deferred, never treated-as-done.
- Medications: name, dose, frequency, start/stop/continue only when spoken. Unsure dose → uncertain=true.

Allowed feature_type by section:
- subjective: problem, hpi, pertinent_negative, current_meds_reported, otc_and_supplements, pmh_fh_sh, other_concern
- objective: vital, exam, result_mentioned
- assessment: impression, rationale
- plan: med_start, med_stop, med_change, order, follow_up, precaution, deferred

kind: medication | finding | plan | deferred | other

Transcript:
---
{numbered_raw_text}
---
"""


def _client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    return genai.Client(api_key=api_key)


def extract_features(numbered_raw_text: str) -> list[Feature]:
    model = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")
    prompt = EXTRACT_PROMPT.format(numbered_raw_text=numbered_raw_text)
    client = _client()
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ExtractPayload,
                    max_output_tokens=32768,
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(
                        disable=True
                    ),
                ),
            )
            parsed = ExtractPayload.model_validate_json(response.text)
            return [_to_feature(item) for item in parsed.features]
        except genai_errors.ServerError as exc:
            last_error = exc
            if exc.code in (503, 429) and attempt < 3:
                time.sleep(2**attempt)
                continue
            raise
        except Exception as exc:
            last_error = exc
            if attempt < 3:
                time.sleep(1)
                continue
            raise
    raise last_error or RuntimeError("Gemini extract failed")


def _clean_quote_text(text: str) -> str:
    return LINE_PREFIX.sub("", text.strip())


def _to_feature(item: ExtractFeature) -> Feature:
    return Feature(
        section=item.section,
        feature_type=item.feature_type,
        text=item.text,
        quotes=[
            Quote(text=_clean_quote_text(q.text), line_numbers=q.line_numbers)
            for q in item.quotes
            if q.text.strip()
        ],
        reason="",
        uncertain=item.uncertain,
        kind=item.kind,
        grounded=False,
    )
