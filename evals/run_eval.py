#!/usr/bin/env python3
"""Score Grounded Visit Note evals. Run from repo root: PYTHONPATH=backend python evals/run_eval.py --offline"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.models import Feature  # noqa: E402
from app.parse.verify import verify_quotes  # noqa: E402
from app.stitch import stitch_note  # noqa: E402
from app.textutil import split_transcript  # noqa: E402

from evals.scorer import (  # noqa: E402
    EVALS_ROOT,
    FIXTURES_DIR,
    list_cases,
    load_labels,
    score_case,
)


def _load_features(raw: list[dict]) -> list[Feature]:
    return [Feature.model_validate(item) for item in raw]


def _print_table(rows: list[dict]) -> None:
    headers = ("case_id", "recall", "safety_ok", "grounded_ok", "passed")
    widths = [max(len(h), max(len(str(r.get(h, ""))) for r in rows) if rows else 0) for h in headers]
    fmt = "  ".join(f"{{:{w}}}" for w in widths)
    print(fmt.format(*headers))
    print(fmt.format(*("-" * w for w in widths)))
    for r in rows:
        print(
            fmt.format(
                r["case_id"],
                f"{r['recall']:.2f}",
                str(r["safety_ok"]),
                str(r["grounded_ok"]),
                str(r["passed"]),
            )
        )


def run_fixture(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    lines = data["lines"]
    features = verify_quotes(_load_features(data["features"]), lines)
    note = stitch_note(features, lines)
    expect = data["expect"]
    grounded = [f.grounded for f in features]
    ok = grounded == expect["grounded"]
    item_count = sum(len(s.items) for s in note.sections)
    if "note_item_count" in expect and item_count != expect["note_item_count"]:
        ok = False
    section_ids = [s.id.value for s in note.sections if s.items]
    if "note_sections" in expect and section_ids != expect["note_sections"]:
        ok = False
    if "note_item_ids" in expect:
        ids = [i.id for s in note.sections for i in s.items]
        if ids != expect["note_item_ids"]:
            ok = False
    return {
        "case_id": data.get("id", path.stem),
        "kind": "fixture",
        "passed": ok,
        "recall": 1.0 if ok else 0.0,
        "safety_ok": ok,
        "grounded_ok": ok,
        "required_sections_ok": ok,
        "expect": expect,
        "got": {
            "grounded": grounded,
            "note_item_count": item_count,
            "note_sections": section_ids,
        },
    }


def run_case_offline(case_dir: Path) -> dict | None:
    gold_path = case_dir / "gold_features.json"
    if not gold_path.is_file():
        return None
    labels = load_labels(case_dir / "labels.json")
    transcript = (case_dir / "transcript.txt").read_text(encoding="utf-8")
    lines = split_transcript(transcript)
    features = verify_quotes(
        _load_features(json.loads(gold_path.read_text(encoding="utf-8"))),
        lines,
    )
    note = stitch_note(features, lines)
    score = score_case(labels, note, transcript, features)
    out = score.as_dict()
    out["kind"] = "offline_case"
    return out


def run_case_pipeline(case_dir: Path) -> dict:
    from app.parse.graph import run_parse

    labels = load_labels(case_dir / "labels.json")
    transcript = (case_dir / "transcript.txt").read_text(encoding="utf-8")
    state = run_parse(job_id=f"eval-{case_dir.name}", raw_text=transcript)
    features = state["features"]
    note = stitch_note(features, state["lines"])
    score = score_case(labels, note, transcript, features)
    out = score.as_dict()
    out["kind"] = "pipeline"
    out["feature_count"] = len(features)
    out["grounded_count"] = sum(1 for f in features if f.grounded)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Grounded Visit Note evals")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--offline", action="store_true", help="fixtures + gold_features cases")
    mode.add_argument("--pipeline", action="store_true", help="Gemini parse + stitch + checklists")
    args = parser.parse_args()

    results: list[dict] = []
    if args.offline:
        for path in sorted(FIXTURES_DIR.glob("*.json")):
            results.append(run_fixture(path))
        for case_dir in list_cases():
            row = run_case_offline(case_dir)
            if row:
                results.append(row)
    else:
        if not os.environ.get("GEMINI_API_KEY"):
            print("GEMINI_API_KEY is not set; cannot run --pipeline", file=sys.stderr)
            return 2
        for case_dir in list_cases():
            results.append(run_case_pipeline(case_dir))

    _print_table(results)
    mean_recall = (
        sum(r["recall"] for r in results) / len(results) if results else 0.0
    )
    safety_fails = sum(1 for r in results if not r["safety_ok"])
    print()
    print(f"mean_recall={mean_recall:.2f}  safety_fails={safety_fails}  n={len(results)}")

    out_dir = EVALS_ROOT / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "mode": "offline" if args.offline else "pipeline",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "mean_recall": mean_recall,
        "safety_fails": safety_fails,
        "results": results,
    }
    (out_dir / "latest.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote {out_dir / 'latest.json'}")
    return 0 if all(r["passed"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
