from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    uploaded = "uploaded"
    parsed = "parsed"
    stitched = "stitched"
    failed = "failed"


class SectionId(str, Enum):
    subjective = "subjective"
    objective = "objective"
    assessment = "assessment"
    plan = "plan"


class FeatureType(str, Enum):
    problem = "problem"
    hpi = "hpi"
    pertinent_negative = "pertinent_negative"
    current_meds_reported = "current_meds_reported"
    otc_and_supplements = "otc_and_supplements"
    pmh_fh_sh = "pmh_fh_sh"
    other_concern = "other_concern"
    vital = "vital"
    exam = "exam"
    result_mentioned = "result_mentioned"
    impression = "impression"
    rationale = "rationale"
    med_start = "med_start"
    med_stop = "med_stop"
    med_change = "med_change"
    order = "order"
    follow_up = "follow_up"
    precaution = "precaution"
    deferred = "deferred"


class Kind(str, Enum):
    medication = "medication"
    finding = "finding"
    plan = "plan"
    deferred = "deferred"
    other = "other"


FEATURE_TYPES_BY_SECTION: dict[SectionId, tuple[FeatureType, ...]] = {
    SectionId.subjective: (
        FeatureType.problem,
        FeatureType.hpi,
        FeatureType.pertinent_negative,
        FeatureType.current_meds_reported,
        FeatureType.otc_and_supplements,
        FeatureType.pmh_fh_sh,
        FeatureType.other_concern,
    ),
    SectionId.objective: (
        FeatureType.vital,
        FeatureType.exam,
        FeatureType.result_mentioned,
    ),
    SectionId.assessment: (
        FeatureType.impression,
        FeatureType.rationale,
    ),
    SectionId.plan: (
        FeatureType.med_start,
        FeatureType.med_stop,
        FeatureType.med_change,
        FeatureType.order,
        FeatureType.follow_up,
        FeatureType.precaution,
        FeatureType.deferred,
    ),
}

SECTION_HEADINGS: dict[SectionId, str] = {
    SectionId.subjective: "Subjective",
    SectionId.objective: "Objective",
    SectionId.assessment: "Assessment",
    SectionId.plan: "Plan",
}

ITEM_ID_PREFIX: dict[SectionId, str] = {
    SectionId.subjective: "s",
    SectionId.objective: "o",
    SectionId.assessment: "a",
    SectionId.plan: "p",
}


class Offsets(BaseModel):
    start: int
    end: int


class Quote(BaseModel):
    text: str
    line_numbers: list[int] = Field(default_factory=list)
    offsets: Offsets | None = None


class Feature(BaseModel):
    section: SectionId
    feature_type: FeatureType
    text: str
    quotes: list[Quote] = Field(default_factory=list)
    reason: str = ""
    uncertain: bool = False
    kind: Kind = Kind.other
    grounded: bool = False


class ExtractQuote(BaseModel):
    text: str = Field(min_length=1)
    line_numbers: list[int] = Field(default_factory=list)


class ExtractFeature(BaseModel):
    section: SectionId
    feature_type: FeatureType
    text: str
    quotes: list[ExtractQuote] = Field(min_length=1)
    uncertain: bool = False
    kind: Kind = Kind.other


class ExtractPayload(BaseModel):
    features: list[ExtractFeature] = Field(default_factory=list)


class Citation(BaseModel):
    quote: str
    line_numbers: list[int]
    offsets: Offsets


class NoteItem(BaseModel):
    id: str
    text: str
    citations: list[Citation]
    uncertain: bool
    grounded: bool = True


class NoteSection(BaseModel):
    id: SectionId
    heading: str
    items: list[NoteItem]


class VisitNote(BaseModel):
    sections: list[NoteSection]


class JobMeta(BaseModel):
    status: JobStatus
    errors: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class JobRecord(BaseModel):
    job_id: str
    transcript: str
    features: list[Feature] | None = None
    note: VisitNote | None = None
    meta: JobMeta


class UploadResponse(BaseModel):
    job_id: str
    status: Literal[JobStatus.uploaded]
    lines: list[str]


class ParseResponse(BaseModel):
    job_id: str
    status: Literal[JobStatus.parsed]
    grounded_count: int
    feature_count: int


class ParseErrorResponse(BaseModel):
    job_id: str
    status: Literal[JobStatus.failed]
    errors: list[str]


class StitchResponse(BaseModel):
    job_id: str
    status: Literal[JobStatus.stitched]
    note: VisitNote
    lines: list[str]


class JobListItem(BaseModel):
    job_id: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime


class JobListResponse(BaseModel):
    jobs: list[JobListItem]


class JobGetResponse(BaseModel):
    job_id: str
    status: JobStatus
    lines: list[str]
    note: VisitNote | None
    errors: list[str]
    created_at: datetime
    updated_at: datetime
