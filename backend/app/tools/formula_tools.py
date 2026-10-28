import ast
import operator
import re
from typing import Any

from openpyxl import Workbook
from openpyxl.utils.cell import (
    get_column_letter,
    range_boundaries,
)
from openpyxl.workbook.properties import CalcProperties


MAX_FORMULA_ROWS = 10_000

ALLOWED_BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}

ALLOWED_UNARY_OPERATORS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _get_sheet(workbook: Workbook, sheet_name: str):
    if sheet_name not in workbook.sheetnames:
        raise ValueError(
            f"Sheet '{sheet_name}' not found."
        )

    return workbook[sheet_name]


def _validate_formula(formula: str) -> str:
    """
    Validate basic Excel formula syntax.

    This does not execute or fully parse Excel formulas.
    """
    if not isinstance(formula, str):
        raise ValueError("Formula must be a string.")

    formula = formula.strip()

    if not formula.startswith("="):
        raise ValueError(
            "Excel formulas must start with '='."
        )

    if len(formula) > 8192:
        raise ValueError(
            "Formula exceeds Excel's 8192-character limit."
        )

    if formula == "=":
        raise ValueError("Formula cannot be empty.")

    return formula


def set_recalculation(workbook: Workbook) -> None:
    """
    Request formula recalculation when Excel opens the file.
    """
    workbook.calculation = CalcProperties(
        calcMode="auto",
        fullCalcOnLoad=True,
        forceFullCalc=True,
    )


def write_formula(
    workbook: Workbook,
    sheet_name: str,
    cell: str,
    formula: str,
) -> dict:
    """
    Write an Excel formula into a cell.
    """
    sheet = _get_sheet(workbook, sheet_name)

    formula = _validate_formula(formula)

    min_col, min_row, max_col, max_row = range_boundaries(cell)

    if (
        min_col is None
        or min_row is None
        or max_col is None
        or max_row is None
        or min_col != max_col
        or min_row != max_row
    ):
        raise ValueError(
            "A single cell reference is required, e.g. D2."
        )

    sheet.cell(
        row=min_row,
        column=min_col,
        value=formula,
    )

    set_recalculation(workbook)

    return {
        "sheet_name": sheet_name,
        "cell": cell.upper(),
        "formula": formula,
        "status": "success",
    }


def write_cell_values(
    workbook: Workbook,
    sheet_name: str,
    values: dict[str, Any],
) -> dict:
    """
    Update multiple cells.

    Values beginning with '=' are treated as Excel formulas.
    """
    sheet = _get_sheet(workbook, sheet_name)

    if not values:
        raise ValueError("No cell values provided.")

    if len(values) > 1000:
        raise ValueError(
            "Maximum 1000 cells per request."
        )

    # Validate all references before modifying the workbook.
    validated = []

    for cell_ref, value in values.items():
        try:
            min_col, min_row, max_col, max_row = range_boundaries(
                cell_ref
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Invalid cell reference: {cell_ref}"
            ) from exc

        if (
            min_col is None
            or min_row is None
            or max_col is None
            or max_row is None
            or min_col != max_col
            or min_row != max_row
        ):
            raise ValueError(
                f"Expected single cell reference: {cell_ref}"
            )

        if isinstance(value, str) and value.startswith("="):
            _validate_formula(value)

        validated.append((min_row, min_col, value))

    for row, col, value in validated:
        sheet.cell(
            row=row,
            column=col,
            value=value,
        )

    set_recalculation(workbook)

    return {
        "sheet_name": sheet_name,
        "updated_cells": len(validated),
        "status": "success",
    }


def create_sheet(
    workbook: Workbook,
    sheet_name: str,
) -> dict:
    """
    Create a new worksheet.
    """
    if not sheet_name or not sheet_name.strip():
        raise ValueError(
            "Sheet name cannot be empty."
        )

    if sheet_name in workbook.sheetnames:
        raise ValueError(
            f"Sheet '{sheet_name}' already exists."
        )

    workbook.create_sheet(
        title=sheet_name
    )

    return {
        "sheet_name": sheet_name,
        "status": "created",
    }


