"""Tests for SheetPilot AI Phase 7.1 planning retries (no Gemini API calls)."""

import json
from types import SimpleNamespace

from openpyxl import Workbook

from backend.app.agents import excel_agent


def make_workbook():
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Sales"
    sheet.append(["Product", "Quantity", "Unit Price", "Revenue"])
    sheet.append(["Laptop", 5, 800, 4000])
    return workbook


def width_plan(width):
    return {
        "reasoning": "Set Revenue column width.",
        "actions": [
            {
                "tool": "set_column_width",
                "arguments": {
                    "sheet_name": "Sales",
                    "column": "D",
                    "width": width,
                },
            }
        ],
    }


def mock_gemini(monkeypatch, plans):
    """Return sequential Gemini JSON responses and record prompts/close calls."""
    calls = {"count": 0, "prompts": [], "closed": 0}

    class FakeModels:
        def generate_content(self, *, model, contents, config):
            calls["prompts"].append(contents)
            index = calls["count"]
            calls["count"] += 1
            if index >= len(plans):
                raise AssertionError("Gemini called more times than expected")
            return SimpleNamespace(text=json.dumps(plans[index]))

    class FakeClient:
        def __init__(self):
            self.models = FakeModels()

        def close(self):
            calls["closed"] += 1

    monkeypatch.setattr(excel_agent, "get_gemini_client", FakeClient)
    monkeypatch.setattr(excel_agent, "get_gemini_model", lambda: "fake-model")
    return calls


def test_valid_plan_executes_without_retry(monkeypatch):
    calls = mock_gemini(monkeypatch, [width_plan(20)])
    original = make_workbook()

    result = excel_agent.run_excel_agent(original, "Set Revenue width to 20")

    assert result.success is True
    assert result.errors == []
    assert calls["count"] == 1
    assert calls["closed"] == 1
    assert result.workbook["Sales"].column_dimensions["D"].width == 20
    assert original["Sales"].column_dimensions["D"].width != 20


def test_invalid_plan_is_corrected_on_retry(monkeypatch):
    calls = mock_gemini(monkeypatch, [width_plan(-20), width_plan(20)])
    original = make_workbook()

    result = excel_agent.run_excel_agent(original, "Set Revenue width to 20")

    assert result.success is True
    assert result.errors == []
    assert calls["count"] == 2
    assert calls["closed"] == 2
    assert "VALIDATION FEEDBACK" in calls["prompts"][1]
    assert result.workbook["Sales"].column_dimensions["D"].width == 20
    assert original["Sales"].column_dimensions["D"].width != 20


def test_repeated_invalid_plans_stop_safely(monkeypatch):
    attempts = excel_agent.MAX_PLAN_RETRIES + 1
    calls = mock_gemini(monkeypatch, [width_plan(-20)] * attempts)
    original = make_workbook()

    result = excel_agent.run_excel_agent(original, "Set Revenue width to 20")

    assert result.success is False
    assert result.errors
    assert str(attempts) in " ".join(result.errors)
    assert result.actions_executed == []
    assert calls["count"] == attempts
    assert calls["closed"] == attempts
    assert result.workbook is None
    assert original["Sales"].column_dimensions["D"].width != 20
