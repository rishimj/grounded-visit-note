from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.models import Feature  # noqa: E402
from app.parse.verify import verify_quotes  # noqa: E402
from app.stitch import stitch_note  # noqa: E402
from app.textutil import split_transcript  # noqa: E402
from evals.run_eval import run_case_offline, run_case_pipeline, run_fixture  # noqa: E402
from evals.scorer import FIXTURES_DIR, list_cases, load_labels, score_case  # noqa: E402


def test_offline_fixtures():
    paths = sorted(FIXTURES_DIR.glob("*.json"))
    assert paths, "expected at least one fixture"
    for path in paths:
        row = run_fixture(path)
        assert row["passed"], row


def test_offline_gold_feature_cases():
    ran = 0
    for case_dir in list_cases():
        row = run_case_offline(case_dir)
        if row is None:
            continue
        ran += 1
        assert row["passed"], row
    assert ran >= 1


def test_scorer_catches_safety_hit():
    case_dir = ROOT / "evals" / "cases" / "05_dose_correction"
    labels = load_labels(case_dir / "labels.json")
    transcript = (case_dir / "transcript.txt").read_text(encoding="utf-8")
    lines = split_transcript(transcript)
    features = verify_quotes(
        [
            Feature.model_validate(
                {
                    "section": "plan",
                    "feature_type": "med_change",
                    "text": "Continue metformin 1000 mg twice daily.",
                    "quotes": [{"text": "metformin one thousand milligrams"}],
                    "kind": "medication",
                    "uncertain": False,
                }
            )
        ],
        lines,
    )
    note = stitch_note(features, lines)
    score = score_case(labels, note, transcript, features)
    assert score.safety_ok is False
    assert any(not r.ok for r in score.must_not)


@pytest.mark.skipif(not os.environ.get("GEMINI_API_KEY"), reason="GEMINI_API_KEY not set")
def test_pipeline_cases():
    for case_dir in list_cases():
        row = run_case_pipeline(case_dir)
        assert "recall" in row
        assert row["grounded_ok"], row
