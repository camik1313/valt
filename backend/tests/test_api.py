# ============================================================
# test_api.py — automated tests for the API.
#
# These prove the endpoints actually work, without a browser. Run
# them with `pytest` from the backend/ folder. Passing tests are
# real evidence your API behaves correctly — the kind of rigor
# that stands out at a science fair.
#
# TestClient lets us call the app in-process (no server needed).
# ============================================================

import io

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    """The health endpoint should report ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_upload_rejects_non_video():
    """Uploading a text file (not a video) should be rejected with 400."""
    fake_text = io.BytesIO(b"i am not a video")
    response = client.post(
        "/upload",
        files={"file": ("notes.txt", fake_text, "text/plain")},
    )
    assert response.status_code == 400


def test_full_flow():
    """Upload -> analyze -> report -> history should all work together."""
    # 1) Upload a fake (but video-typed) file.
    fake_video = io.BytesIO(b"\x00\x00\x00\x18ftypmp42fake-bytes")
    up = client.post(
        "/upload",
        files={"file": ("jump.mp4", fake_video, "video/mp4")},
    )
    assert up.status_code == 200
    upload_id = up.json()["uploadId"]

    # 2) Analyze it.
    an = client.post(
        "/analyze",
        json={"uploadId": upload_id, "athleteName": "Test Athlete"},
    )
    assert an.status_code == 200
    analysis = an.json()
    assert analysis["athleteName"] == "Test Athlete"
    assert len(analysis["metrics"]) == 5  # five measurements

    # 3) Fetch the report by id.
    analysis_id = analysis["id"]
    rep = client.get(f"/report/{analysis_id}")
    assert rep.status_code == 200
    assert rep.json()["id"] == analysis_id

    # 4) The analysis should appear in history.
    hist = client.get("/history")
    assert hist.status_code == 200
    ids = [item["id"] for item in hist.json()]
    assert analysis_id in ids


def test_report_404():
    """Asking for a nonexistent analysis should return 404."""
    response = client.get("/report/does-not-exist")
    assert response.status_code == 404
