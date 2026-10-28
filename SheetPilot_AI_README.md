# SheetPilot AI

**An agentic spreadsheet assistant | JYSK Senior AI Engineer take-home case study**

SheetPilot AI enables users to inspect, analyze, and modify spreadsheets through natural-language instructions. It combines **Google Gemini** for planning, **LangGraph** for workflow orchestration, **FastAPI** for application services, and **Streamlit** for a conversational interface. Spreadsheet changes are performed by deterministic, validated Python tools rather than arbitrary model-generated code.

> **Project status:** Functional local prototype. The developer reported **110 passing automated tests**. This README describes the supplied implementation and reported results; it does not claim independent verification of the entire local repository or production readiness.

## Features

- **Conversational spreadsheet operations:** Ask for workbook structure, sheet previews, and data insights.
- **Excel automation:** Create calculated columns, apply formulas, format cells, and generate charts.
- **Follow-up context:** Refer to previously discussed columns or operations within the same conversation.
- **Persistent workbook edits:** Subsequent requests operate on the latest saved workbook output.
- **Structured planning and validation:** Gemini produces tool plans that are validated before execution.
- **Failure recovery:** Invalid plans and failed executions can trigger bounded retries and replanning.
- **Transactional execution:** Tools operate on a workbook copy; failed attempts do not commit partial edits.
- **Observability:** Structured traces record planning, validation, and execution timings, retry counts, and tool outcomes.
- **Downloadable results:** Retrieve the updated `.xlsx` workbook from the UI.

## Technology stack

| Layer | Technology | Responsibility |
| --- | --- | --- |
| Frontend | Streamlit | Chat, upload, preview, execution details, download |
| API | FastAPI + Pydantic | HTTP endpoints and request validation |
| Agent orchestration | LangGraph | Planner → validator → executor; retry routing |
| LLM | Google Gemini (`google-genai`) | Generate structured plans and user-facing explanations |
| Spreadsheet operations | openpyxl, pandas | Workbook edits, tabular inspection, previews |
| State | Conversation memory + local workbook storage | Follow-up context and latest-workbook selection |
| Quality | pytest | Automated tests |
| Monitoring | Python structured logging | Request-level and stage-level traces |

## Architecture

![SheetPilot AI system architecture](docs/architecture.svg)

The editable Mermaid version is available at [`docs/architecture.md`](docs/architecture.md). The architecture separates **probabilistic planning** from **validated, deterministic execution**.

### Request lifecycle

1. **Upload:** Streamlit sends the spreadsheet to `POST /api/upload`. FastAPI stores the uploaded file and returns a file identifier.
2. **Ask:** The user submits an instruction through the chat interface. Streamlit sends `file_id` and `instruction` to `POST /api/agent/run`.
3. **Load context:** The backend retrieves the latest workbook and conversation history, then prepares workbook metadata for the planner.
4. **Plan:** Gemini returns a structured action plan using the supported tool definitions.
5. **Validate:** Pydantic-based schemas and tool-specific argument validation check the proposed actions. Invalid plans can be replanned within configured retry limits.
6. **Execute:** LangGraph routes validated actions to the Excel tool registry. Execution uses a cloned workbook; failed attempts can be replanned without committing partial changes.
7. **Persist:** On success, the backend saves the updated workbook and records conversation context.
8. **Respond:** A natural-language explanation is generated and returned to Streamlit. The updated file is available for download.
9. **Observe:** Structured traces capture the agent outcome, tool successes/failures, retry counts, and stage durations.

## Repository structure

Representative structure based on the supplied code; additional local modules and tests may be present.

```text
jysk-excel-ai-agent/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI endpoints
│   │   ├── agents/
│   │   │   ├── excel_agent.py         # LangGraph orchestration and retries
│   │   │   ├── agent_schemas.py       # Structured plan/result schemas
│   │   │   ├── tool_validation.py     # Tool argument validation
│   │   │   └── response_generator.py  # Natural-language explanations
│   │   └── services/
│   │       ├── file_storage.py        # Uploaded and generated workbooks
│   │       ├── workbook_transaction.py# Clone-before-execute safety
│   │       ├── conversation_memory.py # Conversation history
│   │       └── agent_observability.py # Structured execution tracing
│   ├── tests/                       # pytest suite
│   └── storage/uploads/             # Runtime files (do not commit)
├── frontend/
│   └── app.py                        # Streamlit UI
├── docs/
│   ├── architecture.md              # Mermaid source
│   ├── architecture.svg             # Architecture diagram
│   └── architecture.png             # Preview image
├── .env                              # Local secrets (do not commit)
└── README.md
```

## Getting started

### Prerequisites

- Python **3.12**
- A valid Google Gemini API key
- Project dependencies installed according to the repository's existing `pyproject.toml` / lockfile or requirements file

### 1. Clone and enter the project

```bash
git clone <YOUR_REPOSITORY_URL>
cd jysk-excel-ai-agent
```

### 2. Create an environment and install dependencies

If the repository uses **uv**:

```bash
uv sync
```

Otherwise, use the project's existing dependency manifest and a Python 3.12 virtual environment. **Do not substitute an incomplete package list for the project's lockfile.**

### 3. Configure environment variables

Create `.env` in the project root and use the **exact Gemini key variable expected by `backend/app`** (check your existing configuration helper):

