import pytest

from backend.app.tools.file_tools import create_workbook

from backend.app.agents.excel_agent import (
    execute_node,
    build_excel_agent,
)

from backend.app.agents.tool_registry import (
    get_tool,
    get_available_tools,
)


@pytest.fixture
def workbook():
    wb = create_workbook("Sales")

    sheet = wb["Sales"]

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

    sheet.append([
        "Mouse",
        20,
        25,
    ])

    return wb


def make_state(workbook, actions):
    return {
        "user_request": "Test request",
        "workbook": workbook,
        "plan": {
            "reasoning": "Test plan",
            "actions": actions,
        },
        "results": [],
        "errors": [],
    }


def test_tool_registry():
    tools = get_available_tools()

    assert "get_summary_statistics" in tools
    assert "write_formula" in tools
    assert "create_bar_chart" in tools


def test_get_registered_tool():
    tool = get_tool("list_sheets")

    assert callable(tool)


def test_unknown_tool():
    with pytest.raises(ValueError):
        get_tool("execute_python")


def test_execute_read_tool(workbook):
    state = make_state(
        workbook,
        [
            {
                "tool": "list_sheets",
                "arguments": {},
            }
        ],
    )

    result = execute_node(state)

    assert result["errors"] == []
    assert len(result["results"]) == 1


def test_execute_formula_tool(workbook):
    state = make_state(
        workbook,
        [
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
    )

    result = execute_node(state)

    assert result["errors"] == []

    assert result["workbook"]["Sales"]["D2"].value == "=B2*C2"
    assert workbook["Sales"]["D2"].value is None


def test_execute_multiple_tools(workbook):
    state = make_state(
        workbook,
        [
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
                    "sheet_name": "Sales",
                    "cell_range": "A1:D1",
                    "bold": True,
                    "fill_color": "1F4E78",
                },
            },
        ],
    )

    result = execute_node(state)

    assert result["errors"] == []
    assert len(result["results"]) == 2
    modified_workbook = result["workbook"]
    assert modified_workbook["Sales"]["D2"].value == "=B2*C2"
    assert modified_workbook["Sales"]["A1"].font.bold is True
    assert workbook["Sales"]["D2"].value is None
    assert workbook["Sales"]["A1"].font.bold is not True


def test_reject_unknown_tool(workbook):
    state = make_state(
        workbook,
        [
            {
                "tool": "execute_python",
                "arguments": {
                    "code": "print('hello')",
                },
            }
        ],
    )

    result = execute_node(state)

    assert len(result["errors"]) == 1
    assert result["results"] == []


def test_reject_workbook_override(workbook):
    state = make_state(
        workbook,
        [
            {
                "tool": "list_sheets",
                "arguments": {
                    "workbook": "malicious_override",
                },
            }
        ],
    )

    result = execute_node(state)

    assert len(result["errors"]) == 1


def test_stop_on_tool_error(workbook):
    state = make_state(
        workbook,
        [
            {
                "tool": "write_formula",
                "arguments": {
                    "sheet_name": "Unknown",
                    "cell": "D2",
                    "formula": "=B2*C2",
                },
            },
            {
                "tool": "create_sheet",
                "arguments": {
                    "sheet_name": "ShouldNotExist",
                },
            },
        ],
    )

    result = execute_node(state)

    assert len(result["errors"]) == 1
    assert "ShouldNotExist" not in workbook.sheetnames


def test_graph_compiles():
    graph = build_excel_agent()

    assert graph is not None