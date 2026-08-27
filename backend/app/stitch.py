from __future__ import annotations

from app.models import (
    FEATURE_TYPES_BY_SECTION,
    ITEM_ID_PREFIX,
    SECTION_HEADINGS,
    Citation,
    Feature,
    NoteItem,
    NoteSection,
    Offsets,
    SectionId,
    VisitNote,
)
from app.textutil import join_lines


def stitch_note(features: list[Feature], lines: list[str]) -> VisitNote:
    raw = join_lines(lines)
    sections: list[NoteSection] = []
    for section_id in (
        SectionId.subjective,
        SectionId.objective,
        SectionId.assessment,
        SectionId.plan,
    ):
        typed_order = FEATURE_TYPES_BY_SECTION[section_id]
        indexed = [
            (i, f)
            for i, f in enumerate(features)
            if f.section == section_id and f.grounded
        ]
        indexed.sort(
            key=lambda pair: (
                typed_order.index(pair[1].feature_type)
                if pair[1].feature_type in typed_order
                else 99,
                pair[0],
            )
        )
        if not indexed:
            continue
        prefix = ITEM_ID_PREFIX[section_id]
        items: list[NoteItem] = []
        for n, (_, feature) in enumerate(indexed, start=1):
            citations: list[Citation] = []
            for quote in feature.quotes:
                if not quote.line_numbers:
                    continue
                offsets = quote.offsets or _offsets_from_quote(raw, quote.text)
                citations.append(
                    Citation(
                        quote=quote.text,
                        line_numbers=quote.line_numbers,
                        offsets=offsets,
                    )
                )
            items.append(
                NoteItem(
                    id=f"{prefix}-{n}",
                    text=feature.text,
                    citations=citations,
                    uncertain=feature.uncertain,
                    grounded=True,
                )
            )
        sections.append(
            NoteSection(
                id=section_id,
                heading=SECTION_HEADINGS[section_id],
                items=items,
            )
        )
    return VisitNote(sections=sections)


def _offsets_from_quote(raw: str, quote: str) -> Offsets:
    idx = raw.find(quote)
    if idx == -1:
        return Offsets(start=0, end=0)
    return Offsets(start=idx, end=idx + len(quote))
