# ============================================================
# conftest.py — shared test setup.
#
# Without this, API tests that POST to /upload and /analyze write their
# fake analyses and uploads into the REAL data folders (backend/data/),
# so running the test suite quietly filled the app's History page with
# "Test Athlete" entries. Every test now gets its own throwaway folders.
# ============================================================

import pytest

from app.config import settings


@pytest.fixture(autouse=True)
def isolated_data_dirs(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "analyses_dir", str(tmp_path / "analyses"))
