import pytest

from backend.app.tools.file_tools import create_workbook
from backend.app.tools.read_tools import (
    inspect_columns,
    list_sheets,
    preview_sheet,
    read_cell_range,
)


@pytest.fixture
def sample_workbook():
    workbook = create_workbook("Sales")

    sheet = workbook["Sales"]

    sheet.append(["Product", "Quantity", "Price"])
    sheet.append(["Laptop", 5, 800])
    sheet.append(["Mouse", 20, 25])
    sheet.append(["Keyboard", 10, 60])

    return workbook


def test_list_sheets(sample_workbook):
    result = list_sheets(sample_workbook)

    assert result["sheet_count"] == 1
    assert result["sheets"][0]["name"] == "Sales"


def test_preview_sheet(sample_workbook):
    result = preview_sheet(
        sample_workbook,
        "Sales",
        limit=2,
    )

    assert result["columns"] == [
        "Product",
        "Quantity",
        "Price",
    ]

    assert result["returned_rows"] == 2
    assert result["rows"][0] == ["Laptop", 5, 800]
    assert result["rows"][1] == ["Mouse", 20, 25]


def test_inspect_columns(sample_workbook):
    result = inspect_columns(
        sample_workbook,
        "Sales",
    )

    assert result["total_rows"] == 3
    assert result["total_columns"] == 3

    assert result["columns"][0]["type"] == "text"
    assert result["columns"][1]["type"] == "numeric"
    assert result["columns"][2]["type"] == "numeric"


def test_read_cell_range(sample_workbook):
    result = read_cell_range(
        sample_workbook,
        "Sales",
        "A1:C2",
    )

    assert result["values"] == [
        ["Product", "Quantity", "Price"],
        ["Laptop", 5, 800],
    ]


def test_invalid_sheet(sample_workbook):
    with pytest.raises(ValueError):
        preview_sheet(
            sample_workbook,
            "MissingSheet",
        )


def test_invalid_preview_limit(sample_workbook):
    with pytest.raises(ValueError):
        preview_sheet(
            sample_workbook,
            "Sales",
            limit=200,
        )


def test_invalid_cell_range(sample_workbook):
    with pytest.raises(ValueError):
        read_cell_range(
            sample_workbook,
            "Sales",
            "INVALID",
        )


def test_oversized_cell_range(sample_workbook):
    with pytest.raises(ValueError):
        read_cell_range(
            sample_workbook,
            "Sales",
            "A1:Z100",
        )


def test_missing_values():
    workbook = create_workbook("Sales")
    sheet = workbook["Sales"]

    sheet.append(["Product", "Revenue"])
    sheet.append(["Laptop", 1000])
    sheet.append(["Mouse", None])
    sheet.append(["Keyboard", 500])

    result = inspect_columns(workbook, "Sales")

    revenue_column = result["columns"][1]

    assert revenue_column["type"] == "numeric"
    assert revenue_column["missing_count"] == 1
    assert revenue_column["non_null_count"] == 2