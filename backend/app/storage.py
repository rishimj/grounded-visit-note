from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from app.models import Feature, JobListItem, JobMeta, JobRecord, JobStatus, VisitNote
from app.textutil import split_transcript

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_UPLOADS = REPO_ROOT / "data" / "uploads"


def _now() -> datetime:
    return datetime.now(timezone.utc)


class JobStorage(Protocol):
    def create_job(self, transcript: str) -> str: ...
    def get_job(self, job_id: str) -> JobRecord | None: ...
    def save_features(self, job_id: str, features: list[Feature]) -> None: ...
    def save_note(self, job_id: str, note: VisitNote) -> None: ...
    def set_status(
        self,
        job_id: str,
        status: JobStatus,
        errors: list[str] | None = None,
    ) -> None: ...
    def clear_note(self, job_id: str) -> None: ...
    def list_jobs(self) -> list[JobListItem]: ...


class DiskJobStorage:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or DEFAULT_UPLOADS
        self.root.mkdir(parents=True, exist_ok=True)

    def _dir(self, job_id: str) -> Path:
        return self.root / job_id

    def create_job(self, transcript: str) -> str:
        job_id = str(uuid4())
        path = self._dir(job_id)
        path.mkdir(parents=True, exist_ok=True)
        (path / "transcript.txt").write_text(transcript, encoding="utf-8")
        now = _now()
        meta = JobMeta(status=JobStatus.uploaded, errors=[], created_at=now, updated_at=now)
        self._write_meta(job_id, meta)
        return job_id

    def get_job(self, job_id: str) -> JobRecord | None:
        path = self._dir(job_id)
        transcript_path = path / "transcript.txt"
        if not transcript_path.exists():
            return None
        transcript = transcript_path.read_text(encoding="utf-8")
        meta = self._read_meta(job_id)
        features = None
        features_path = path / "features.json"
        if features_path.exists():
            raw = json.loads(features_path.read_text(encoding="utf-8"))
            features = [Feature.model_validate(f) for f in raw]
        note = None
        note_path = path / "note.json"
        if note_path.exists():
            note = VisitNote.model_validate_json(note_path.read_text(encoding="utf-8"))
        return JobRecord(
            job_id=job_id,
            transcript=transcript,
            features=features,
            note=note,
            meta=meta,
        )

    def save_features(self, job_id: str, features: list[Feature]) -> None:
        path = self._dir(job_id)
        payload = [f.model_dump(mode="json") for f in features]
        (path / "features.json").write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )
        self.set_status(job_id, JobStatus.parsed, errors=[])

    def save_note(self, job_id: str, note: VisitNote) -> None:
        path = self._dir(job_id)
        (path / "note.json").write_text(note.model_dump_json(indent=2), encoding="utf-8")
        self.set_status(job_id, JobStatus.stitched, errors=[])

    def clear_note(self, job_id: str) -> None:
        note_path = self._dir(job_id) / "note.json"
        if note_path.exists():
            note_path.unlink()

    def set_status(
        self,
        job_id: str,
        status: JobStatus,
        errors: list[str] | None = None,
    ) -> None:
        meta = self._read_meta(job_id)
        meta.status = status
        if errors is not None:
            meta.errors = errors
        meta.updated_at = _now()
        self._write_meta(job_id, meta)

    def list_jobs(self) -> list[JobListItem]:
        items: list[JobListItem] = []
        if not self.root.exists():
            return items
        for child in self.root.iterdir():
            if not child.is_dir():
                continue
            if not (child / "transcript.txt").exists():
                continue
            meta = self._read_meta(child.name)
            items.append(
                JobListItem(
                    job_id=child.name,
                    status=meta.status,
                    created_at=meta.created_at,
                    updated_at=meta.updated_at,
                )
            )
        items.sort(key=lambda j: j.updated_at, reverse=True)
        return items

    def _read_meta(self, job_id: str) -> JobMeta:
        path = self._dir(job_id) / "meta.json"
        return JobMeta.model_validate_json(path.read_text(encoding="utf-8"))

    def _write_meta(self, job_id: str, meta: JobMeta) -> None:
        (self._dir(job_id) / "meta.json").write_text(
            meta.model_dump_json(indent=2),
            encoding="utf-8",
        )


storage: DiskJobStorage = DiskJobStorage()


def lines_for(transcript: str) -> list[str]:
    return split_transcript(transcript)
