import os
import uuid
import tempfile
from pathlib import Path

from fastapi import UploadFile

from backend.app.services.workbook_versions import WorkbookVersionStore
from backend.app.tools.file_tools import (
    load_spreadsheet,
    save_workbook,
)


# ============================================================
# STORAGE CONFIGURATION
# ============================================================

STORAGE_DIR = Path(
    os.getenv(
        "SHEETPILOT_STORAGE_DIR",
        "backend/storage/uploads",
    )
)

SUPPORTED_EXTENSIONS = {
    ".xlsx",
    ".xlsm",
    ".csv",
    ".tsv",
}

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB

CHUNK_SIZE = 1024 * 1024  # 1 MB


# ============================================================
# PHASE 8.3 — WORKBOOK VERSION STORE
# ============================================================

VERSION_STORE = WorkbookVersionStore(
    root=STORAGE_DIR.parent / "versions",
    max_versions=25,
)


# ============================================================
# STORAGE HELPERS
# ============================================================

def ensure_storage_directory() -> None:
    """
    Ensure that the upload storage directory exists.
    """

    STORAGE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def validate_file_id(file_id: str) -> None:
    """
    Validate a file identifier before using it in a path.
    """

    try:
        parsed_id = uuid.UUID(hex=file_id)

        if parsed_id.hex != file_id:
            raise ValueError

    except (ValueError, AttributeError, TypeError):
        raise ValueError(
            "Invalid file identifier."
        )


# ============================================================
# UPLOAD SPREADSHEET
# ============================================================

async def save_uploaded_file(
    file: UploadFile,
) -> dict:
    """
    Validate and save an uploaded spreadsheet.

    Supported formats:
        - XLSX
        - XLSM
        - CSV
        - TSV

    Versioning:
        - Original upload is saved as Version 1.
        - Future AI modifications create new versions.
    """

    ensure_storage_directory()

    original_filename = file.filename or ""

    extension = Path(
        original_filename
    ).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            "Unsupported file type. "
            "Allowed: .xlsx, .xlsm, .csv, .tsv"
        )

    # Generate a unique identifier.
    file_id = uuid.uuid4().hex

    stored_filename = f"{file_id}{extension}"

    file_path = STORAGE_DIR / stored_filename

    total_size = 0

    try:

        # ----------------------------------------------------
        # STEP 1 — SAVE UPLOADED FILE
        # ----------------------------------------------------

        with open(file_path, "wb") as destination:

            while True:

                chunk = await file.read(
                    CHUNK_SIZE
                )

                if not chunk:
                    break

                total_size += len(chunk)

                if total_size > MAX_FILE_SIZE:
                    raise ValueError(
                        "File exceeds the 20 MB limit."
                    )

                destination.write(chunk)

        # ----------------------------------------------------
        # STEP 2 — VALIDATE SPREADSHEET
        # ----------------------------------------------------

        workbook = load_spreadsheet(
            file_path
        )

        # ----------------------------------------------------
        # STEP 3 — CREATE INITIAL VERSION SNAPSHOT
        # ----------------------------------------------------

        temporary_snapshot = None

        try:

            # Normalize uploaded workbook to XLSX.
            # CSV/TSV files are also stored as XLSX snapshots.
            with tempfile.NamedTemporaryFile(
                suffix=".xlsx",
                delete=False,
            ) as handle:

                temporary_snapshot = Path(
                    handle.name
                )

            save_workbook(
                workbook,
                temporary_snapshot,
            )

            # Create Version 1.
            VERSION_STORE.save_version(
                file_id=file_id,
                workbook_path=temporary_snapshot,
                description="Original uploaded workbook",
            )

        finally:

            if temporary_snapshot is not None:

                temporary_snapshot.unlink(
                    missing_ok=True
                )

    except Exception:

        # Remove an invalid or incomplete upload.
        file_path.unlink(
            missing_ok=True
        )

        raise

    finally:

        await file.close()

    return {
        "file_id": file_id,
        "filename": original_filename,
        "stored_filename": stored_filename,
        "size_bytes": total_size,
    }


# ============================================================
# GET LATEST DOWNLOADABLE FILE
# ============================================================

def get_file_path(
    file_id: str,
) -> Path:
    """
    Return the latest downloadable spreadsheet.

    Priority:
        1. Modified or restored XLSX workbook
        2. Original uploaded file
    """

    ensure_storage_directory()

    validate_file_id(file_id)

    generated_path = (
        STORAGE_DIR / f"{file_id}_output.xlsx"
    )

    if generated_path.is_file():
        return generated_path

    for extension in SUPPORTED_EXTENSIONS:

        candidate = (
            STORAGE_DIR / f"{file_id}{extension}"
        )

        if candidate.is_file():
            return candidate

    raise FileNotFoundError(
        "File not found."
    )


# ============================================================
# GET ORIGINAL UPLOADED FILE
# ============================================================

def get_original_file_path(
    file_id: str,
) -> Path:
    """
    Return the original uploaded spreadsheet.

    This function deliberately ignores generated outputs.
    """

    ensure_storage_directory()

    validate_file_id(file_id)

    for extension in SUPPORTED_EXTENSIONS:

        candidate = (
            STORAGE_DIR / f"{file_id}{extension}"
        )

        if candidate.is_file():
            return candidate

    raise FileNotFoundError(
        "Original file not found."
    )


# ============================================================
# SAVE AI-MODIFIED WORKBOOK
# ============================================================

def save_agent_output(
    file_id: str,
    workbook,
) -> Path:
    """
    Save the AI-modified workbook.

    Every successful modification creates a new version.
    """

    ensure_storage_directory()

    # Confirm that this file belongs to an existing upload.
    get_original_file_path(file_id)

    output_path = (
        STORAGE_DIR / f"{file_id}_output.xlsx"
    )

    # --------------------------------------------------------
    # STEP 1 — SAVE MODIFIED WORKBOOK
    # --------------------------------------------------------

    save_workbook(
        workbook,
        output_path,
    )

    # --------------------------------------------------------
    # STEP 2 — RECORD NEW VERSION
    # --------------------------------------------------------

    VERSION_STORE.save_version(
        file_id=file_id,
        workbook_path=output_path,
        description="AI spreadsheet modification",
    )

    return output_path


# ============================================================
# GET WORKBOOK FOR NEXT AI OPERATION
# ============================================================

def get_latest_workbook_path(
    file_id: str,
) -> Path:
    """
    Return the latest workbook for the AI agent.

    If an AI-modified or restored workbook exists, use it.

    Otherwise, use the original uploaded spreadsheet.
    """

    original_path = get_original_file_path(
        file_id
    )

    output_path = (
        STORAGE_DIR / f"{file_id}_output.xlsx"
    )

    if output_path.is_file():
        return output_path

    return original_path