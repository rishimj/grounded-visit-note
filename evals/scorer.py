from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.models import Feature, VisitNote
from app.parse.verify import find_span

EVALS_ROOT = Path(__file__).resolve().parent
CASES_DIR = EVALS_ROOT / "cases"
FIXTURES_DIR = EVALS_ROOT / "fixtures"


@dataclass
class CheckResult:
    id: str
    ok: bool
    detail: str = ""


@dataclass
class CaseScore:
    case_id: str
    recall: float
    safety_ok: bool
    grounded_ok: bool
    required_sections_ok: bool
    must_include: list[CheckResult] = field(default_factory=list)
    must_not: list[CheckResult] = field(default_factory=list)
    extras: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return (
            self.recall == 1.0
            and self.safety_ok
            and self.grounded_ok
            and self.required_sections_ok
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "passed": self.passed,
            "recall": self.recall,
            "safety_ok": self.safety_ok,
            "grounded_ok": self.grounded_ok,
            "required_sections_ok": self.required_sections_ok,
            "must_include": [r.__dict__ for r in self.must_include],
            "must_not": [r.__dict__ for r in self.must_not],
            "extras": [r.__dict__ for r in self.extras],
        }


@dataclass
class Row:
    section: str
    text: str
    uncertain: bool
    grounded: bool
    feature_type: str | None = None
    source: str = "note"


def load_labels(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def list_cases() -> list[Path]:
    if not CASES_DIR.exists():
        return []
    return sorted(p for p in CASES_DIR.iterdir() if (p / "labels.json").is_file())


def _rows_from_note(note: VisitNote) -> list[Row]:
    rows: list[Row] = []
    for section in note.sections:
        for item in section.items:
            rows.append(
                Row(
                    section=section.id.value,
                    text=item.text,
                    uncertain=item.uncertain,
                    grounded=item.grounded,
                    source="note",
                )
            )
    return rows


def _rows_from_features(features: list[Feature] | None) -> list[Row]:
    if not features:
        return []
    return [
        Row(
            section=f.section.value,
            text=f.text,
            uncertain=f.uncertain,
            grounded=f.grounded,
            feature_type=f.feature_type.value,
            source="feature",
        )
        for f in features
    ]


def _text_matches(text: str, spec: dict[str, Any]) -> bool:
    has_constraint = False
    if spec.get("any"):
        has_constraint = True
        lower = text.lower()
        if not all(s.lower() in lower for s in spec["any"]):
            return False
    if spec.get("pattern"):
        has_constraint = True
        if not re.search(spec["pattern"], text, flags=re.IGNORECASE):
            return False
    return has_constraint


def _row_matches(row: Row, spec: dict[str, Any], *, require_feature_type: bool) -> bool:
    if spec.get("section") and row.section != spec["section"]:
        return False
    if require_feature_type and spec.get("feature_type"):
        if row.feature_type != spec["feature_type"]:
            return False
    if "uncertain" in spec and spec["uncertain"] is not None:
        if row.uncertain is not spec["uncertain"]:
            return False
    return _text_matches(row.text, spec)


def _find_include(rows: list[Row], spec: dict[str, Any]) -> bool:
    need_ft = bool(spec.get("feature_type"))
    pool = rows
    if need_ft:
        typed = [r for r in rows if r.source == "feature"]
        pool = typed if typed else [r for r in rows if r.source == "note"]
    return any(_row_matches(r, spec, require_feature_type=need_ft) for r in pool)


def _concat_note(note: VisitNote, section: str | None = None) -> str:
    parts: list[str] = []
    for sec in note.sections:
        if section and sec.id.value != section:
            continue
        for item in sec.items:
            parts.append(item.text)
    return "\n".join(parts)


def _must_not_hit(note: VisitNote, rows: list[Row], spec: dict[str, Any]) -> bool:
    section = spec.get("section")
    scoped = [r for r in rows if (not section or r.section == section)]
    for row in scoped:
        if spec.get("any") or spec.get("pattern"):
            if _text_matches(row.text, spec):
                return True
    blob = _concat_note(note, section)
    if spec.get("pattern") and re.search(spec["pattern"], blob, flags=re.IGNORECASE):
        return True
    if spec.get("any") and not section:
        lower = blob.lower()
        if all(s.lower() in lower for s in spec["any"]):
            return True
    return False


def check_grounding(note: VisitNote, transcript: str) -> tuple[bool, str]:
    missing: list[str] = []
    for section in note.sections:
        for item in section.items:
            if not item.grounded:
                missing.append(f"{item.id} not grounded")
                continue
            for cit in item.citations:
                if find_span(transcript, cit.quote) is None:
                    missing.append(f"{item.id} quote not in file")
    return (not missing, "; ".join(missing))


def score_case(
    labels: dict[str, Any],
    note: VisitNote,
    transcript: str,
    features: list[Feature] | None = None,
) -> CaseScore:
    rows = _rows_from_note(note) + _rows_from_features(features)
    include_results: list[CheckResult] = []
    for spec in labels.get("must_include") or []:
        cid = spec.get("id", "include")
        ok = _find_include(rows, spec)
        include_results.append(CheckResult(id=cid, ok=ok, detail="" if ok else "not found"))

    hits = sum(1 for r in include_results if r.ok)
    total = len(include_results)
    recall = 1.0 if total == 0 else hits / total

    must_not_results: list[CheckResult] = []
    for spec in labels.get("must_not") or []:
        cid = spec.get("id", "must_not")
        hit = _must_not_hit(note, rows, spec)
        must_not_results.append(
            CheckResult(id=cid, ok=not hit, detail="safety hit" if hit else "")
        )

    extras: list[CheckResult] = []
    for sec in labels.get("must_not_section") or []:
        present = any(s.id.value == sec and s.items for s in note.sections)
        extras.append(
            CheckResult(
                id=f"no_section_{sec}",
                ok=not present,
                detail="section present" if present else "",
            )
        )

    present_ids = {s.id.value for s in note.sections if s.items}
    required = labels.get("required_sections") or []
    missing_sec = [s for s in required if s not in present_ids]
    req_ok = not missing_sec
    extras.append(
        CheckResult(
            id="required_sections",
            ok=req_ok,
            detail="" if req_ok else f"missing {missing_sec}",
        )
    )

    min_sections = labels.get("min_sections")
    if min_sections is not None:
        n = len([s for s in note.sections if s.items])
        extras.append(
            CheckResult(
                id="min_sections",
                ok=n >= min_sections,
                detail="" if n >= min_sections else f"got {n}",
            )
        )

    grounding_spec = labels.get("grounding") or {}
    grounded_ok = True
    ground_detail = ""
    if grounding_spec.get("all_note_items_grounded", True):
        grounded_ok, ground_detail = check_grounding(note, transcript)
    extras.append(CheckResult(id="grounding", ok=grounded_ok, detail=ground_detail))

    safety_ok = all(r.ok for r in must_not_results) and all(
        r.ok for r in extras if r.id.startswith("no_section_")
    )
    required_sections_ok = all(
        r.ok for r in extras if r.id in {"required_sections", "min_sections"}
    )

    return CaseScore(
        case_id=labels.get("id", "unknown"),
        recall=recall,
        safety_ok=safety_ok,
        grounded_ok=grounded_ok,
        required_sections_ok=required_sections_ok,
        must_include=include_results,
        must_not=must_not_results,
        extras=extras,
    )
