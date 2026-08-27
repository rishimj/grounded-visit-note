from fastapi.testclient import TestClient

from app.main import app
from app.storage import DiskJobStorage
import app.api.jobs as jobs_mod
import app.upload as upload_mod

client = TestClient(app)


def _use_tmp(monkeypatch, tmp_path):
    disk = DiskJobStorage(tmp_path)
    monkeypatch.setattr(jobs_mod, "storage", disk)
    monkeypatch.setattr(upload_mod, "storage", disk)
    return disk


def test_upload_get_list(tmp_path, monkeypatch):
    _use_tmp(monkeypatch, tmp_path)
    files = {"file": ("visit.txt", b"LINE ONE\nLINE TWO\n", "text/plain")}
    res = client.post("/api/jobs", files=files)
    assert res.status_code == 201
    body = res.json()
    assert body["status"] == "uploaded"
    assert body["lines"] == ["LINE ONE", "LINE TWO"]
    job_id = body["job_id"]
    got = client.get(f"/api/jobs/{job_id}")
    assert got.status_code == 200
    assert got.json()["note"] is None
    listed = client.get("/api/jobs")
    assert any(j["job_id"] == job_id for j in listed.json()["jobs"])


def test_upload_rejects_non_txt():
    res = client.post(
        "/api/jobs",
        files={"file": ("visit.pdf", b"x", "application/pdf")},
    )
    assert res.status_code == 400


def test_stitch_before_parse_409(tmp_path, monkeypatch):
    disk = _use_tmp(monkeypatch, tmp_path)
    job_id = disk.create_job("hello")
    res = client.post(f"/api/jobs/{job_id}/stitch")
    assert res.status_code == 409
