"""Phase 7.3 telemetry tests; no Gemini calls or API keys required."""

import json
import logging

import pytest

from backend.app.services.agent_observability import instrument_node, run_with_trace


class Result:
    success = True


def _events(caplog):
    return [json.loads(r.message) for r in caplog.records if r.name == "sheetpilot.observability"]


def test_trace_reports_stages_and_retries(caplog):
    caplog.set_level(logging.INFO, logger="sheetpilot.observability")
    attempts = {"n": 0}

    def planner(state):
        attempts["n"] += 1
        return {"plan": {"actions": []}}

    def validator(state):
        return {"plan_valid": attempts["n"] > 1}

    def executor(state):
        return {"execution_success": True, "results": [{"tool": "list_sheets"}]}

    def operation():
        p = instrument_node("planner", planner)
        v = instrument_node("validator", validator)
        e = instrument_node("executor", executor)
        p({})
        v({})
        p({})
        v({})
        e({})
        return Result()

    run_with_trace(operation)
    completed = [e for e in _events(caplog) if e["event"] == "agent_completed"]
    assert len(completed) == 1
    assert completed[0]["planner_attempts"] == 2
    assert completed[0]["validation_failures"] == 1
    assert completed[0]["execution_attempts"] == 1
    assert completed[0]["tool_successes"] == {"list_sheets": 1}
    assert completed[0]["duration_ms"] >= 0
    assert completed[0]["request_id"]


def test_execution_failure_is_counted(caplog):
    caplog.set_level(logging.INFO, logger="sheetpilot.observability")

    def operation():
        instrument_node("executor", lambda state: {
            "execution_success": False,
            "errors": ["create_bar_chart: missing data"],
            "results": [],
        })({})
        return Result()

    run_with_trace(operation)
    completed = next(e for e in _events(caplog) if e["event"] == "agent_completed")
    assert completed["execution_failures"] == 1
    assert completed["tool_failures"] == {"create_bar_chart": 1}


def test_exception_is_logged_without_sensitive_input(caplog):
    caplog.set_level(logging.INFO, logger="sheetpilot.observability")
    secret = "PRIVATE_SHEET_CELL_VALUE"

    def operation():
        raise RuntimeError(secret)

    with pytest.raises(RuntimeError):
        run_with_trace(operation)

    records = _events(caplog)
    assert records[-1]["event"] == "agent_exception"
    assert secret not in caplog.text
