from typing import Any

import pandas as pd
from openpyxl.workbook.workbook import Workbook


ALLOWED_AGGREGATIONS = {
    "sum",
    "mean",
    "median",
    "min",
    "max",
    "count",
}

ALLOWED_OPERATORS = {
    "==",
    "!=",
    ">",
    ">=",
    "<",
    "<=",
}


def workbook_to_dataframe(
    workbook: Workbook,
    sheet_name: str,
) -> pd.DataFrame:
    """
    Convert an Excel worksheet into a Pandas DataFrame.

    Assumes the first row contains column headers.
    """

    if sheet_name not in workbook.sheetnames:
        raise ValueError(
            f"Worksheet '{sheet_name}' not found."
        )

    worksheet = workbook[sheet_name]

    rows = list(
        worksheet.iter_rows(values_only=True)
    )

    if not rows:
        return pd.DataFrame()

    headers = list(rows[0])

    if any(header is None or str(header).strip() == "" for header in headers):
        raise ValueError(
            "All columns must have non-empty headers."
        )

    if len(set(headers)) != len(headers):
        raise ValueError(
            "Duplicate column headers are not supported."
        )

    dataframe = pd.DataFrame(
        rows[1:],
        columns=headers,
    )

    return dataframe


def _validate_column(
    dataframe: pd.DataFrame,
    column: str,
):
    """
    Validate that a column exists.
    """

    if column not in dataframe.columns:
        raise ValueError(
            f"Column '{column}' not found. "
            f"Available columns: {list(dataframe.columns)}"
        )


def _validate_numeric_column(
    dataframe: pd.DataFrame,
    column: str,
):
    """
    Ensure a column contains numeric data.
    """

    _validate_column(dataframe, column)

    if not pd.api.types.is_numeric_dtype(
        dataframe[column]
    ):
        raise ValueError(
            f"Column '{column}' must be numeric."
        )

    if pd.api.types.is_bool_dtype(dataframe[column]):
        raise ValueError(
            f"Column '{column}' must contain numbers, not booleans."
        )


def get_summary_statistics(
    workbook: Workbook,
    sheet_name: str,
) -> dict:
    """
    Calculate summary statistics for numeric columns.
    """

    dataframe = workbook_to_dataframe(
        workbook,
        sheet_name,
    )

    numeric_columns = dataframe.select_dtypes(
        include="number"
    )

    numeric_columns = numeric_columns.select_dtypes(
        exclude="bool"
    )

    statistics = {}

    for column in numeric_columns.columns:

        series = numeric_columns[column]

        statistics[str(column)] = {
            "count": int(series.count()),
            "sum": float(series.sum()),
            "mean": (
                float(series.mean())
                if series.count() > 0
                else None
            ),
            "median": (
                float(series.median())
                if series.count() > 0
                else None
            ),
            "min": (
                float(series.min())
                if series.count() > 0
                else None
            ),
            "max": (
                float(series.max())
                if series.count() > 0
                else None
            ),
        }

    return {
        "sheet_name": sheet_name,
        "total_rows": len(dataframe),
        "numeric_statistics": statistics,
    }


def group_and_aggregate(
    workbook: Workbook,
    sheet_name: str,
    group_by: str,
    value_column: str,
    aggregation: str = "sum",
) -> dict:
    """
    Group records by a column and aggregate values.
    """

    dataframe = workbook_to_dataframe(
        workbook,
        sheet_name,
    )

    _validate_column(dataframe, group_by)
    _validate_column(dataframe, value_column)

    if aggregation not in ALLOWED_AGGREGATIONS:
        raise ValueError(
            f"Unsupported aggregation: {aggregation}"
        )

    if aggregation != "count":
        _validate_numeric_column(
            dataframe,
            value_column,
        )

    result = (
        dataframe.groupby(
            group_by,
            dropna=False,
        )[value_column]
        .agg(aggregation)
        .reset_index()
    )

    result = result.where(
        pd.notnull(result),
        None,
    )

    return {
        "sheet_name": sheet_name,
        "group_by": group_by,
        "value_column": value_column,
        "aggregation": aggregation,
        "results": result.to_dict(
            orient="records"
        ),
    }


