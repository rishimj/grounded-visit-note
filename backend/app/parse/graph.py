from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.models import Feature
from app.parse.gemini import extract_features
from app.parse.verify import verify_quotes
from app.textutil import split_transcript


class ParseState(TypedDict):
    job_id: str
    file_path: str
    raw_text: str
    lines: list[str]
    features: list[Feature]
    verification: dict
    errors: list[str]


def ingest(state: ParseState) -> dict:
    raw_text = state["raw_text"]
    if not raw_text and state.get("file_path"):
        raw_text = open(state["file_path"], encoding="utf-8").read()
    lines = split_transcript(raw_text)
    return {"raw_text": raw_text, "lines": lines, "errors": []}


def numbered_transcript(lines: list[str]) -> str:
    return "\n".join(f"LINE {i}: {line}" for i, line in enumerate(lines, start=1))


def extract_features_node(state: ParseState) -> dict:
    numbered = numbered_transcript(state["lines"])
    features = extract_features(numbered)
    return {"features": features}


def verify_quotes_node(state: ParseState) -> dict:
    features = verify_quotes(state["features"], state["lines"])
    grounded = sum(1 for f in features if f.grounded)
    return {
        "features": features,
        "verification": {
            "grounded_count": grounded,
            "feature_count": len(features),
        },
    }


def build_parse_graph():
    graph = StateGraph(ParseState)
    graph.add_node("ingest", ingest)
    graph.add_node("extract_features", extract_features_node)
    graph.add_node("verify_quotes", verify_quotes_node)
    graph.add_edge(START, "ingest")
    graph.add_edge("ingest", "extract_features")
    graph.add_edge("extract_features", "verify_quotes")
    graph.add_edge("verify_quotes", END)
    return graph.compile()


parse_graph = build_parse_graph()


def run_parse(job_id: str, raw_text: str, file_path: str = "") -> ParseState:
    result = parse_graph.invoke(
        {
            "job_id": job_id,
            "file_path": file_path,
            "raw_text": raw_text,
            "lines": [],
            "features": [],
            "verification": {},
            "errors": [],
        }
    )
    return result
