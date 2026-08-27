from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.models import (
    JobGetResponse,
    JobListResponse,
    JobStatus,
    ParseResponse,
    StitchResponse,
    UploadResponse,
)
from app.parse.graph import run_parse
from app.storage import lines_for, storage
from app.stitch import stitch_note
from app.upload import create_job_from_upload

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("", response_model=UploadResponse, status_code=201)
async def upload_job(file: UploadFile):
    job_id, lines = await create_job_from_upload(file)
    return UploadResponse(job_id=job_id, status=JobStatus.uploaded, lines=lines)


@router.get("", response_model=JobListResponse)
def list_jobs():
    return JobListResponse(jobs=storage.list_jobs())


@router.get("/{job_id}", response_model=JobGetResponse)
def get_job(job_id: str):
    record = storage.get_job(job_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Job not found")
    note = record.note if record.meta.status == JobStatus.stitched else None
    return JobGetResponse(
        job_id=record.job_id,
        status=record.meta.status,
        lines=lines_for(record.transcript),
        note=note,
        errors=record.meta.errors,
        created_at=record.meta.created_at,
        updated_at=record.meta.updated_at,
    )


@router.post("/{job_id}/parse")
def parse_job(job_id: str):
    record = storage.get_job(job_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Job not found")
    try:
        result = run_parse(job_id, record.transcript)
        features = result["features"]
        storage.clear_note(job_id)
        storage.save_features(job_id, features)
        verification = result.get("verification") or {}
        return ParseResponse(
            job_id=job_id,
            status=JobStatus.parsed,
            grounded_count=int(verification.get("grounded_count", 0)),
            feature_count=int(verification.get("feature_count", len(features))),
        )
    except Exception as exc:
        storage.set_status(job_id, JobStatus.failed, errors=[str(exc)])
        return JSONResponse(
            status_code=502,
            content={
                "job_id": job_id,
                "status": JobStatus.failed.value,
                "errors": [str(exc)],
            },
        )


@router.post("/{job_id}/stitch", response_model=StitchResponse)
def stitch_job(job_id: str):
    record = storage.get_job(job_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if record.features is None:
        raise HTTPException(
            status_code=409,
            detail="Job has not been parsed yet",
        )
    lines = lines_for(record.transcript)
    note = stitch_note(record.features, lines)
    storage.save_note(job_id, note)
    return StitchResponse(
        job_id=job_id,
        status=JobStatus.stitched,
        note=note,
        lines=lines,
    )