def filter_rows(
    workbook: Workbook,
    sheet_name: str,
    column: str,
    operator: str,
    value: Any,
    limit: int = 100,
) -> dict:
    """
    Filter spreadsheet rows using a validated operator.
    """

    dataframe = workbook_to_dataframe(
        workbook,
        sheet_name,
    )

    _validate_column(dataframe, column)

    if operator not in ALLOWED_OPERATORS:
        raise ValueError(
            f"Unsupported filter operator: {operator}"
        )

    if not 1 <= limit <= 1000:
        raise ValueError(
            "Limit must be between 1 and 1000."
        )

    series = dataframe[column]

    try:
        if operator == "==":
            mask = series == value

        elif operator == "!=":
            mask = series != value

        elif operator == ">":
            mask = series > value

        elif operator == ">=":
            mask = series >= value

        elif operator == "<":
            mask = series < value

        else:
            mask = series <= value

    except (TypeError, ValueError) as exc:
        raise ValueError(
            "Filter value is incompatible with the column type."
        ) from exc

    filtered = dataframe.loc[mask]

    return {
        "sheet_name": sheet_name,
        "total_matches": len(filtered),
        "returned_rows": min(len(filtered), limit),
        "rows": filtered.head(limit).to_dict(
            orient="records"
        ),
    }


def get_top_n(
    workbook: Workbook,
    sheet_name: str,
    column: str,
    n: int = 5,
    ascending: bool = False,
) -> dict:
    """
    Return top or bottom N records.
    """

    dataframe = workbook_to_dataframe(
        workbook,
        sheet_name,
    )

    _validate_numeric_column(
        dataframe,
        column,
    )

    if not 1 <= n <= 100:
        raise ValueError(
            "n must be between 1 and 100."
        )

    result = dataframe.sort_values(
        by=column,
        ascending=ascending,
        na_position="last",
    ).head(n)

    return {
        "sheet_name": sheet_name,
        "sorted_by": column,
        "ascending": ascending,
        "rows": result.to_dict(
            orient="records"
        ),
    }


def analyze_missing_values(
    workbook: Workbook,
    sheet_name: str,
) -> dict:
    """
    Calculate missing values for each column.
    """

    dataframe = workbook_to_dataframe(
        workbook,
        sheet_name,
    )

    missing = dataframe.isna() | dataframe.eq("")

    total_rows = len(dataframe)

    results = []

    for column in dataframe.columns:

        missing_count = int(
            missing[column].sum()
        )

        percentage = (
            round(
                missing_count / total_rows * 100,
                2,
            )
            if total_rows > 0
            else 0.0
        )

        results.append({
            "column": str(column),
            "missing_count": missing_count,
            "missing_percentage": percentage,
        })

    return {
        "sheet_name": sheet_name,
        "total_rows": total_rows,
        "missing_values": results,
    }


def calculate_correlation(
    workbook: Workbook,
    sheet_name: str,
    column_a: str,
    column_b: str,
) -> dict:
    """
    Calculate Pearson correlation between two numeric columns.
    """

    dataframe = workbook_to_dataframe(
        workbook,
        sheet_name,
    )

    _validate_numeric_column(
        dataframe,
        column_a,
    )

    _validate_numeric_column(
        dataframe,
        column_b,
    )

    valid_rows = dataframe[
        [column_a, column_b]
    ].dropna()

    if len(valid_rows) < 2:
        raise ValueError(
            "At least two complete rows are required."
        )

    correlation = valid_rows[
        column_a
    ].corr(
        valid_rows[column_b]
    )

    return {
        "sheet_name": sheet_name,
        "column_a": column_a,
        "column_b": column_b,
        "correlation": (
            float(correlation)
            if pd.notna(correlation)
            else None
        ),
        "sample_size": len(valid_rows),
    }