from fastapi import HTTPException, UploadFile

from app.storage import storage
from app.textutil import split_transcript

MAX_UPLOAD_BYTES = 2_000_000


async def create_job_from_upload(file: UploadFile) -> tuple[str, list[str]]:
    filename = (file.filename or "").lower()
    if not filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Upload a .txt transcript")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="File is empty")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File is too large")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="File is not valid UTF-8 text") from exc
    if not text.strip():
        raise HTTPException(status_code=400, detail="File is empty")
    job_id = storage.create_job(text)
    return job_id, split_transcript(text)