```dotenv
# Set the variable name used by your Gemini client configuration.
# Example only; verify against the code before running:
GEMINI_API_KEY=your_api_key_here
BACKEND_URL=http://127.0.0.1:8000
```

Never commit `.env`, API keys, or uploaded spreadsheets.

### 4. Start FastAPI

Run from the project root, using the project's environment:

```bash
python -m uvicorn backend.app.main:app --reload --port 8000
```

API documentation is available locally at `http://127.0.0.1:8000/docs`; the health endpoint is `GET /health`.

### 5. Start Streamlit

In a second terminal:

```bash
streamlit run frontend/app.py
```

Open the local URL printed by Streamlit (typically port 8501).

## Example workflow

Upload a sample workbook with **Product**, **Quantity**, and **Unit Price** columns, then try:

1. `List all columns in the workbook.`
2. `Create a Revenue column by multiplying Quantity and Unit Price.`
3. `Format that column as currency.`
4. `Create a bar chart showing Revenue by Product.`
5. `List all columns again.`

Download the resulting workbook to inspect the generated formula column and chart. Supported operations depend on the tool registry and the workbook's actual layout.

## API overview

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Backend health check |
| `POST` | `/api/upload` | Upload a spreadsheet |
| `POST` | `/api/agent/run` | Execute a natural-language instruction |
| `GET` | `/api/files/{file_id}` | Download a stored workbook |

Example agent request (after a successful upload):

```json
{
  "file_id": "<file-id-from-upload>",
  "instruction": "Create a Revenue column by multiplying Quantity and Unit Price"
}
```

## Reliability and safety

**Structured tool interface.** The planner selects from registered operations; generated actions are validated before execution. This limits unsupported arguments and separates LLM decisions from direct workbook mutations.

**Bounded self-correction.** The supplied LangGraph agent defines `MAX_PLAN_RETRIES = 2` and `MAX_EXECUTION_RETRIES = 2`, allowing up to three attempts per retry loop (initial attempt plus two retries). Recovery is best-effort, not a guarantee that every instruction can succeed.

**Transactional workbook changes.** Operations execute on a cloned workbook. The updated workbook is saved only after successful execution, reducing the risk of partial changes.

**Input and deployment boundaries.** This is a local case-study prototype, not a multi-tenant production service. Authentication, per-user authorization, upload limits, file scanning, retention policies, and secure cloud storage would be necessary for production.

## Observability

The agent records structured execution metrics such as:

- `success`, `duration_ms`
- `planner_attempts`, `validation_failures`
- `execution_attempts`, `execution_failures`
- `tool_successes`, `tool_failures`
- `stage_ms` (planner, validator, executor)

**Observed example (one local run):**

| Metric | Value |
| --- | ---: |
| Agent execution time | 1,486.75 ms |
| Planner | 1,468.82 ms |
| Validator | 0.40 ms |
| Executor | 8.68 ms |
| Planning attempts | 1 |
| Execution failures | 0 |

In that run, planning represented approximately **98.8% of measured agent execution time**. The trace measures the instrumented agent execution, **not necessarily total API latency**, because workbook saving and a separate natural-language explanation call can occur afterward. Logs are currently the monitoring surface; a persistent metrics backend and visual dashboard are future enhancements.

## Testing

Run from the repository root:

```bash
python -m pytest backend/tests -q
```

**Reported result:** 110 tests passed in the developer's local environment. The suite covers agent behavior and validation, API behavior, workbook persistence/transactions, recovery, and observability. The exact breakdown and live-LLM coverage should be checked against the final repository and test report; passing tests alone do not establish LLM accuracy or production readiness.

For a final submission, capture the test command and its output (or a CI run) so reviewers can reproduce the result.

## Design trade-offs and limitations

| Decision | Benefit | Limitation / next step |
| --- | --- | --- |
| Gemini planning + deterministic tools | Flexible language interface with constrained actions | LLM plans still require validation and evaluation |
| LangGraph retries | Recovery from some invalid plans and tool errors | Bounded retries cannot solve every failure |
| Local file storage | Simple, reproducible prototype | Move to durable, access-controlled object storage |
| In-process conversation history | Easy follow-up interactions | Use persistent, session-isolated storage in production |
| openpyxl workbook edits | Fine-grained Excel control | Formula calculation/cached results may require Excel or another calculation engine |
| Structured logs | Diagnose failures and latency | Add durable tracing, dashboards, alerts, and cost monitoring |
| Streamlit UI | Fast iteration and demonstration | Add accessibility, user management, and richer UI tests |

## Future improvements

1. **End-to-end evaluation dataset:** Representative spreadsheet tasks scored for correctness, tool selection, and recovery behavior.
2. **Durable state and secure tenancy:** Database-backed conversations and authenticated, isolated workbook storage.
3. **Production monitoring:** Persist traces; measure full request latency, model token usage, cost, and failure rates.
4. **Deployment hardening:** Containerization, CI/CD, rate limiting, secrets management, and upload security.
5. **Spreadsheet validation:** More complex workbooks, formula recalculation, and compatibility checks.

## Assignment attribution

Developed as an **independent JYSK Senior AI Engineer take-home case study**. “JYSK” denotes the case-study context; SheetPilot AI is **not represented as an official JYSK product**.