def apply_formula_to_column(
    workbook: Workbook,
    sheet_name: str,
    target_column: str,
    formula_template: str,
    start_row: int = 2,
    end_row: int | None = None,
    header: str | None = None,
) -> dict:
    """
    Apply a formula template across multiple rows.

    Use {row} as the row placeholder.

    Example:
        formula_template="=B{row}*C{row}"

    Produces:
        =B2*C2
        =B3*C3
        =B4*C4
    """
    sheet = _get_sheet(workbook, sheet_name)

    if not re.fullmatch(r"[A-Za-z]{1,3}", target_column):
        raise ValueError(
            "Target column must be a column letter, e.g. D."
        )

    target_column = target_column.upper()

    column_index = 0

    for char in target_column:
        column_index = column_index * 26 + (
            ord(char) - ord("A") + 1
        )

    if column_index > 16384:
        raise ValueError(
            "Target column exceeds Excel's XFD limit."
        )

    if start_row < 2:
        raise ValueError(
            "Start row must be at least 2."
        )

    if end_row is None:
        end_row = sheet.max_row

    if end_row < start_row:
        raise ValueError(
            "End row must be greater than or equal to start row."
        )

    if end_row > 1_048_576:
        raise ValueError(
            "End row exceeds Excel's row limit."
        )

    if end_row - start_row + 1 > MAX_FORMULA_ROWS:
        raise ValueError(
            f"Maximum {MAX_FORMULA_ROWS} formula rows per request."
        )

    if formula_template.count("{row}") == 0:
        raise ValueError(
            "Formula template must contain '{row}'."
        )

    # Validate the complete formula batch before modifying cells.
    formulas = []

    for row in range(start_row, end_row + 1):
        formula = formula_template.replace(
            "{row}",
            str(row),
        )

        formulas.append(
            (row, _validate_formula(formula))
        )

    if header is not None:
        sheet.cell(
            row=1,
            column=column_index,
            value=header,
        )

    for row, formula in formulas:
        sheet.cell(
            row=row,
            column=column_index,
            value=formula,
        )

    set_recalculation(workbook)

    return {
        "sheet_name": sheet_name,
        "target_column": target_column,
        "start_row": start_row,
        "end_row": end_row,
        "formulas_created": len(formulas),
        "status": "success",
    }


def _evaluate_ast(node):
    """
    Safely evaluate a restricted arithmetic expression.

    No eval(), exec(), function calls, or arbitrary Python execution.
    """
    if isinstance(node, ast.Expression):
        return _evaluate_ast(node.body)

    if isinstance(node, ast.Constant):
        if type(node.value) in (int, float):
            return node.value
        raise ValueError("Only numeric constants are allowed.")

    if isinstance(node, ast.BinOp):
        operation = ALLOWED_BINARY_OPERATORS.get(
            type(node.op)
        )

        if operation is None:
            raise ValueError(
                "Unsupported arithmetic operator."
            )

        left = _evaluate_ast(node.left)
        right = _evaluate_ast(node.right)

        return operation(left, right)

    if isinstance(node, ast.UnaryOp):
        operation = ALLOWED_UNARY_OPERATORS.get(
            type(node.op)
        )

        if operation is None:
            raise ValueError(
                "Unsupported unary operator."
            )

        return operation(
            _evaluate_ast(node.operand)
        )

    raise ValueError(
        "Unsupported expression."
    )


def preview_arithmetic_formula(
    workbook: Workbook,
    sheet_name: str,
    formula: str,
) -> dict:
    """
    Preview a simple arithmetic formula using numeric cell values.

    Supported examples:
        =B2*C2
        =B2+C2
        =(B2+C2)/2

    Not a full Excel calculation engine.
    """
    sheet = _get_sheet(workbook, sheet_name)

    formula = _validate_formula(formula)

    expression = formula[1:]

    # Replace cell references with their numeric values.
    cell_pattern = re.compile(
        r"(?<![A-Za-z0-9_])\$?([A-Za-z]{1,3})\$?(\d+)(?![A-Za-z0-9_])"
    )

    def replace_cell(match):
        column = match.group(1)
        row = int(match.group(2))

        cell_value = sheet[f"{column}{row}"].value

        if type(cell_value) not in (int, float):
            raise ValueError(
                f"Cell {column}{row} is not a numeric constant."
            )

        return f"({cell_value})"

    expression = cell_pattern.sub(
        replace_cell,
        expression,
    )

    # Restrict the remaining expression to arithmetic characters.
    if not re.fullmatch(
        r"[0-9eE+\-*/().\s]+",
        expression,
    ):
        raise ValueError(
            "Only basic arithmetic formulas are supported for preview."
        )

    try:
        parsed = ast.parse(
            expression,
            mode="eval",
        )

        result = _evaluate_ast(parsed)

    except (
        SyntaxError,
        ZeroDivisionError,
        OverflowError,
    ) as exc:
        raise ValueError(
            "Formula cannot be evaluated."
        ) from exc

    if not isinstance(result, (int, float)):
        raise ValueError(
            "Formula did not produce a numeric result."
        )

    if abs(result) > 1e15:
        raise ValueError(
            "Calculated result exceeds preview limit."
        )

    return {
        "sheet_name": sheet_name,
        "formula": formula,
        "preview_result": float(result),
        "calculation_type": "python_arithmetic_preview",
    }