from datetime import date, datetime
from typing import Any

from openpyxl.utils.cell import range_boundaries
from openpyxl.workbook.workbook import Workbook


def _serialize_value(value: Any) -> Any:
    """
    Convert Excel values into JSON-compatible values.
    """
    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, (str, int, float, bool)) or value is None:
        return value

    return str(value)


def _get_sheet(workbook: Workbook, sheet_name: str):
    """
    Retrieve a worksheet and validate its name.
    """
    if sheet_name not in workbook.sheetnames:
        raise ValueError(
            f"Worksheet '{sheet_name}' not found. "
            f"Available sheets: {workbook.sheetnames}"
        )

    return workbook[sheet_name]


def list_sheets(workbook: Workbook) -> dict:
    """
    Return information about all worksheets.
    """
    sheets = []

    for sheet in workbook.worksheets:
        sheets.append(
            {
                "name": sheet.title,
                "rows": sheet.max_row,
                "columns": sheet.max_column,
            }
        )

    return {
        "sheet_count": len(sheets),
        "sheets": sheets,
    }


def preview_sheet(
    workbook: Workbook,
    sheet_name: str,
    limit: int = 10,
) -> dict:
    """
    Preview the first N data rows.

    Assumes the first row contains column headers.
    """
    if limit < 1 or limit > 100:
        raise ValueError(
            "Preview limit must be between 1 and 100."
        )

    sheet = _get_sheet(workbook, sheet_name)

    if sheet.max_row < 1:
        return {
            "sheet_name": sheet_name,
            "columns": [],
            "rows": [],
            "returned_rows": 0,
        }

    headers = [
        _serialize_value(sheet.cell(1, col).value)
        for col in range(1, sheet.max_column + 1)
    ]

    records = []

    for row in sheet.iter_rows(
        min_row=2,
        max_row=min(sheet.max_row, limit + 1),
        values_only=True,
    ):
        records.append(
            [_serialize_value(value) for value in row]
        )

    return {
        "sheet_name": sheet_name,
        "columns": headers,
        "rows": records,
        "returned_rows": len(records),
    }


def inspect_columns(
    workbook: Workbook,
    sheet_name: str,
) -> dict:
    """
    Inspect column names, inferred types, and missing values.
    """
    sheet = _get_sheet(workbook, sheet_name)

    columns = []

    for col_idx in range(1, sheet.max_column + 1):
        header = sheet.cell(1, col_idx).value

        values = [
            sheet.cell(row_idx, col_idx).value
            for row_idx in range(2, sheet.max_row + 1)
        ]

        non_null_values = [
            value
            for value in values
            if value is not None and value != ""
        ]

        missing_count = len(values) - len(non_null_values)

        if not non_null_values:
            inferred_type = "empty"

        elif all(
            isinstance(value, bool)
            for value in non_null_values
        ):
            inferred_type = "boolean"

        elif all(
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            for value in non_null_values
        ):
            inferred_type = "numeric"

        elif all(
            isinstance(value, (datetime, date))
            for value in non_null_values
        ):
            inferred_type = "datetime"

        elif all(
            isinstance(value, str)
            for value in non_null_values
        ):
            inferred_type = "text"

        else:
            inferred_type = "mixed"

        columns.append(
            {
                "name": _serialize_value(header),
                "type": inferred_type,
                "non_null_count": len(non_null_values),
                "missing_count": missing_count,
                "sample_values": [
                    _serialize_value(value)
                    for value in non_null_values[:3]
                ],
            }
        )

    return {
        "sheet_name": sheet_name,
        "total_rows": max(sheet.max_row - 1, 0),
        "total_columns": len(columns),
        "columns": columns,
    }


def read_cell_range(
    workbook: Workbook,
    sheet_name: str,
    cell_range: str,
) -> dict:
    """
    Read values from an Excel range such as A1:C5.
    """
    sheet = _get_sheet(workbook, sheet_name)

    try:
        min_col, min_row, max_col, max_row = range_boundaries(
            cell_range
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Invalid cell range: {cell_range}"
        ) from exc

    if (
        min_col is None
        or min_row is None
        or max_col is None
        or max_row is None
    ):
        raise ValueError(
            "A bounded range such as A1:C5 is required."
        )

    if (
        min_col > max_col
        or min_row > max_row
        or (max_col - min_col + 1)
        * (max_row - min_row + 1) > 1000
    ):
        raise ValueError(
            "Invalid or oversized range. "
            "Maximum 1,000 cells per request."
        )

    values = []

    for row in sheet.iter_rows(
        min_row=min_row,
        max_row=max_row,
        min_col=min_col,
        max_col=max_col,
        values_only=True,
    ):
        values.append(
            [_serialize_value(value) for value in row]
        )

    return {
        "sheet_name": sheet_name,
        "range": cell_range,
        "values": values,
    }