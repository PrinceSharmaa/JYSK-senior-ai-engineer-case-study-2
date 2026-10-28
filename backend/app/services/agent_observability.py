"""Structured, privacy-conscious per-request telemetry for SheetPilot AI."""

from __future__ import annotations

import json
import logging
import time
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("sheetpilot.observability")


@dataclass
class AgentTrace:
    request_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    started_at: float = field(default_factory=time.perf_counter)
    planner_attempts: int = 0
    validation_failures: int = 0
    execution_attempts: int = 0
    execution_failures: int = 0
    tool_attempts: dict[str, int] = field(default_factory=dict)
    tool_successes: dict[str, int] = field(default_factory=dict)
    tool_failures: dict[str, int] = field(default_factory=dict)
    stage_ms: dict[str, float] = field(default_factory=dict)


_current_trace: ContextVar[AgentTrace | None] = ContextVar("sheetpilot_trace", default=None)


def emit(event: str, **fields: Any) -> None:
    """Emit one JSON log record without workbook or conversation contents."""
    trace = _current_trace.get()
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "request_id": trace.request_id if trace else None,
        **fields,
    }
    logger.info(json.dumps(payload, default=str, separators=(",", ":")))


def instrument_node(stage: str, node):
    """Wrap a LangGraph node without changing its input/output contract."""
    def wrapped(state):
        trace = _current_trace.get()
        started = time.perf_counter()
        if trace:
            if stage == "planner":
                trace.planner_attempts += 1
            elif stage == "executor":
                trace.execution_attempts += 1
        try:
            output = node(state)
            if trace:
                if stage == "validator" and not output.get("plan_valid", False):
                    trace.validation_failures += 1
                if stage == "executor":
                    if not output.get("execution_success", False):
                        trace.execution_failures += 1
                    for action in output.get("results", []):
                        name = action.get("tool", "unknown")
                        trace.tool_successes[name] = trace.tool_successes.get(name, 0) + 1
                    # On failure the executor intentionally discards rolled-back results.
                    if not output.get("execution_success", True):
                        name = (output.get("errors") or ["unknown"])[0].split(":", 1)[0]
                        trace.tool_failures[name] = trace.tool_failures.get(name, 0) + 1
            emit("agent_stage", stage=stage, status="ok", duration_ms=round((time.perf_counter()-started)*1000, 2))
            return output
        except Exception:
            emit("agent_stage", stage=stage, status="exception", duration_ms=round((time.perf_counter()-started)*1000, 2))
            raise
        finally:
            if trace:
                trace.stage_ms[stage] = round(trace.stage_ms.get(stage, 0) + (time.perf_counter()-started)*1000, 2)
    return wrapped


def run_with_trace(operation, *args, **kwargs):
    """Run one agent invocation with an isolated trace (safe for concurrent requests)."""
    trace = AgentTrace()
    token = _current_trace.set(trace)
    emit("agent_started")
    try:
        result = operation(*args, **kwargs)
        emit(
            "agent_completed",
            success=bool(result.success),
            duration_ms=round((time.perf_counter()-trace.started_at)*1000, 2),
            planner_attempts=trace.planner_attempts,
            validation_failures=trace.validation_failures,
            execution_attempts=trace.execution_attempts,
            execution_failures=trace.execution_failures,
            tool_successes=trace.tool_successes,
            tool_failures=trace.tool_failures,
            stage_ms=trace.stage_ms,
        )
        return result
    except Exception:
        emit(
            "agent_exception",
            duration_ms=round((time.perf_counter()-trace.started_at)*1000, 2),
            planner_attempts=trace.planner_attempts,
            execution_attempts=trace.execution_attempts,
        )
        raise
    finally:
        _current_trace.reset(token)
