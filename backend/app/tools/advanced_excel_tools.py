"""Phase 8.3 deterministic openpyxl tools. All functions receive workbook from the agent.

Register these functions in TOOL_REGISTRY and document signatures in TOOL_GUIDE.
"""
from __future__ import annotations

from copy import copy
from typing import Any
import re

from openpyxl.workbook.workbook import Workbook
from openpyxl.utils import get_column_letter


def _sheet(workbook: Workbook, name: str):
    if name not in workbook.sheetnames:
        raise ValueError(f"Worksheet {name!r} does not exist")
    return workbook[name]


def rename_sheet(workbook: Workbook, sheet_name: str, new_name: str) -> dict:
    if not new_name.strip() or len(new_name) > 31:
        raise ValueError("Sheet name must contain 1–31 characters")
    if new_name in workbook.sheetnames:
        raise ValueError("Target worksheet already exists")
    _sheet(workbook, sheet_name).title = new_name
    return {"renamed": sheet_name, "new_name": new_name}


def duplicate_sheet(workbook: Workbook, sheet_name: str, new_name: str) -> dict:
    if new_name in workbook.sheetnames:
        raise ValueError("Target worksheet already exists")
    if not new_name.strip() or len(new_name) > 31:
        raise ValueError("Sheet name must contain 1–31 characters")
    copied = workbook.copy_worksheet(_sheet(workbook, sheet_name))
    copied.title = new_name
    return {"source": sheet_name, "created": new_name}


def delete_sheet(workbook: Workbook, sheet_name: str) -> dict:
    if len(workbook.sheetnames) == 1:
        raise ValueError("Cannot delete the last worksheet")
    workbook.remove(_sheet(workbook, sheet_name))
    return {"deleted": sheet_name}


def move_sheet(workbook: Workbook, sheet_name: str, position: int) -> dict:
    ws = _sheet(workbook, sheet_name)
    if not 0 <= position < len(workbook.worksheets):
        raise ValueError("Position is out of range (zero-based)")
    workbook._sheets.remove(ws)
    workbook._sheets.insert(position, ws)
    return {"sheet": sheet_name, "position": position}


def find_and_replace(
    workbook: Workbook, sheet_name: str, find: str, replace: str,
    column: str | None = None, match_case: bool = False,
    whole_cell: bool = False, max_replacements: int = 10000,
) -> dict:
    if not find:
        raise ValueError("Find text cannot be empty")
    if max_replacements < 1:
        raise ValueError("max_replacements must be positive")
    ws = _sheet(workbook, sheet_name)
    if column:
        header_map = {str(ws.cell(1, i).value).casefold(): i for i in range(1, ws.max_column + 1)}
        col_idx = header_map.get(column.casefold())
        if col_idx is None:
            raise ValueError(f"Column header {column!r} not found")
        cells = (ws.cell(r, col_idx) for r in range(2, ws.max_row + 1))
    else:
        cells = (cell for row in ws.iter_rows() for cell in row)
    flags = 0 if match_case else re.IGNORECASE
    pattern = re.compile(re.escape(find), flags)
    count = 0
    for cell in cells:
        # Never alter formulas by text replacement.
        if cell.data_type == 'f' or not isinstance(cell.value, str):
            continue
        old = cell.value
        if whole_cell:
            matched = old == find if match_case else old.casefold() == find.casefold()
            new = replace if matched else old
            n = int(matched)
        else:
            new, n = pattern.subn(lambda _: replace, old)
        if n:
            if count + n > max_replacements:
                raise ValueError("Replacement limit exceeded; transaction should be rolled back")
            cell.value = new
            count += n
    return {"sheet": sheet_name, "replacements": count}


def apply_auto_filter(workbook: Workbook, sheet_name: str, cell_range: str | None = None) -> dict:
    """Enable Excel's filter dropdowns. Does not remove or hide data rows."""
    ws = _sheet(workbook, sheet_name)
    if ws.max_row < 1 or ws.max_column < 1:
        raise ValueError("Worksheet is empty")
    ref = cell_range or f"A1:{get_column_letter(ws.max_column)}{ws.max_row}"
    ws.auto_filter.ref = ref
    return {"sheet": sheet_name, "filter_range": ref, "note": "Excel filter dropdowns enabled; no rows deleted"}


def clear_auto_filter(workbook: Workbook, sheet_name: str) -> dict:
    ws = _sheet(workbook, sheet_name)
    ws.auto_filter.ref = None
    ws.auto_filter.filterColumn = []
    return {"sheet": sheet_name, "filter_cleared": True}


def filter_rows_to_sheet(
    workbook: Workbook, sheet_name: str, column: str, operator: str,
    value: Any, output_sheet: str,
) -> dict:
    """Non-destructive filter: copy matching rows to a new sheet.

    Supported operators: ==, !=, >, >=, <, <=, contains.
    """
    if output_sheet in workbook.sheetnames:
        raise ValueError("Output sheet already exists")
    if not output_sheet.strip() or len(output_sheet) > 31:
        raise ValueError("Output sheet name must contain 1–31 characters")
    ws = _sheet(workbook, sheet_name)
    headers = [ws.cell(1, i).value for i in range(1, ws.max_column + 1)]
    indices = [i for i, h in enumerate(headers) if str(h).casefold() == column.casefold()]
    if len(indices) != 1:
        raise ValueError("Column must match exactly one header")
    col_index = indices[0]
    if operator not in {"==", "!=", ">", ">=", "<", "<=", "contains"}:
        raise ValueError("Unsupported filter operator")

    def matches(item: Any) -> bool:
        if item is None:
            return False
        if operator == "contains":
            return str(value).casefold() in str(item).casefold()
        if operator == "==":
            return item == value or str(item).casefold() == str(value).casefold()
        if operator == "!=":
            return not (item == value or str(item).casefold() == str(value).casefold())
        try:
            a, b = float(item), float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("Numeric comparison requires numeric cell and value") from exc
        return {">": a > b, ">=": a >= b, "<": a < b, "<=": a <= b}[operator]

    matching = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if matches(row[col_index]):
            matching.append(row)
    dest = workbook.create_sheet(output_sheet)
    dest.append(headers)
    for row in matching:
        dest.append(list(row))
    return {"source": sheet_name, "output_sheet": output_sheet, "matching_rows": len(matching)}
