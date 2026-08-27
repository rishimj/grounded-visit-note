from __future__ import annotations

import re

from app.models import Feature, Offsets, Quote
from app.textutil import join_lines

MAX_QUOTE_CHARS = 300


def _ws_pattern(quote: str) -> str | None:
    parts = [p for p in re.split(r"\s+", quote.strip()) if p]
    if not parts:
        return None
    return r"\s+".join(re.escape(p) for p in parts)


def find_span(raw_text: str, quote: str) -> tuple[int, int] | None:
    q = quote.strip()
    if not q:
        return None
    if len(q) > MAX_QUOTE_CHARS:
        q = q[:MAX_QUOTE_CHARS]
    idx = raw_text.find(q)
    if idx != -1:
        return idx, idx + len(q)
    pattern = _ws_pattern(q)
    if not pattern:
        return None
    match = re.search(pattern, raw_text)
    if match:
        return match.start(), match.end()
    return None


def line_numbers_for_span(raw_text: str, start: int, end: int) -> list[int]:
    if start < 0 or end <= start:
        return []
    end_inclusive = min(end, len(raw_text)) - 1
    numbers: list[int] = []
    offset = 0
    for i, line in enumerate(raw_text.split("\n"), start=1):
        line_end = offset + len(line)
        if end > offset and start < line_end:
            numbers.append(i)
        elif end > offset and start == offset and start == line_end:
            numbers.append(i)
        offset = line_end + 1
        if offset > end and start < offset:
            break
    return numbers


def verify_quotes(features: list[Feature], lines: list[str]) -> list[Feature]:
    """Ground each quote in the file and recompute line_numbers. reason is unused."""
    raw_text = join_lines(lines)
    verified: list[Feature] = []
    for feature in features:
        new_quotes: list[Quote] = []
        all_ok = True
        if not feature.quotes:
            all_ok = False
        for quote in feature.quotes:
            span = find_span(raw_text, quote.text)
            if span is None:
                all_ok = False
                new_quotes.append(
                    Quote(text=quote.text, line_numbers=[], offsets=None)
                )
                continue
            start, end = span
            found = raw_text[start:end]
            nums = line_numbers_for_span(raw_text, start, end)
            new_quotes.append(
                Quote(
                    text=found,
                    line_numbers=nums,
                    offsets=Offsets(start=start, end=end),
                )
            )
        verified.append(
            feature.model_copy(
                update={"quotes": new_quotes, "grounded": all_ok and bool(new_quotes)}
            )
        )
    return verified
