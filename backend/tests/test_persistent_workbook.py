from pathlib import Path

import pytest
from openpyxl import Workbook, load_workbook

from backend.app.services import file_storage


def test_latest_workbook_uses_original_when_no_output(
    tmp_path,
    monkeypatch,
):
    original = tmp_path / "uploads" / "test_original.xlsx"
    original.parent.mkdir(parents=True)
    original.touch()

    monkeypatch.setattr(
        file_storage,
        "get_original_file_path",
        lambda file_id: original,
    )

    result = file_storage.get_latest_workbook_path("test")

    assert result == original


def test_latest_workbook_prefers_generated_output(
    tmp_path,
    monkeypatch,
):
    from backend.app.services import file_storage

    # Use the same directory for original and generated files.
    uploads = tmp_path / "uploads"
    uploads.mkdir()

    file_id = "test"

    original = uploads / f"{file_id}.xlsx"
    original.touch()

    generated = uploads / f"{file_id}_output.xlsx"
    generated.touch()

    # Point storage to the temporary test directory.
    monkeypatch.setattr(
        file_storage,
        "STORAGE_DIR",
        uploads,
    )

    monkeypatch.setattr(
        file_storage,
        "get_original_file_path",
        lambda requested_file_id: original,
    )

    result = file_storage.get_latest_workbook_path(file_id)

    assert result == generated