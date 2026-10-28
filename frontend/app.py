"""SheetPilot AI — Streamlit chat frontend for the JYSK case study."""

import hashlib
import os
import json
import logging
import re
from io import BytesIO

import httpx
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
import hashlib
import os
import json
import logging
import re
import sys
from io import BytesIO
from pathlib import Path

# Ensure the project root is importable when Streamlit
# executes frontend/app.py directly.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")

st.set_page_config(page_title="SheetPilot AI | JYSK Case Study", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
/* SheetPilot: force readable contrast regardless of browser/Streamlit theme. */
:root {
  color-scheme: light;
  --sp-navy: #142B52;
  --sp-blue: #2058B5;
  --sp-muted: #526681;
  --sp-border: #DCE6F4;
}
html, body, .stApp, [data-testid="stAppViewContainer"],
[data-testid="stMain"], [data-testid="stMainBlockContainer"] {
  background: #F6F8FC !important;
  color: var(--sp-navy) !important;
}
[data-testid="stHeader"] { background: #F6F8FC !important; }
[data-testid="stToolbar"] { color: #263C5A !important; }
[data-testid="stSidebar"], [data-testid="stSidebarContent"] {
  background: #EAF1FC !important;
  color: var(--sp-navy) !important;
}
[data-testid="stSidebar"] {
  border-right: 1px solid #CEDDF1 !important;
}
[data-testid="stSidebar"] *, [data-testid="stMain"] p,
[data-testid="stMain"] li, [data-testid="stMain"] label,
[data-testid="stMain"] h1, [data-testid="stMain"] h2,
[data-testid="stMain"] h3, [data-testid="stMain"] h4 {
  color: var(--sp-navy);
}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] *,
[data-testid="stMain"] [data-testid="stCaptionContainer"] * {
  color: var(--sp-muted) !important;
}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
  background: #FFFFFF !important;
  border: 1px dashed #A4B9D8 !important;
}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] * {
  color: var(--sp-navy) !important;
}
[data-testid="stSidebar"] [data-testid="stFileUploaderFile"] {
  background: #FFFFFF !important;
  border-radius: 10px;
}
[data-testid="stSidebar"] [data-testid="stFileUploaderFile"] * {
  color: var(--sp-navy) !important;
}
[data-testid="stChatMessage"] {
  background: #FFFFFF !important;
  border: 1px solid var(--sp-border) !important;
  border-radius: 16px !important;
  padding: 1rem 1.15rem !important;
  box-shadow: 0 3px 14px rgba(20,43,82,.04);
  margin-bottom: .8rem;
}
[data-testid="stChatMessage"] *,
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] span {
  color: var(--sp-navy) !important;
}
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
  color: var(--sp-navy) !important;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
  background: #E8F1FF !important;
  border-color: #C9DCF8 !important;
}
[data-testid="stChatMessageAvatarAssistant"] {
  background: #DCEAFF !important;
}
[data-testid="stChatMessageAvatarUser"] {
  background: #2058B5 !important;
}
[data-testid="stBottom"], [data-testid="stBottomBlockContainer"],
[data-testid="stChatInputContainer"] {
  background: #F6F8FC !important;
}
[data-testid="stChatInput"] {
  background: #FFFFFF !important;
  border: 1px solid #B5C9E5 !important;
  border-radius: 16px !important;
  box-shadow: 0 6px 22px rgba(20,43,82,.08);
}
[data-testid="stChatInput"] textarea,
[data-testid="stChatInput"] textarea::placeholder {
  color: #253B5D !important;
  -webkit-text-fill-color: #253B5D !important;
  opacity: 1 !important;
}
[data-testid="stChatInput"] button { color: #2058B5 !important; }
[data-testid="stSidebar"] [data-testid="stExpander"] {
  background: #F9FBFF !important;
  border: 1px solid #DCE6F4 !important;
  border-radius: 12px;
}
[data-testid="stAlert"] p, [data-testid="stAlert"] span {
  color: #17385D !important;
}
.stButton > button[kind="primary"],
.stDownloadButton > button[kind="primary"] {
  background: #2058B5 !important;
  color: #FFFFFF !important;
  border: 1px solid #2058B5 !important;
  border-radius: 10px !important;
}
.stDownloadButton > button[kind="primary"] * { color: #FFFFFF !important; }
.block-container {
  max-width: 1050px !important;
  padding-top: 2rem !important;
  padding-bottom: 6rem !important;
}
.pilot-brand {
  font-size: 2.2rem;
  line-height: 1.2;
  font-weight: 800;
  letter-spacing: -.055em;
  color: #142B52 !important;
}
.pilot-brand span { color: #2365D3 !important; }
.pilot-subtitle {
  color: #526681 !important;
  margin-top: .25rem;
  margin-bottom: 1.5rem;
}
.pilot-badge {
  display: inline-block;
  background: #DFEBFF;
  color: #2058B5 !important;
  border-radius: 999px;
  padding: .32rem .85rem;
  font-size: .75rem;
  font-weight: 750;
  letter-spacing: .08em;
  margin-bottom: .8rem;
}
</style>
""", unsafe_allow_html=True)

DEFAULTS = {
    "file_id": None,
    "filename": None,
    "file_bytes": None,
    "file_signature": None,
    "messages": [],
    "agent_result": None,
    "download_bytes": None,
    "upload_error": None,
    "suggested_questions": [],
    "suggestions_signature": None,
    "pending_suggested_prompt": None,
    "pending_chart_spec": None,
    "version_notice": None,
}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


def reset_file_state():
    for key, value in DEFAULTS.items():
        st.session_state[key] = [] if key == "messages" else value


def api_error(response: httpx.Response) -> str:
    try:
        payload = response.json()
        detail = payload.get("detail", response.text) if isinstance(payload, dict) else payload
    except ValueError:
        detail = response.text
    return str(detail)


def fetch_workbook(download_url: str) -> bytes:
    # Download links are returned by our own backend; avoid accepting arbitrary hosts.
    if not download_url.startswith("/api/files/"):
        raise ValueError("Unexpected download URL returned by the backend.")
    with httpx.Client(timeout=60) as client:
        response = client.get(f"{BACKEND_URL}{download_url}")
        response.raise_for_status()
        return response.content


def upload_spreadsheet(name: str, content: bytes, signature: str) -> None:
    with httpx.Client(timeout=60) as client:
        response = client.post(f"{BACKEND_URL}/api/upload", files={"file": (name, content)})
        response.raise_for_status()
        payload = response.json()
    reset_file_state()
    st.session_state.file_id = payload["file_id"]
    st.session_state.filename = name
    st.session_state.file_bytes = content
    st.session_state.file_signature = signature


def run_instruction(prompt: str) -> tuple[str, bool]:
    with httpx.Client(timeout=180) as client:
        response = client.post(
            f"{BACKEND_URL}/api/agent/run",
            json={"file_id": st.session_state.file_id, "instruction": prompt},
        )
        response.raise_for_status()
        result = response.json()

    st.session_state.agent_result = result
    message = result.get("message") or "Instruction processed."
    success = bool(result.get("success"))
    if not success:
        errors = result.get("errors") or []
        if errors:
            message += "\n\n" + "\n".join(str(error) for error in errors)
    else:
        download_url = result.get("download_url")
        if download_url:
            try:
                st.session_state.download_bytes = fetch_workbook(download_url)
            except (httpx.HTTPError, ValueError) as exc:
                message += f"\n\n⚠️ Operation succeeded, but downloading the workbook failed: {exc}"
    if success and st.session_state.download_bytes:
        spec = _chart_spec(prompt, result, st.session_state.download_bytes)
        st.session_state.pending_chart_spec = spec
    else:
        st.session_state.pending_chart_spec = None
    return message, success




def _match_column(columns: list[str], candidate: str | None) -> str | None:
    """Match agent tool arguments to actual workbook column names."""
    if not isinstance(candidate, str) or not candidate.strip():
        return None
    normalized = lambda value: re.sub(r"[^a-z0-9]", "", str(value).casefold())
    for column in columns:
        if normalized(column) == normalized(candidate):
            return column
    return None


def _chart_spec(prompt: str, result: dict, workbook_bytes: bytes) -> dict | None:
    """Create a lightweight, serializable chart spec from a successful chart action.

    Uses the actual updated workbook, never invented chart data.
    """
    actions = result.get("actions_executed") or []
    chart_actions = [
        action for action in actions
        if "chart" in str(action.get("tool", "")).lower()
    ]
    if not chart_actions:
        return None

    action = chart_actions[-1]
    args = action.get("arguments") or {}
    if not isinstance(args, dict):
        return None

    chart_type_text = " ".join([
        str(args.get("chart_type", "")),
        str(args.get("type", "")),
        str(action.get("tool", "")),
        prompt,
    ]).casefold()
    if "scatter" in chart_type_text:
        chart_type = "scatter"
    elif "line" in chart_type_text or "trend" in chart_type_text:
        chart_type = "line"
    elif "pie" in chart_type_text or "donut" in chart_type_text:
        chart_type = "pie"
    else:
        chart_type = "bar"

    try:
        book = pd.ExcelFile(BytesIO(workbook_bytes))
        sheet_candidate = next(
            (args[key] for key in ("sheet_name", "sheet", "worksheet")
             if isinstance(args.get(key), str)), None
        )
        sheet = next(
            (name for name in book.sheet_names
             if name.casefold() == str(sheet_candidate).casefold()),
            book.sheet_names[0],
        )
        frame = pd.read_excel(book, sheet_name=sheet)
    except Exception as exc:
        logging.getLogger("sheetpilot").warning("Chart preview unavailable: %s", exc)
        return None

    columns = [str(c) for c in frame.columns]
    x = None
    y = None
    for key in ("x_column", "x_axis", "category_column", "label_column", "x", "categories"):
        x = _match_column(columns, args.get(key))
        if x:
            break
    for key in ("y_column", "y_axis", "value_column", "values_column", "y", "values"):
        y = _match_column(columns, args.get(key))
        if y:
            break

    # Some chart tools use column names under generic argument keys.
    if not x or not y:
        for key, value in args.items():
            if not isinstance(value, str):
                continue
            match = _match_column(columns, value)
            if not match:
                continue
            if not x and any(word in key.lower() for word in ("category", "label", "x_")):
                x = match
            if not y and any(word in key.lower() for word in ("value", "metric", "y_")):
                y = match

    # Do not guess axes if the tool didn't specify them: use clear prompt references.
    if not x or not y:
        mentioned = [
            column for column in columns
            if re.search(r"(?<!\\w)" + re.escape(column) + r"(?!\\w)", prompt, re.I)
        ]
        if len(mentioned) >= 2:
            # "Revenue by Product" means y=Revenue, x=Product.
            if re.search(r"\\bby\\b", prompt, re.I):
                before, after = re.split(r"\\bby\\b", prompt, maxsplit=1, flags=re.I)
                y = y or next((c for c in mentioned if c.lower() in before.lower()), None)
                x = x or next((c for c in mentioned if c.lower() in after.lower()), None)
            if not x or not y:
                numeric = [c for c in mentioned if pd.api.types.is_numeric_dtype(frame[c])]
                categorical = [c for c in mentioned if c not in numeric]
                y = y or (numeric[0] if numeric else None)
                x = x or (categorical[0] if categorical else None)

    if not x or not y or x == y or frame.empty:
        return None

    return {
        "sheet": sheet,
        "chart_type": chart_type,
        "x": x,
        "y": y,
        "title": str(args.get("title") or f"{y} by {x}"),
    }


def render_chat_chart(spec: dict, workbook_bytes: bytes) -> None:
    """Render an interactive Plotly chart using actual workbook values."""
    try:
        frame = pd.read_excel(BytesIO(workbook_bytes), sheet_name=spec["sheet"])
        x, y = spec["x"], spec["y"]
        if x not in frame or y not in frame:
            st.info("Chart columns are no longer available in this workbook.")
            return
        data = frame[[x, y]].dropna()
        if data.empty:
            st.info("There is no non-empty data available for this chart.")
            return
        kind = spec["chart_type"]
        if kind in ("bar", "pie"):
            if not pd.api.types.is_numeric_dtype(data[y]):
                st.info("This chart needs a numeric value column.")
                return
            data = data.groupby(x, dropna=False, as_index=False)[y].sum()
            data = data.sort_values(y, ascending=False).head(30)
        elif kind == "line":
            data = data.sort_values(x).head(500)
        else:
            data = data.head(2000)

        options = {"title": spec["title"], "template": "plotly_white"}
        if kind == "pie":
            fig = px.pie(data, names=x, values=y, **options)
        elif kind == "line":
            fig = px.line(data, x=x, y=y, markers=True, **options)
        elif kind == "scatter":
            fig = px.scatter(data, x=x, y=y, **options)
        else:
            fig = px.bar(data, x=x, y=y, **options)
        fig.update_layout(margin=dict(l=10, r=10, t=55, b=15))
        st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})
    except Exception as exc:
        logging.getLogger("sheetpilot").warning("Could not render chat chart: %s", exc)
        st.info("Interactive chart preview unavailable; the Excel output remains downloadable.")

def workbook_schema_summary(content: bytes, filename: str) -> dict:
    """Read workbook metadata only; never send cell values to the LLM."""
    extension = os.path.splitext(filename)[1].lower()
    sheets = []
    if extension in (".xlsx", ".xlsm"):
        excel = pd.ExcelFile(BytesIO(content))
        for sheet_name in excel.sheet_names[:8]:
            frame = pd.read_excel(excel, sheet_name=sheet_name, nrows=30)
            sheets.append({
                "sheet": sheet_name,
                "columns": [
                    {"name": str(column), "dtype": str(frame[column].dtype)}
                    for column in frame.columns[:35]
                ],
            })
    else:
        frame = pd.read_csv(
            BytesIO(content), sep="\t" if extension == ".tsv" else ",", nrows=30
        )
        sheets.append({
            "sheet": "Data",
            "columns": [
                {"name": str(column), "dtype": str(frame[column].dtype)}
                for column in frame.columns[:35]
            ],
        })
    return {"filename": filename, "sheets": sheets}


def fallback_questions(schema: dict) -> list[str]:
    """Provide relevant questions even if Gemini is unavailable."""
    sheets = schema.get("sheets") or []
    columns = [col["name"] for sheet in sheets for col in sheet.get("columns", [])]
    numeric = [
        col["name"] for sheet in sheets for col in sheet.get("columns", [])
        if any(t in col["dtype"] for t in ("int", "float"))
    ]
    text_cols = [col for col in columns if col not in numeric]
    options = ["Summarize this workbook", "Check for missing values and duplicate rows"]
    if numeric:
        options.append(f"Show summary statistics for {numeric[0]}")
    if numeric and text_cols:
        options.append(f"Create a bar chart of {numeric[0]} by {text_cols[0]}")
    options.append("List all columns and sheets")
    return options[:5]


def generate_suggested_questions(schema: dict) -> list[str]:
    """Ask Gemini for workbook-specific suggestions; fall back if unavailable."""
    fallback = fallback_questions(schema)
    try:
        from google.genai import types
        from backend.app.agents.gemini_client import get_gemini_client, get_gemini_model

        client = get_gemini_client()
        try:
            response = client.models.generate_content(
                model=get_gemini_model(),
                contents=(
                    "You are SheetPilot AI, an Excel assistant. Based ONLY on the workbook "
                    "metadata below, propose exactly 5 practical, distinct user instructions "
                    "that the assistant can execute. Prefer useful analysis, summaries, "
                    "formulas or charts. Use actual column names. Do not assume data values. "
                    "Return a JSON object with key 'questions' containing a list of strings. "
                    "Each instruction must be 3 to 110 characters long. Metadata: "
                    + json.dumps(schema, ensure_ascii=False)
                ),
                config=types.GenerateContentConfig(
                    temperature=0.3, response_mime_type="application/json"
                ),
            )
        finally:
            client.close()
        parsed = json.loads(response.text or "{}")
        items = parsed.get("questions", []) if isinstance(parsed, dict) else []
        questions = []
        if isinstance(items, list):
            for item in items:
                if isinstance(item, str) and 3 <= len(item.strip()) <= 110:
                    item = item.strip()
                    if item.casefold() not in {q.casefold() for q in questions}:
                        questions.append(item)
        return questions[:5] if len(questions) >= 3 else fallback
    except Exception as exc:
        logging.getLogger("sheetpilot").warning(
            "Question suggestions unavailable; using local fallback: %s", exc
        )
        return fallback


def ensure_suggested_questions() -> None:
    """Generate once per upload; avoid extra Gemini calls on Streamlit reruns."""
    signature = st.session_state.file_signature
    if not signature or signature == st.session_state.suggestions_signature:
        return
    st.session_state.suggestions_signature = signature
    try:
        schema = workbook_schema_summary(
            st.session_state.file_bytes, st.session_state.filename
        )
        st.session_state.suggested_questions = generate_suggested_questions(schema)
    except Exception as exc:
        logging.getLogger("sheetpilot").warning("Could not inspect workbook: %s", exc)
        st.session_state.suggested_questions = [
            "Summarize this workbook", "List all columns and sheets"
        ]


def select_suggested_question(question: str) -> None:
    st.session_state.pending_suggested_prompt = question

# ============================================================
# PHASE 8.3 — VERSION HISTORY, UNDO AND RESTORE
# ============================================================


def fetch_version_history() -> dict:
    """Fetch saved versions for the currently uploaded workbook."""

    file_id = st.session_state.file_id

    if not file_id:
        raise ValueError("Upload a workbook first.")

    with httpx.Client(timeout=30) as client:
        response = client.get(
            f"{BACKEND_URL}/api/files/{file_id}/versions"
        )
        response.raise_for_status()
        return response.json()


def apply_workbook_version(
    operation: str,
    version: int | None = None,
) -> dict:
    """
    Undo or restore a workbook version.

    Refresh the workbook bytes after the backend succeeds.
    """

    file_id = st.session_state.file_id

    if not file_id:
        raise ValueError("Upload a workbook first.")

    if operation == "undo":
        endpoint = f"/api/files/{file_id}/undo"

    elif operation == "restore":
        if version is None:
            raise ValueError("Select a version to restore.")

        endpoint = f"/api/files/{file_id}/restore/{version}"

    else:
        raise ValueError(f"Unsupported operation: {operation}")

    with httpx.Client(timeout=60) as client:
        response = client.post(
            f"{BACKEND_URL}{endpoint}"
        )
        response.raise_for_status()
        result = response.json()

    if not result.get("success"):
        raise ValueError(
            result.get("message", "Version operation failed.")
        )

    download_url = result.get(
        "download_url",
        f"/api/files/{file_id}",
    )

    # Always refresh the workbook after Undo or Restore.
    updated_bytes = fetch_workbook(download_url)

    st.session_state.download_bytes = updated_bytes

    # The last AI execution details no longer describe
    # the currently selected workbook state.
    st.session_state.agent_result = None
    st.session_state.pending_chart_spec = None

    restored_version = result.get("version") or {}
    version_number = restored_version.get("version", version)

    st.session_state.version_notice = (
        f"Workbook restored to Version {version_number}."
    )

    return result


with st.sidebar:
    st.markdown('<div class="pilot-brand">SheetPilot <span>AI</span></div>', unsafe_allow_html=True)
    st.caption("JYSK · AI Engineering Case Study")
    st.divider()
    st.subheader("📁 Your workbook")

    uploaded_file = st.file_uploader(
        "Upload Excel or CSV", type=["xlsx", "xlsm", "csv", "tsv"],
        accept_multiple_files=False, key="workbook_upload",
    )
    if uploaded_file is not None:
        content = uploaded_file.getvalue()
        signature = hashlib.sha256(uploaded_file.name.encode("utf-8") + content).hexdigest()
        if signature != st.session_state.file_signature:
            try:
                with st.spinner("Uploading workbook..."):
                    upload_spreadsheet(uploaded_file.name, content, signature)
            except httpx.HTTPStatusError as exc:
                st.error(f"Upload failed: {api_error(exc.response)}")
            except httpx.RequestError as exc:
                st.error(f"Connection failed: {exc}")
            except (KeyError, ValueError) as exc:
                st.error(f"Unexpected upload response: {exc}")
    elif st.session_state.file_id is not None:
        reset_file_state()

    if st.session_state.file_id:
        st.success(f"Ready: {st.session_state.filename}")
        if st.session_state.download_bytes:
            st.download_button(
                "⬇️ Download updated Excel",
                data=st.session_state.download_bytes,
                file_name="sheetpilot_output.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary", width="stretch",
            )
                    # ====================================================
        # PHASE 8.3 — WORKBOOK VERSION CONTROLS
        # ====================================================

        if st.session_state.version_notice:
            st.success(st.session_state.version_notice)
            st.session_state.version_notice = None

        with st.expander(
            "🕒 Version History & Undo",
            expanded=False,
        ):

            try:
                history = fetch_version_history()

                versions = history.get("versions", [])
                current_version = history.get("current_version")

                if not versions:
                    st.info("No workbook versions available.")

                else:
                    st.caption(
                        f"{len(versions)} saved version(s)"
                    )

                    st.markdown(
                        f"**Current version:** {current_version}"
                    )

                    # ----------------------------------------
                    # UNDO BUTTON
                    # ----------------------------------------

                    can_undo = (
                        current_version is not None
                        and any(
                            item["version"] < current_version
                            for item in versions
                        )
                    )

                    if st.button(
                        "↩ Undo last change",
                        key="undo_workbook_button",
                        disabled=not can_undo,
                        use_container_width=True,
                    ):

                        with st.spinner(
                            "Restoring previous version..."
                        ):
                            apply_workbook_version("undo")

                        st.rerun()

                    st.divider()

                    # ----------------------------------------
                    # VERSION SELECTOR
                    # ----------------------------------------

                    version_numbers = [
                        item["version"]
                        for item in reversed(versions)
                    ]

                    version_lookup = {
                        item["version"]: item
                        for item in versions
                    }

                    selected_version = st.selectbox(
                        "Select a workbook version",
                        options=version_numbers,
                        index=0,
                        format_func=lambda number: (
                            f"Version {number} — "
                            f"{version_lookup[number]['description']}"
                            + (
                                " (Current)"
                                if number == current_version
                                else ""
                            )
                        ),
                        key="selected_workbook_version",
                    )

                    selected_details = version_lookup[
                        selected_version
                    ]

                    st.caption(
                        "Saved: "
                        + selected_details.get(
                            "timestamp",
                            "Unknown",
                        )
                    )

                    # ----------------------------------------
                    # RESTORE BUTTON
                    # ----------------------------------------

                    if st.button(
                        "♻ Restore selected version",
                        key="restore_workbook_button",
                        disabled=(
                            selected_version == current_version
                        ),
                        use_container_width=True,
                    ):

                        with st.spinner(
                            "Restoring workbook..."
                        ):
                            apply_workbook_version(
                                operation="restore",
                                version=selected_version,
                            )

                        st.rerun()

            except httpx.HTTPStatusError as exc:
                st.error(
                    f"Version history error: "
                    f"{api_error(exc.response)}"
                )

            except httpx.RequestError as exc:
                st.error(
                    f"Cannot connect to version history: {exc}"
                )

            except (ValueError, KeyError, TypeError) as exc:
                st.error(
                    f"Version operation failed: {exc}"
                )
        with st.expander("📄 Preview workbook", expanded=False):
            try:
                # Prefer latest generated workbook so preview reflects chat edits.
                current_bytes = st.session_state.download_bytes or st.session_state.file_bytes
                current_name = "output.xlsx" if st.session_state.download_bytes else st.session_state.filename
                ext = os.path.splitext(current_name)[1].lower()
                if ext in (".xlsx", ".xlsm"):
                    excel = pd.ExcelFile(BytesIO(current_bytes))
                    sheet_name = st.selectbox("Sheet", excel.sheet_names, key="preview_sheet")
                    frame = pd.read_excel(excel, sheet_name=sheet_name, nrows=100)
                else:
                    frame = pd.read_csv(BytesIO(current_bytes), sep="\t" if ext == ".tsv" else ",", nrows=100)
                st.dataframe(frame, hide_index=True, width="stretch")
                st.caption(f"Showing up to 100 rows · {len(frame.columns)} columns")
            except Exception as exc:
                st.warning(f"Preview unavailable: {exc}")
    else:
        st.info("Upload a spreadsheet to start chatting.")

    st.divider()
    try:
        health = httpx.get(f"{BACKEND_URL}/health", timeout=3)
        health.raise_for_status()
        st.caption("🟢 Backend connected")
    except httpx.HTTPError:
        st.caption("🔴 Backend offline — start FastAPI on port 8000")

    if st.session_state.agent_result:
        with st.expander("⚙️ Last execution details"):
            result = st.session_state.agent_result
            actions = result.get("actions_executed") or []
            st.metric("Operations executed", len(actions))
            for index, action in enumerate(actions, start=1):
                st.markdown(f"**{index}. {action.get('tool', 'Unknown')}**")
                st.json(action.get("arguments") or {})
            if result.get("errors"):
                st.error("\n".join(map(str, result["errors"])))

if st.session_state.file_id:
    ensure_suggested_questions()

# A single self-contained HTML block avoids Streamlit markdown line-box clipping.
st.markdown(
    """<section style="padding:18px 0 26px; margin:0; overflow:visible; min-height:190px;">
      <div style="display:inline-flex; align-items:center; min-height:30px;
                  padding:6px 14px; border-radius:999px; background:#DFEBFF;
                  color:#2058B5; font-size:12px; font-weight:800;
                  line-height:18px; letter-spacing:1.5px; box-sizing:border-box;">
        JYSK · CASE STUDY
      </div>
      <h1 style="color:#142B52; font-size:clamp(32px,4vw,48px); font-weight:800;
                 letter-spacing:-1.5px; line-height:1.25; margin:15px 0 8px;
                 padding:4px 0; overflow:visible;">
        SheetPilot <span style="color:#2365D3;">AI</span>
      </h1>
      <p style="color:#526681; font-size:17px; line-height:1.6;
                margin:0; padding:0;">
        Your intelligent spreadsheet copilot ·
      </p>
    </section>""",
    unsafe_allow_html=True,
)

if not st.session_state.messages:
    st.markdown("### 👋 What would you like to do with your spreadsheet?")
    st.write("Upload a workbook using the sidebar, then ask questions:)")
    st.caption("You can also ask for formatting, summaries, charts, or follow-up changes.")


if st.session_state.file_id and st.session_state.suggested_questions:
    with st.container():
        st.markdown("#### ✨ Suggested questions for your workbook")
        st.caption("Generated from your sheet names and column types. Click to ask.")
        questions = st.session_state.suggested_questions
        for row_start in range(0, len(questions), 2):
            columns = st.columns(2)
            for offset, question in enumerate(questions[row_start:row_start + 2]):
                with columns[offset]:
                    st.button(
                        question,
                        key=f"suggestion_{row_start + offset}",
                        use_container_width=True,
                        on_click=select_suggested_question,
                        args=(question,),
                    )
    st.divider()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("chart_spec") and message.get("chart_bytes"):
            render_chat_chart(message["chart_spec"], message["chart_bytes"])

# At the page root (not inside a tab or expander), chat_input is pinned to the bottom.
prompt = st.chat_input(
    "Message SheetPilot AI…",
    disabled=st.session_state.file_id is None,
    key="sheetpilot_chat_input",
)
selected_prompt = st.session_state.pending_suggested_prompt
if selected_prompt:
    st.session_state.pending_suggested_prompt = None
    prompt = selected_prompt

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("SheetPilot is working on your spreadsheet..."):
            try:
                message, success = run_instruction(prompt)
            except httpx.HTTPStatusError as exc:
                message, success = f"API error: {api_error(exc.response)}", False
            except httpx.RequestError as exc:
                message, success = f"Connection error: {exc}", False
            except (ValueError, KeyError) as exc:
                message, success = f"Unexpected response: {exc}", False
        if success:
            st.markdown(message)
        else:
            st.error(message)
        chart_spec = st.session_state.pending_chart_spec if success else None
        chart_bytes = st.session_state.download_bytes if chart_spec else None
        if chart_spec and chart_bytes:
            render_chat_chart(chart_spec, chart_bytes)
        st.session_state.messages.append({
            "role": "assistant",
            "content": message,
            "chart_spec": chart_spec,
            "chart_bytes": chart_bytes,
        })
        st.session_state.pending_chart_spec = None
    st.rerun()
