import re

from openpyxl import Workbook
from copy import copy
from openpyxl.formatting.rule import CellIsRule, ColorScaleRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils.cell import (
    column_index_from_string,
    get_column_letter,
    range_boundaries,
)
from openpyxl.worksheet.table import Table, TableStyleInfo


MAX_FORMAT_CELLS = 10_000

ALLOWED_NUMBER_FORMATS = {
    "integer": "#,##0",
    "decimal": "#,##0.00",
    "percentage": "0.00%",
    "currency": '"$"#,##0.00',
    "date": "yyyy-mm-dd",
    "datetime": "yyyy-mm-dd hh:mm",
}

ALLOWED_CONDITIONS = {
    "greaterThan",
    "lessThan",
    "equal",
    "notEqual",
    "greaterThanOrEqual",
    "lessThanOrEqual",
    "between",
    "notBetween",
}

ALLOWED_TABLE_STYLES = {
    "TableStyleMedium2",
    "TableStyleMedium4",
    "TableStyleMedium9",
    "TableStyleLight1",
    "TableStyleLight9",
    "TableStyleDark1",
}


def _get_sheet(workbook: Workbook, sheet_name: str):
    if sheet_name not in workbook.sheetnames:
        raise ValueError(
            f"Worksheet '{sheet_name}' not found."
        )

    return workbook[sheet_name]


def _validate_range(cell_range: str):
    """
    Validate a bounded Excel range and limit its size.
    """
    try:
        min_col, min_row, max_col, max_row = range_boundaries(
            cell_range
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Invalid Excel range: {cell_range}"
        ) from exc

    if any(
        value is None
        for value in (min_col, min_row, max_col, max_row)
    ):
        raise ValueError(
            "Use a bounded range such as A1:D10."
        )

    if min_col > max_col or min_row > max_row:
        raise ValueError("Invalid range boundaries.")

    if max_col > 16384 or max_row > 1048576:
        raise ValueError("Range exceeds Excel limits.")

    total_cells = (
        (max_col - min_col + 1)
        * (max_row - min_row + 1)
    )

    if total_cells > MAX_FORMAT_CELLS:
        raise ValueError(
            f"Maximum {MAX_FORMAT_CELLS} cells per operation."
        )

    return min_col, min_row, max_col, max_row


def _validate_color(color: str) -> str:
    """
    Accept six-character RGB hex colors, e.g. 1F4E78.
    """
    if not isinstance(color, str):
        raise ValueError("Color must be a hex string.")

    color = color.lstrip("#").upper()

    if not re.fullmatch(r"[0-9A-F]{6}", color):
        raise ValueError(
            "Color must be a six-character RGB hex value."
        )

    return color


def format_cells(
    workbook: Workbook,
    sheet_name: str,
    cell_range: str,
    bold: bool | None = None,
    italic: bool | None = None,
    font_color: str | None = None,
    fill_color: str | None = None,
    font_size: int | None = None,
    horizontal_alignment: str | None = None,
    wrap_text: bool | None = None,
    border: bool = False,
) -> dict:
    """
    Apply formatting while preserving unrelated existing styles.
    """
    sheet = _get_sheet(workbook, sheet_name)

    min_col, min_row, max_col, max_row = _validate_range(
        cell_range
    )

    if font_color is not None:
        font_color = _validate_color(font_color)

    if fill_color is not None:
        fill_color = _validate_color(fill_color)

    if font_size is not None and not 6 <= font_size <= 72:
        raise ValueError("Font size must be between 6 and 72.")

    if horizontal_alignment not in {
        None, "left", "center", "right"
    }:
        raise ValueError(
            "Alignment must be left, center, or right."
        )

    thin_side = Side(
        style="thin",
        color="D9E2F3",
    )

    for row in sheet.iter_rows(
        min_row=min_row,
        max_row=max_row,
        min_col=min_col,
        max_col=max_col,
    ):
        for cell in row:
            font = copy(cell.font)

            if bold is not None:
                font.bold = bold

            if italic is not None:
                font.italic = italic

            if font_color is not None:
                font.color = font_color

            if font_size is not None:
                font.sz = font_size

            cell.font = font

            if fill_color is not None:
                cell.fill = PatternFill(
                    fill_type="solid",
                    fgColor=fill_color,
                )

            alignment = copy(cell.alignment)

            if horizontal_alignment is not None:
                alignment.horizontal = horizontal_alignment

            if wrap_text is not None:
                alignment.wrap_text = wrap_text

            cell.alignment = alignment

            if border:
                cell.border = Border(
                    left=thin_side,
                    right=thin_side,
                    top=thin_side,
                    bottom=thin_side,
                )

    return {
        "sheet_name": sheet_name,
        "range": cell_range,
        "formatted_cells": (
            (max_col - min_col + 1)
            * (max_row - min_row + 1)
        ),
        "status": "success",
    }


def apply_number_format(
    workbook: Workbook,
    sheet_name: str,
    cell_range: str,
    format_type: str,
) -> dict:
    """
    Apply a predefined Excel number format.
    """
    sheet = _get_sheet(workbook, sheet_name)

    min_col, min_row, max_col, max_row = _validate_range(
        cell_range
    )

    if format_type not in ALLOWED_NUMBER_FORMATS:
        raise ValueError(
            f"Unsupported format: {format_type}. "
            f"Available: {list(ALLOWED_NUMBER_FORMATS)}"
        )

    number_format = ALLOWED_NUMBER_FORMATS[format_type]

    for row in sheet.iter_rows(
        min_row=min_row,
        max_row=max_row,
        min_col=min_col,
        max_col=max_col,
    ):
        for cell in row:
            cell.number_format = number_format

    return {
        "sheet_name": sheet_name,
        "range": cell_range,
        "format_type": format_type,
        "status": "success",
    }


