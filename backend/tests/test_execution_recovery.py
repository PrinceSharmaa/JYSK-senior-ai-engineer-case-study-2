"""Phase 7.2: recover from tool runtime failures without committing partial edits."""

import json
from types import SimpleNamespace

from openpyxl import Workbook

from backend.app.agents import excel_agent


def workbook_fixture():
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Sales"
    sheet.append(["Product", "Quantity", "Unit Price"])
    sheet.append(["Laptop", 5, 800])
    return workbook


def plan(*actions):
    return {"reasoning": "Execute requested spreadsheet changes.", "actions": list(actions)}


def action(sheet_name, cell, formula):
    return {
        "tool": "write_formula",
        "arguments": {"sheet_name": sheet_name, "cell": cell, "formula": formula},
    }


def mock_gemini(monkeypatch, responses):
    observed = {"prompts": [], "closed": 0}

    class FakeModels:
        def generate_content(self, *, model, contents, config):
            observed["prompts"].append(contents)
            index = len(observed["prompts"]) - 1
            if index >= len(responses):
                raise AssertionError("Unexpected extra Gemini request")
            return SimpleNamespace(text=json.dumps(responses[index]))

    class FakeClient:
        def __init__(self):
            self.models = FakeModels()

        def close(self):
            observed["closed"] += 1

    monkeypatch.setattr(excel_agent, "get_gemini_client", FakeClient)
    monkeypatch.setattr(excel_agent, "get_gemini_model", lambda: "test-model")
    return observed


def test_execution_success_does_not_retry(monkeypatch):
    observed = mock_gemini(monkeypatch, [plan(action("Sales", "D2", "=B2*C2"))])
    original = workbook_fixture()
    result = excel_agent.run_excel_agent(original, "Calculate revenue")
    assert result.success
    assert len(observed["prompts"]) == 1
    assert result.workbook["Sales"]["D2"].value == "=B2*C2"
    assert original["Sales"]["D2"].value is None


def test_runtime_failure_recovers_and_rolls_back_first_attempt(monkeypatch):
    observed = mock_gemini(
        monkeypatch,
        [
            plan(
                action("Sales", "E2", "=1+1"),
                action("MissingSheet", "D2", "=B2*C2"),
            ),
            plan(action("Sales", "D2", "=B2*C2")),
        ],
    )
    original = workbook_fixture()
    result = excel_agent.run_excel_agent(original, "Calculate revenue")
    assert result.success
    assert len(observed["prompts"]) == 2
    assert "EXECUTION FEEDBACK" in observed["prompts"][1]
    assert "MissingSheet" in observed["prompts"][1]
    assert result.workbook["Sales"]["D2"].value == "=B2*C2"
    assert result.workbook["Sales"]["E2"].value is None
    assert original["Sales"]["D2"].value is None
    assert original["Sales"]["E2"].value is None
    assert len(result.actions_executed) == 1
    assert observed["closed"] == 2


def test_repeated_execution_failures_stop_safely(monkeypatch):
    attempts = excel_agent.MAX_EXECUTION_RETRIES + 1
    observed = mock_gemini(
        monkeypatch,
        [plan(action("MissingSheet", "D2", "=B2*C2"))] * attempts,
    )
    original = workbook_fixture()
    result = excel_agent.run_excel_agent(original, "Calculate revenue")
    assert not result.success
    assert len(observed["prompts"]) == attempts
    assert str(attempts) in " ".join(result.errors)
    assert result.actions_executed == []
    assert result.workbook is None
    assert original["Sales"]["D2"].value is None
