from io import BytesIO

from fastapi.testclient import TestClient
from openpyxl import Workbook, load_workbook

from backend.app.main import app
from backend.app.agents.agent_schemas import AgentResult


client = TestClient(app)


def create_excel_bytes():
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Sales"

    sheet.append(["Product", "Quantity", "Price"])
    sheet.append(["Laptop", 5, 800])

    buffer = BytesIO()
    workbook.save(buffer)

    return buffer.getvalue()
def test_agent_success(tmp_path, monkeypatch):
    from backend.app.services import file_storage
    from backend.app import main

    monkeypatch.setattr(
        file_storage,
        "STORAGE_DIR",
        tmp_path,
    )

    upload_response = client.post(
        "/api/upload",
        files={
            "file": (
                "sales.xlsx",
                create_excel_bytes(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert upload_response.status_code == 200

    file_id = upload_response.json()["file_id"]

    # FIX: conversation_history belongs in the function signature.
    def fake_agent(
        workbook,
        user_request,
        conversation_history=None,
    ):
        assert isinstance(conversation_history, list)
        assert user_request == "Calculate revenue"

        workbook["Sales"]["D1"] = "Revenue"
        workbook["Sales"]["D2"] = "=B2*C2"

        return AgentResult(
            success=True,
            message="Executed successfully",
            workbook=workbook,
            actions_executed=[
                {
                    "tool": "write_formula",
                    "arguments": {},
                    "result": None,
                }
            ],
            errors=[],
        )

    monkeypatch.setattr(
        main,
        "run_excel_agent",
        fake_agent,
    )

    monkeypatch.setattr(
        main,
        "generate_agent_response",
        lambda user_request, actions_executed: (
            "The Revenue column was created successfully. "
            "Revenue is calculated by multiplying "
            "Quantity and Price."
        ),
    )

    response = client.post(
        "/api/agent/run",
        json={
            "file_id": file_id,
            "instruction": "Calculate revenue",
        },
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["success"] is True
    assert data["download_url"] is not None
    assert "Revenue" in data["message"]

    download_response = client.get(
        data["download_url"]
    )

    assert download_response.status_code == 200
    assert len(download_response.content) > 0

    # Verify that the downloaded workbook contains the changes.
    downloaded_workbook = Workbook
    from openpyxl import load_workbook

    downloaded_workbook = load_workbook(
        BytesIO(download_response.content)
    )

    assert downloaded_workbook["Sales"]["D1"].value == "Revenue"
    assert downloaded_workbook["Sales"]["D2"].value == "=B2*C2"