def set_column_width(
    workbook: Workbook,
    sheet_name: str,
    column: str,
    width: float,
) -> dict:
    """
    Set the display width of a worksheet column.
    """
    sheet = _get_sheet(workbook, sheet_name)

    try:
        column_index = column_index_from_string(
            column.upper()
        )
    except (AttributeError, ValueError) as exc:
        raise ValueError("Invalid column letter.") from exc

    if column_index > 16384:
        raise ValueError("Column exceeds Excel limits.")

    if not 1 <= width <= 100:
        raise ValueError(
            "Column width must be between 1 and 100."
        )

    column = get_column_letter(column_index)

    sheet.column_dimensions[column].width = width

    return {
        "sheet_name": sheet_name,
        "column": column,
        "width": width,
        "status": "success",
    }


def add_conditional_formatting(
    workbook: Workbook,
    sheet_name: str,
    cell_range: str,
    condition: str,
    threshold: float,
    fill_color: str = "FFC7CE",
) -> dict:
    """
    Highlight cells based on a numeric comparison.

    Example:
        Highlight Revenue < 1000 in red.
    """
    sheet = _get_sheet(workbook, sheet_name)

    _validate_range(cell_range)

    if condition not in {
        "greaterThan",
        "lessThan",
        "equal",
        "notEqual",
        "greaterThanOrEqual",
        "lessThanOrEqual",
    }:
        raise ValueError(
            "Unsupported conditional formatting condition."
        )

    if not isinstance(threshold, (int, float)) or isinstance(
        threshold, bool
    ):
        raise ValueError("Threshold must be numeric.")

    fill_color = _validate_color(fill_color)

    rule = CellIsRule(
        operator=condition,
        formula=[str(threshold)],
        fill=PatternFill(
            fill_type="solid",
            fgColor=fill_color,
        ),
    )

    sheet.conditional_formatting.add(
        cell_range,
        rule,
    )

    return {
        "sheet_name": sheet_name,
        "range": cell_range,
        "condition": condition,
        "threshold": threshold,
        "status": "success",
    }


def apply_color_scale(
    workbook: Workbook,
    sheet_name: str,
    cell_range: str,
) -> dict:
    """
    Add a red-yellow-green conditional formatting color scale.
    """
    sheet = _get_sheet(workbook, sheet_name)

    _validate_range(cell_range)

    rule = ColorScaleRule(
        start_type="min",
        start_color="F8696B",
        mid_type="percentile",
        mid_value=50,
        mid_color="FFEB84",
        end_type="max",
        end_color="63BE7B",
    )

    sheet.conditional_formatting.add(
        cell_range,
        rule,
    )

    return {
        "sheet_name": sheet_name,
        "range": cell_range,
        "status": "success",
    }


def freeze_panes(
    workbook: Workbook,
    sheet_name: str,
    cell: str = "A2",
) -> dict:
    """
    Freeze rows and/or columns above and left of a cell.
    """
    sheet = _get_sheet(workbook, sheet_name)

    min_col, min_row, max_col, max_row = _validate_range(
        cell
    )

    if min_col != max_col or min_row != max_row:
        raise ValueError(
            "Freeze panes requires one cell reference."
        )

    sheet.freeze_panes = cell.upper()

    return {
        "sheet_name": sheet_name,
        "freeze_at": cell.upper(),
        "status": "success",
    }


def apply_table_style(
    workbook: Workbook,
    sheet_name: str,
    cell_range: str,
    table_name: str = "SalesTable",
    style_name: str = "TableStyleMedium2",
) -> dict:
    """
    Convert a data range into a styled Excel table.

    The first row must contain unique text headers.
    """
    sheet = _get_sheet(workbook, sheet_name)

    min_col, min_row, max_col, max_row = _validate_range(
        cell_range
    )

    if min_row == max_row:
        raise ValueError(
            "A table must contain a header and at least one data row."
        )

    if style_name not in ALLOWED_TABLE_STYLES:
        raise ValueError(
            f"Unsupported table style: {style_name}"
        )

    if not re.fullmatch(
        r"[A-Za-z_][A-Za-z0-9_]*",
        table_name,
    ):
        raise ValueError(
            "Table name must contain letters, numbers, or underscores "
            "and cannot start with a number."
        )

    if any(
        table_name.lower() == existing.name.lower()
        for worksheet in workbook.worksheets
        for existing in worksheet.tables.values()
    ):
        raise ValueError(
            f"Table '{table_name}' already exists."
        )

    headers = [
        sheet.cell(min_row, col).value
        for col in range(min_col, max_col + 1)
    ]

    if not all(
        isinstance(header, str) and header.strip()
        for header in headers
    ):
        raise ValueError(
            "Table headers must be non-empty strings."
        )

    if len(set(headers)) != len(headers):
        raise ValueError(
            "Table headers must be unique."
        )

    table = Table(
        displayName=table_name,
        ref=cell_range,
    )

    table.tableStyleInfo = TableStyleInfo(
        name=style_name,
        showFirstColumn=False,
        showLastColumn=False,
        showRowStripes=True,
        showColumnStripes=False,
    )

    sheet.add_table(table)

    return {
        "sheet_name": sheet_name,
        "table_name": table_name,
        "range": cell_range,
        "style_name": style_name,
        "status": "success",
    }