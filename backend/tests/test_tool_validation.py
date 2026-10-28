import pytest

from backend.app.agents.tool_registry import TOOL_REGISTRY
from backend.app.agents.tool_validation import validate_tool_call


def validate(name, arguments):
    return validate_tool_call(
        tool_name=name,
        arguments=arguments,
        tool_registry=TOOL_REGISTRY,
    )


def test_valid_column_width():
    result = validate(
        "set_column_width",
        {
            "sheet_name": "Sales",
            "column": "A",
            "width": 25,
        },
    )

    assert result["width"] == 25


def test_reject_excessive_column_width():
    with pytest.raises(ValueError):
        validate(
            "set_column_width",
            {
                "sheet_name": "Sales",
                "column": "A",
                "width": 999999,
            },
        )


def test_reject_negative_column_width():
    with pytest.raises(ValueError):
        validate(
            "set_column_width",
            {
                "sheet_name": "Sales",
                "column": "A",
                "width": -5,
            },
        )


def test_reject_unknown_tool():
    with pytest.raises(ValueError):
        validate("execute_python", {"code": "print(1)"})


def test_reject_workbook_override():
    with pytest.raises(ValueError):
        validate(
            "list_sheets",
            {"workbook": "override"},
        )


def test_reject_unknown_argument():
    with pytest.raises(ValueError):
        validate(
            "list_sheets",
            {"unexpected": True},
        )


def test_reject_missing_required_argument():
    with pytest.raises(ValueError):
        validate(
            "set_column_width",
            {"sheet_name": "Sales"},
        )


def test_valid_formula_column():
    result = validate(
        "apply_formula_to_column",
        {
            "sheet_name": "Sales",
            "target_column": "D",
            "formula_template": "=B{row}*C{row}",
            "header": "Revenue",
        },
    )

    assert result["target_column"] == "D"


def test_reject_invalid_formula_column():
    with pytest.raises(ValueError):
        validate(
            "apply_formula_to_column",
            {
                "sheet_name": "Sales",
                "target_column": "123",
                "formula_template": "=B{row}*C{row}",
            },
        )


def test_reject_invalid_cell():
    with pytest.raises(ValueError):
        validate(
            "write_formula",
            {
                "sheet_name": "Sales",
                "cell": "INVALID",
                "formula": "=A1+B1",
            },
        )