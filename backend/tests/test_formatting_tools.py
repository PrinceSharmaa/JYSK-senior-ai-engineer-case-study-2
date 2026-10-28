import pytest

from backend.app.tools.file_tools import create_workbook
from backend.app.tools.formatting_tools import (
    add_conditional_formatting,
    apply_color_scale,
    apply_number_format,
    apply_table_style,
    format_cells,
    freeze_panes,
    set_column_width,
)


@pytest.fixture
def sales_workbook():
    workbook = create_workbook("Sales")
    sheet = workbook["Sales"]

    sheet.append(["Product", "Quantity", "Price", "Revenue"])
    sheet.append(["Laptop", 5, 800, 4000])
    sheet.append(["Mouse", 20, 25, 500])
    sheet.append(["Keyboard", 10, 60, 600])

    return workbook


def test_format_header(sales_workbook):
    result = format_cells(
        sales_workbook,
        "Sales",
        "A1:D1",
        bold=True,
        font_color="FFFFFF",
        fill_color="1F4E78",
        horizontal_alignment="center",
    )

    sheet = sales_workbook["Sales"]

    assert result["formatted_cells"] == 4
    assert sheet["A1"].font.bold is True
    assert sheet["A1"].fill.fgColor.rgb.endswith("1F4E78")
    assert sheet["A1"].alignment.horizontal == "center"


def test_format_preserves_existing_style(sales_workbook):
    sheet = sales_workbook["Sales"]

    format_cells(
        sales_workbook,
        "Sales",
        "A1",
        bold=True,
    )

    format_cells(
        sales_workbook,
        "Sales",
        "A1",
        fill_color="FFFF00",
    )

    assert sheet["A1"].font.bold is True
    assert sheet["A1"].fill.fgColor.rgb.endswith("FFFF00")


def test_invalid_color(sales_workbook):
    with pytest.raises(ValueError):
        format_cells(
            sales_workbook,
            "Sales",
            "A1",
            fill_color="NOT_A_COLOR",
        )


def test_invalid_range(sales_workbook):
    with pytest.raises(ValueError):
        format_cells(
            sales_workbook,
            "Sales",
            "INVALID",
            bold=True,
        )


def test_oversized_range(sales_workbook):
    with pytest.raises(ValueError):
        format_cells(
            sales_workbook,
            "Sales",
            "A1:Z1000",
            bold=True,
        )


def test_currency_format(sales_workbook):
    result = apply_number_format(
        sales_workbook,
        "Sales",
        "D2:D4",
        "currency",
    )

    assert result["status"] == "success"
    assert "$" in sales_workbook["Sales"]["D2"].number_format


def test_invalid_number_format(sales_workbook):
    with pytest.raises(ValueError):
        apply_number_format(
            sales_workbook,
            "Sales",
            "D2:D4",
            "unknown",
        )


def test_column_width(sales_workbook):
    set_column_width(
        sales_workbook,
        "Sales",
        "A",
        25,
    )

    assert sales_workbook["Sales"].column_dimensions["A"].width == 25


def test_invalid_column_width(sales_workbook):
    with pytest.raises(ValueError):
        set_column_width(
            sales_workbook,
            "Sales",
            "A",
            500,
        )


def test_conditional_formatting(sales_workbook):
    result = add_conditional_formatting(
        sales_workbook,
        "Sales",
        "D2:D4",
        condition="lessThan",
        threshold=1000,
        fill_color="FFC7CE",
    )

    assert result["status"] == "success"
    assert len(
        sales_workbook["Sales"].conditional_formatting
    ) == 1


def test_invalid_conditional_operator(sales_workbook):
    with pytest.raises(ValueError):
        add_conditional_formatting(
            sales_workbook,
            "Sales",
            "D2:D4",
            condition="execute_code",
            threshold=1000,
        )


def test_color_scale(sales_workbook):
    result = apply_color_scale(
        sales_workbook,
        "Sales",
        "D2:D4",
    )

    assert result["status"] == "success"
    assert len(
        sales_workbook["Sales"].conditional_formatting
    ) == 1


def test_freeze_panes(sales_workbook):
    freeze_panes(
        sales_workbook,
        "Sales",
        "A2",
    )

    assert sales_workbook["Sales"].freeze_panes == "A2"


def test_table_style(sales_workbook):
    result = apply_table_style(
        sales_workbook,
        "Sales",
        "A1:D4",
        table_name="SalesData",
    )

    assert result["status"] == "success"
    assert "SalesData" in sales_workbook["Sales"].tables


def test_duplicate_table(sales_workbook):
    apply_table_style(
        sales_workbook,
        "Sales",
        "A1:D4",
        table_name="SalesData",
    )

    with pytest.raises(ValueError):
        apply_table_style(
            sales_workbook,
            "Sales",
            "A1:D4",
            table_name="SalesData",
        )


def test_invalid_table_headers(sales_workbook):
    sheet = sales_workbook["Sales"]
    sheet["B1"] = None

    with pytest.raises(ValueError):
        apply_table_style(
            sales_workbook,
            "Sales",
            "A1:D4",
            table_name="InvalidTable",
        )