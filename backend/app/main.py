from fastapi import (
    FastAPI,
    File,
    HTTPException,
    UploadFile,
)

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from backend.app.services.conversation_memory import (
    get_conversation_history,
    add_conversation_message,
)
import logging

# ============================================================
# SHEETPILOT AI - IMPORTS
# ============================================================

from backend.app.agents.excel_agent import (
    run_excel_agent,
)

from backend.app.agents.response_generator import (
    generate_agent_response,
)

from backend.app.schemas.api_schemas import (
    UploadResponse,
    AgentRequest,
    AgentExecutionResponse,
)

from backend.app.services.file_storage import (
    save_uploaded_file,
    get_file_path,
    get_original_file_path,
    save_agent_output,
    get_latest_workbook_path,
)
from backend.app.services.file_storage import (
    STORAGE_DIR,
    VERSION_STORE,
)
from backend.app.tools.file_tools import (
    load_spreadsheet,
)


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
)

logger = logging.getLogger("sheetpilot")


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="SheetPilot AI",
    description=(
        "An intelligent Excel assistant powered by "
        "Google Gemini, LangGraph, FastAPI and Python."
    ),
    version="0.3.0",
)


# ============================================================
# CORS CONFIGURATION
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "http://localhost:8500",
        "http://127.0.0.1:8500",
    ],
    allow_credentials=False,
    allow_methods=[
        "GET",
        "POST",
    ],
    allow_headers=[
        "Content-Type",
    ],
)


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
def root():
    """
    Return basic application information.
    """

    return {
        "application": "SheetPilot AI",
        "status": "running",
        "version": "0.3.0",
        "features": [
            "Excel file upload",
            "Spreadsheet analysis",
            "Gemini AI agent",
            "LangGraph orchestration",
            "Excel formulas",
            "Formatting",
            "Charts",
            "Natural-language explanations",
            "Excel download",
        ],
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health_check():
    """
    Check whether the FastAPI service is running.
    """

    return {
        "status": "healthy",
        "service": "excel-agent-backend",
    }


# ============================================================
# UPLOAD SPREADSHEET
# ============================================================

@app.post(
    "/api/upload",
    response_model=UploadResponse,
)
async def upload_spreadsheet(
    file: UploadFile = File(...),
):
    """
    Upload an Excel or CSV spreadsheet.

    Supported formats:
    - XLSX
    - XLSM
    - CSV
    - TSV
    """

    try:
        logger.info(
            "Uploading spreadsheet: %s",
            file.filename,
        )

        result = await save_uploaded_file(
            file
        )

        logger.info(
            "File uploaded successfully: %s",
            result["file_id"],
        )

        return UploadResponse(
            file_id=result["file_id"],
            filename=result["filename"],
            size_bytes=result["size_bytes"],
        )

    except ValueError as exc:

        logger.warning(
            "Invalid upload: %s",
            exc,
        )

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception:

        logger.exception(
            "Unexpected error while uploading spreadsheet"
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to process uploaded file.",
        )


# ============================================================
# RUN GEMINI + LANGGRAPH AGENT
# ============================================================

@app.post(
    "/api/agent/run",
    response_model=AgentExecutionResponse,
)
def execute_agent(
    request: AgentRequest,
):
    """
    Execute a natural-language spreadsheet request.

    Workflow:

    1. Find uploaded spreadsheet.
    2. Load workbook.
    3. Execute Gemini + LangGraph agent.
    4. Validate and execute spreadsheet tools.
    5. Save successful workbook output.
    6. Generate a natural-language explanation.
    7. Return results to Streamlit.
    """

    try:

        # ----------------------------------------------------
        # STEP 1 - FIND UPLOADED FILE
        # ----------------------------------------------------

        logger.info(
            "Received agent request for file: %s",
            request.file_id,
        )

        file_path = get_latest_workbook_path(
            request.file_id
    )

        # ----------------------------------------------------
        # STEP 2 - LOAD WORKBOOK
        # ----------------------------------------------------

        workbook = load_spreadsheet(
            file_path
        )

        logger.info(
            "Workbook loaded successfully."
        )

        # ----------------------------------------------------
        # STEP 3 - RUN LANGGRAPH AGENT
        # ----------------------------------------------------

        logger.info(
            "Executing Gemini + LangGraph agent."
        )
        history = get_conversation_history(request.file_id)
        result = run_excel_agent(
            workbook=workbook,
            user_request=request.instruction,
            conversation_history=history,
        )

        # ----------------------------------------------------
        # STEP 4 - HANDLE AGENT FAILURE
        # ----------------------------------------------------

        if not result.success:

            logger.warning(
                "Agent execution failed: %s",
                result.errors,
            )

            return AgentExecutionResponse(
                success=False,
                file_id=request.file_id,
                message=result.message,
                actions_executed=result.actions_executed,
                errors=result.errors,
                download_url=None,
            )

        # ----------------------------------------------------
        # STEP 5 - VALIDATE WORKBOOK RESULT
        # ----------------------------------------------------

        if result.workbook is None:

            raise RuntimeError(
                "Agent completed successfully but "
                "returned no workbook."
            )

        # ----------------------------------------------------
        # STEP 6 - SAVE MODIFIED WORKBOOK
        # ----------------------------------------------------

        # ----------------------------------------------------
        # STEP 6 - SAVE MODIFIED WORKBOOK
        # ----------------------------------------------------

        READ_ONLY_TOOLS = {
            "list_sheets",
            "preview_sheet",
            "inspect_columns",
            "get_summary_statistics",
            "group_and_aggregate",
            "filter_rows",
            "get_top_n",
            "analyze_missing_values",
            "calculate_correlation",
            "list_charts",
        }

        has_modifications = any(
            action.get("tool") not in READ_ONLY_TOOLS
            for action in result.actions_executed
        )

        if has_modifications:
            output_path = save_agent_output(
                file_id=request.file_id,
                workbook=result.workbook,
            )

            logger.info(
                "Workbook modification saved: %s",
                output_path,
            )

        else:
            output_path = get_latest_workbook_path(
                request.file_id
            )

            logger.info(
                "Read-only request: no new workbook version created."
            )

        # ----------------------------------------------------
        # STEP 7 - GENERATE CONVERSATIONAL RESPONSE
        # ----------------------------------------------------

        logger.info(
            "Generating natural-language explanation."
        )

        try:

            ai_message = generate_agent_response(
                user_request=request.instruction,
                actions_executed=result.actions_executed,
            )

            logger.info(
                "AI explanation generated successfully."
            )

        except Exception as exc:

            logger.exception(
                "AI response generation failed: %s",
                exc,
            )

            # The Excel operations succeeded.
            # Do not discard the generated workbook
            # just because explanation generation failed.

            ai_message = (
                result.message
                + "\n\n"
                + "The spreadsheet operations completed "
                + "successfully, but the AI explanation "
                + "is temporarily unavailable. "
                + "Please check the Execution Details tab."
                )
        add_conversation_message(
            file_id=request.file_id,
            role="user",
            content=request.instruction,
        )

        add_conversation_message(
            file_id=request.file_id,
            role="assistant",
            content=ai_message,
        )
        # ----------------------------------------------------
        # STEP 8 - RETURN RESULT TO STREAMLIT
        # ----------------------------------------------------

        logger.info(
            "Agent request completed successfully."
        )

        return AgentExecutionResponse(
            success=True,
            file_id=request.file_id,
            message=ai_message,
            actions_executed=result.actions_executed,
            errors=[],
            download_url=(
                f"/api/files/{request.file_id}"
            ),
        )

    # ========================================================
    # ERROR HANDLING
    # ========================================================

    except FileNotFoundError as exc:

        logger.warning(
            "Requested file not found: %s",
            request.file_id,
        )

        raise HTTPException(
            status_code=404,
            detail="File not found.",
        ) from exc

    except ValueError as exc:

        logger.warning(
            "Invalid agent request: %s",
            exc,
        )

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        logger.exception(
            "Unexpected error during agent execution"
        )

        raise HTTPException(
            status_code=500,
            detail="Agent execution failed.",
        ) from exc


# ============================================================
# DOWNLOAD SPREADSHEET
# ============================================================

@app.get(
    "/api/files/{file_id}",
)
def download_file(
    file_id: str,
):
    """
    Download an uploaded or AI-modified spreadsheet.

    If a generated output exists, it is returned.
    Otherwise, the original uploaded file is returned.
    """

    try:

        file_path = get_file_path(
            file_id
        )

        logger.info(
            "Downloading file: %s",
            file_path.name,
        )

        return FileResponse(
            path=file_path,
            filename=file_path.name,
            media_type=(
                "application/octet-stream"
            ),
        )

    except FileNotFoundError as exc:

        raise HTTPException(
            status_code=404,
            detail="File not found.",
        ) from exc

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
  # ============================================================
# PHASE 8.3 — WORKBOOK VERSION HISTORY
# ============================================================


@app.get("/api/files/{file_id}/versions")
def get_workbook_versions(file_id: str):
    """Return the version history of an uploaded workbook."""
    try:
        get_original_file_path(file_id)

        versions = VERSION_STORE.list_versions(file_id)

        return {
            "file_id": file_id,
            "versions": versions,
            "total_versions": len(versions),
            "current_version": next(
                (
                    entry["version"]
                    for entry in versions
                    if entry.get("is_current")
                ),
                None,
            ),
        }

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail="Workbook not found.",
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@app.post("/api/files/{file_id}/undo")
def undo_workbook(file_id: str):
    """Restore the previous workbook version."""
    try:
        get_original_file_path(file_id)

        output_path = STORAGE_DIR / f"{file_id}_output.xlsx"

        restored = VERSION_STORE.undo(
            file_id=file_id,
            current_workbook_path=output_path,
        )

        return {
            "success": True,
            "file_id": file_id,
            "message": (
                f"Restored workbook version {restored['version']}."
            ),
            "version": restored,
            "download_url": f"/api/files/{file_id}",
        }

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail="Workbook or snapshot not found.",
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

@app.post("/api/files/{file_id}/restore/{version}")
def restore_workbook(file_id: str, version: int):
    """Restore a selected workbook version."""
    try:
        get_original_file_path(file_id)

        output_path = STORAGE_DIR / f"{file_id}_output.xlsx"

        restored = VERSION_STORE.restore_version(
            file_id=file_id,
            version=version,
            current_workbook_path=output_path,
        )

        return {
            "success": True,
            "file_id": file_id,
            "message": (
                f"Restored workbook version {restored['version']}."
            ),
            "version": restored,
            "download_url": f"/api/files/{file_id}",
        }

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail="Workbook or snapshot not found.",
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc  