from app.models import Feature, FeatureType, Kind, Quote, SectionId
from app.parse.verify import find_span, line_numbers_for_span, verify_quotes
from app.stitch import stitch_note


def test_find_span_and_line_numbers():
    lines = ["hello world", "second line", "third"]
    raw = "\n".join(lines)
    span = find_span(raw, "second line")
    assert span == (12, 23)
    assert line_numbers_for_span(raw, *span) == [2]


def test_verify_whitespace_and_ungrounded():
    lines = ["She takes metformin 500 mg.", "Knee pain later."]
    features = [
        Feature(
            section=SectionId.subjective,
            feature_type=FeatureType.current_meds_reported,
            text="Metformin 500 mg",
            quotes=[Quote(text="metformin 500 mg")],
            reason="audit",
            uncertain=False,
            kind=Kind.medication,
        ),
        Feature(
            section=SectionId.plan,
            feature_type=FeatureType.deferred,
            text="Invented",
            quotes=[Quote(text="this quote is not in the file")],
            reason="audit",
            kind=Kind.deferred,
        ),
    ]
    out = verify_quotes(features, lines)
    assert out[0].grounded is True
    assert out[0].quotes[0].line_numbers == [1]
    assert out[0].quotes[0].offsets is not None
    assert out[1].grounded is False


def test_stitch_copies_quotes_omits_ungrounded():
    lines = ["Start amlodipine five milligrams.", "Defer the knee."]
    features = verify_quotes(
        [
            Feature(
                section=SectionId.plan,
                feature_type=FeatureType.med_start,
                text="Start amlodipine 5 mg daily",
                quotes=[Quote(text="amlodipine five milligrams")],
                kind=Kind.medication,
            ),
            Feature(
                section=SectionId.plan,
                feature_type=FeatureType.deferred,
                text="Not in file",
                quotes=[Quote(text="nope")],
                kind=Kind.deferred,
            ),
        ],
        lines,
    )
    note = stitch_note(features, lines)
    assert len(note.sections) == 1
    assert note.sections[0].id == SectionId.plan
    assert len(note.sections[0].items) == 1
    item = note.sections[0].items[0]
    assert item.id == "p-1"
    assert item.text == "Start amlodipine 5 mg daily"
    assert item.citations[0].quote
    assert 1 in item.citations[0].line_numbers
