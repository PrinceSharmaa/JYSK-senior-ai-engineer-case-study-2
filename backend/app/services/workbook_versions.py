"""Persistent workbook version history with repeatable undo and restore.

Snapshots are immutable. A cursor identifies the currently selected snapshot.
New edits after undo append a new snapshot, preserving prior history.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import os
import re
import shutil
import tempfile


class WorkbookVersionStore:
    def __init__(
        self,
        root: str | Path = "backend/storage/versions",
        max_versions: int = 25,
    ):
        if max_versions < 2:
            raise ValueError("max_versions must be at least 2")
        self.root = Path(root)
        self.max_versions = max_versions

    def _directory(self, file_id: str) -> Path:
        if not isinstance(file_id, str) or not re.fullmatch(r"[a-f0-9]{32}", file_id):
            raise ValueError("Invalid workbook file ID")
        return self.root / file_id

    def _read_state(self, file_id: str) -> dict:
        manifest = self._directory(file_id) / "versions.json"
        if not manifest.exists():
            return {"versions": [], "current_version": None}
        data = json.loads(manifest.read_text(encoding="utf-8"))
        if isinstance(data, list):  # Migrate the original Phase 8.3 manifest.
            return {
                "versions": data,
                "current_version": data[-1]["version"] if data else None,
            }
        return data

    def _write_state(self, folder: Path, state: dict) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        temp = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=folder,
                delete=False, suffix=".json",
            ) as handle:
                json.dump(state, handle, indent=2)
                temp = Path(handle.name)
            os.replace(temp, folder / "versions.json")
        finally:
            if temp is not None:
                temp.unlink(missing_ok=True)

    def list_versions(self, file_id: str) -> list[dict]:
        state = self._read_state(file_id)
        return [
            {**entry, "is_current": entry["version"] == state["current_version"]}
            for entry in state["versions"]
        ]

    def save_version(
        self, file_id: str, workbook_path: str | Path, description: str
    ) -> dict:
        source = Path(workbook_path)
        if not source.is_file():
            raise FileNotFoundError(source)
        folder = self._directory(file_id)
        folder.mkdir(parents=True, exist_ok=True)
        state = self._read_state(file_id)
        versions = state["versions"]
        number = max((item["version"] for item in versions), default=0) + 1
        snapshot = folder / f"v{number:06d}.xlsx"
        shutil.copy2(source, snapshot)
        entry = {
            "version": number,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "description": str(description)[:200],
        }
        versions.append(entry)
        state["current_version"] = number
        removed = versions[:-self.max_versions]
        state["versions"] = versions[-self.max_versions:]
        self._write_state(folder, state)
        for old in removed:
            (folder / f"v{old['version']:06d}.xlsx").unlink(missing_ok=True)
        return {**entry, "is_current": True}

    def _activate_version(
        self, file_id: str, version: int, current_workbook_path: str | Path
    ) -> dict:
        folder = self._directory(file_id)
        state = self._read_state(file_id)
        entry = next(
            (item for item in state["versions"] if item["version"] == version),
            None,
        )
        if entry is None:
            raise ValueError("Requested workbook version not found")
        source = folder / f"v{version:06d}.xlsx"
        if not source.is_file():
            raise FileNotFoundError(source)
        destination = Path(current_workbook_path)
        if destination.suffix.lower() != ".xlsx":
            raise ValueError("Restoration destination must be an .xlsx file")
        destination.parent.mkdir(parents=True, exist_ok=True)
        temp = None
        try:
            with tempfile.NamedTemporaryFile(
                dir=destination.parent, delete=False, suffix=".xlsx"
            ) as handle:
                temp = Path(handle.name)
            shutil.copyfile(source, temp)
            os.replace(temp, destination)
        finally:
            if temp is not None:
                temp.unlink(missing_ok=True)
        state["current_version"] = version
        self._write_state(folder, state)
        return {**entry, "is_current": True}

    def restore_version(
        self, file_id: str, version: int, current_workbook_path: str | Path
    ) -> dict:
        """Select a retained version without creating another snapshot."""
        return self._activate_version(file_id, version, current_workbook_path)

    def undo(self, file_id: str, current_workbook_path: str | Path) -> dict:
        """Move to the previous snapshot in chronological history."""
        state = self._read_state(file_id)
        versions = state["versions"]
        current = state["current_version"]
        index = next(
            (i for i, entry in enumerate(versions) if entry["version"] == current),
            -1,
        )
        if index <= 0:
            raise ValueError("No previous version to undo to")
        return self._activate_version(
            file_id, versions[index - 1]["version"], current_workbook_path
        )
