import pytest

from backend.app.tools.file_tools import create_workbook
from backend.app.tools.formula_tools import (
    apply_formula_to_column,
    create_sheet,
    preview_arithmetic_formula,
    set_recalculation,
    write_cell_values,
    write_formula,
)


@pytest.fixture
def sales_workbook():
    workbook = create_workbook("Sales")
    sheet = workbook["Sales"]

    sheet.append(["Product", "Quantity", "Price"])
    sheet.append(["Laptop", 5, 800])
    sheet.append(["Mouse", 20, 25])
    sheet.append(["Keyboard", 10, 60])

    return workbook


def test_write_formula(sales_workbook):
    result = write_formula(
        sales_workbook,
        "Sales",
        "D2",
        "=B2*C2",
    )

    assert result["status"] == "success"
    assert sales_workbook["Sales"]["D2"].value == "=B2*C2"


def test_formula_requires_equals(sales_workbook):
    with pytest.raises(ValueError):
        write_formula(
            sales_workbook,
            "Sales",
            "D2",
            "B2*C2",
        )


def test_write_cell_values(sales_workbook):
    result = write_cell_values(
        sales_workbook,
        "Sales",
        {
            "C2": 900,
            "C3": 30,
        },
    )

    assert result["updated_cells"] == 2
    assert sales_workbook["Sales"]["C2"].value == 900
    assert sales_workbook["Sales"]["C3"].value == 30


def test_create_sheet(sales_workbook):
    result = create_sheet(
        sales_workbook,
        "Summary",
    )

    assert result["status"] == "created"
    assert "Summary" in sales_workbook.sheetnames


def test_duplicate_sheet(sales_workbook):
    with pytest.raises(ValueError):
        create_sheet(
            sales_workbook,
            "Sales",
        )


def test_apply_formula_to_column(sales_workbook):
    result = apply_formula_to_column(
        sales_workbook,
        "Sales",
        target_column="D",
        formula_template="=B{row}*C{row}",
        header="Revenue",
    )

    sheet = sales_workbook["Sales"]

    assert result["formulas_created"] == 3
    assert sheet["D1"].value == "Revenue"
    assert sheet["D2"].value == "=B2*C2"
    assert sheet["D3"].value == "=B3*C3"
    assert sheet["D4"].value == "=B4*C4"


def test_invalid_formula_template(sales_workbook):
    with pytest.raises(ValueError):
        apply_formula_to_column(
            sales_workbook,
            "Sales",
            target_column="D",
            formula_template="=B2*C2",
        )


def test_invalid_target_column(sales_workbook):
    with pytest.raises(ValueError):
        apply_formula_to_column(
            sales_workbook,
            "Sales",
            target_column="INVALID",
            formula_template="=B{row}*C{row}",
        )


def test_preview_arithmetic_formula(sales_workbook):
    result = preview_arithmetic_formula(
        sales_workbook,
        "Sales",
        "=B2*C2",
    )

    assert result["preview_result"] == 4000


def test_preview_parentheses(sales_workbook):
    result = preview_arithmetic_formula(
        sales_workbook,
        "Sales",
        "=(B2+C2)/2",
    )

    assert result["preview_result"] == 402.5


def test_preview_rejects_excel_functions(sales_workbook):
    with pytest.raises(ValueError):
        preview_arithmetic_formula(
            sales_workbook,
            "Sales",
            "=SUM(B2:B4)",
        )


def test_preview_rejects_text_cells(sales_workbook):
    with pytest.raises(ValueError):
        preview_arithmetic_formula(
            sales_workbook,
            "Sales",
            "=A2*C2",
        )


def test_recalculation_enabled(sales_workbook):
    set_recalculation(sales_workbook)

    assert sales_workbook.calculation.calcMode == "auto"
    assert sales_workbook.calculation.fullCalcOnLoad is True
    assert sales_workbook.calculation.forceFullCalc is True