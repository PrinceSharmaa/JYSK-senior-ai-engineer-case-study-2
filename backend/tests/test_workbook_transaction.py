from backend.app.tools.file_tools import create_workbook

from backend.app.services.workbook_transaction import (
    clone_workbook,
)

from backend.app.agents.excel_agent import execute_node


def create_test_workbook():
    workbook = create_workbook("Sales")

    sheet = workbook["Sales"]

    sheet.append([
        "Product",
        "Quantity",
        "Price",
    ])

    sheet.append([
        "Laptop",
        5,
        800,
    ])

    return workbook


def test_clone_is_independent():
    original = create_test_workbook()

    cloned = clone_workbook(original)

    cloned["Sales"]["A2"] = "Modified"

    assert original["Sales"]["A2"].value == "Laptop"
    assert cloned["Sales"]["A2"].value == "Modified"


def test_success_returns_modified_copy():
    original = create_test_workbook()

    state = {
        "user_request": "Calculate revenue",
        "workbook": original,
        "plan": {
            "reasoning": "Create revenue",
            "actions": [
                {
                    "tool": "apply_formula_to_column",
                    "arguments": {
                        "sheet_name": "Sales",
                        "target_column": "D",
                        "formula_template": "=B{row}*C{row}",
                        "header": "Revenue",
                    },
                }
            ],
        },
        "results": [],
        "errors": [],
    }

    result = execute_node(state)

    assert result["errors"] == []

    assert result["workbook"]["Sales"]["D2"].value == "=B2*C2"

    assert original["Sales"]["D2"].value is None


def test_failure_preserves_original():
    original = create_test_workbook()

    state = {
        "user_request": "Calculate and format revenue",
        "workbook": original,
        "plan": {
            "reasoning": "Test rollback",
            "actions": [
                {
                    "tool": "apply_formula_to_column",
                    "arguments": {
                        "sheet_name": "Sales",
                        "target_column": "D",
                        "formula_template": "=B{row}*C{row}",
                        "header": "Revenue",
                    },
                },
                {
                    "tool": "format_cells",
                    "arguments": {
                        "sheet_name": "MissingSheet",
                        "cell_range": "A1",
                        "bold": True,
                    },
                },
            ],
        },
        "results": [],
        "errors": [],
    }

    result = execute_node(state)

    assert len(result["errors"]) == 1

    assert result["workbook"] is original

    assert original["Sales"]["D2"].value is None