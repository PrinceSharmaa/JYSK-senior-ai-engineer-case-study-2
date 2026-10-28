from openpyxl import Workbook
from openpyxl.chart import (
    BarChart,
    LineChart,
    PieChart,
    ScatterChart,
    Reference,
    Series,
)
from openpyxl.utils.cell import coordinate_from_string
from openpyxl.utils.cell import column_index_from_string
from openpyxl.utils.exceptions import CellCoordinatesException

MAX_CHART_ROWS = 5000

ALLOWED_CHART_TYPES = {
    "bar",
    "line",
    "pie",
    "scatter",
}


def _get_sheet(workbook: Workbook, sheet_name: str):
    if sheet_name not in workbook.sheetnames:
        raise ValueError(
            f"Worksheet '{sheet_name}' not found."
        )

    return workbook[sheet_name]


def _validate_column(column: str) -> int:
    """
    Convert Excel column letter into its numeric index.
    """
    try:
        index = column_index_from_string(column.upper())
    except (AttributeError, ValueError) as exc:
        raise ValueError(
            f"Invalid Excel column: {column}"
        ) from exc

    if not 1 <= index <= 16384:
        raise ValueError(
            "Column exceeds Excel limits."
        )

    return index


def _validate_chart_rows(
    start_row: int,
    end_row: int,
):
    if start_row < 2:
        raise ValueError(
            "Chart data must start from row 2 or later."
        )

    if end_row < start_row:
        raise ValueError(
            "End row must be greater than or equal to start row."
        )

    if end_row - start_row + 1 > MAX_CHART_ROWS:
        raise ValueError(
            f"Maximum {MAX_CHART_ROWS} chart data rows."
        )


def _validate_anchor(anchor: str):
    """
    Validate chart position, e.g. F2.
    """
    try:
        column, row = coordinate_from_string(anchor)
        column_index = column_index_from_string(column)

    except (TypeError, ValueError, CellCoordinatesException) as exc:
        raise ValueError(
            f"Invalid chart anchor: {anchor}"
        ) from exc

    if not 1 <= column_index <= 16384 or not 1 <= row <= 1048576:
        raise ValueError(
            "Chart anchor exceeds Excel limits."
        )


def create_bar_chart(
    workbook: Workbook,
    sheet_name: str,
    category_column: str,
    value_column: str,
    start_row: int = 2,
    end_row: int | None = None,
    title: str = "Bar Chart",
    anchor: str = "F2",
    horizontal: bool = False,
) -> dict:
    """
    Create a bar or column chart.
    """
    sheet = _get_sheet(workbook, sheet_name)

    category_index = _validate_column(category_column)
    value_index = _validate_column(value_column)

    if end_row is None:
        end_row = sheet.max_row

    _validate_chart_rows(start_row, end_row)
    _validate_anchor(anchor)

    chart = BarChart()

    chart.type = "bar" if horizontal else "col"
    chart.style = 10
    chart.title = title
    chart.y_axis.title = str(
        sheet.cell(1, value_index).value or "Value"
    )
    chart.x_axis.title = str(
        sheet.cell(1, category_index).value or "Category"
    )

    data = Reference(
        sheet,
        min_col=value_index,
        min_row=start_row - 1,
        max_row=end_row,
    )

    categories = Reference(
        sheet,
        min_col=category_index,
        min_row=start_row,
        max_row=end_row,
    )

    chart.add_data(
        data,
        titles_from_data=True,
    )

    chart.set_categories(categories)

    chart.width = 16
    chart.height = 9

    sheet.add_chart(chart, anchor)

    return {
        "sheet_name": sheet_name,
        "chart_type": "bar",
        "title": title,
        "anchor": anchor,
        "status": "success",
    }


def create_line_chart(
    workbook: Workbook,
    sheet_name: str,
    category_column: str,
    value_column: str,
    start_row: int = 2,
    end_row: int | None = None,
    title: str = "Line Chart",
    anchor: str = "F2",
) -> dict:
    """
    Create a line chart.
    """
    sheet = _get_sheet(workbook, sheet_name)

    category_index = _validate_column(category_column)
    value_index = _validate_column(value_column)

    if end_row is None:
        end_row = sheet.max_row

    _validate_chart_rows(start_row, end_row)
    _validate_anchor(anchor)

    chart = LineChart()

    chart.style = 13
    chart.title = title
    chart.y_axis.title = str(
        sheet.cell(1, value_index).value or "Value"
    )
    chart.x_axis.title = str(
        sheet.cell(1, category_index).value or "Category"
    )

    data = Reference(
        sheet,
        min_col=value_index,
        min_row=start_row - 1,
        max_row=end_row,
    )

    categories = Reference(
        sheet,
        min_col=category_index,
        min_row=start_row,
        max_row=end_row,
    )

    chart.add_data(
        data,
        titles_from_data=True,
    )

    chart.set_categories(categories)

    chart.width = 16
    chart.height = 9

    sheet.add_chart(chart, anchor)

    return {
        "sheet_name": sheet_name,
        "chart_type": "line",
        "title": title,
        "anchor": anchor,
        "status": "success",
    }


def create_pie_chart(
    workbook: Workbook,
    sheet_name: str,
    category_column: str,
    value_column: str,
    start_row: int = 2,
    end_row: int | None = None,
    title: str = "Pie Chart",
    anchor: str = "F2",
) -> dict:
    """
    Create a pie chart.
    """
    sheet = _get_sheet(workbook, sheet_name)

    category_index = _validate_column(category_column)
    value_index = _validate_column(value_column)

    if end_row is None:
        end_row = sheet.max_row

    _validate_chart_rows(start_row, end_row)
    _validate_anchor(anchor)

    chart = PieChart()

    chart.title = title
    chart.style = 10

    data = Reference(
        sheet,
        min_col=value_index,
        min_row=start_row - 1,
        max_row=end_row,
    )

    categories = Reference(
        sheet,
        min_col=category_index,
        min_row=start_row,
        max_row=end_row,
    )

    chart.add_data(
        data,
        titles_from_data=True,
    )

    chart.set_categories(categories)

    chart.width = 14
    chart.height = 9

    sheet.add_chart(chart, anchor)

    return {
        "sheet_name": sheet_name,
        "chart_type": "pie",
        "title": title,
        "anchor": anchor,
        "status": "success",
    }


def create_scatter_chart(
    workbook: Workbook,
    sheet_name: str,
    x_column: str,
    y_column: str,
    start_row: int = 2,
    end_row: int | None = None,
    title: str = "Scatter Chart",
    anchor: str = "F2",
) -> dict:
    """
    Create an XY scatter chart.
    """
    sheet = _get_sheet(workbook, sheet_name)

    x_index = _validate_column(x_column)
    y_index = _validate_column(y_column)

    if end_row is None:
        end_row = sheet.max_row

    _validate_chart_rows(start_row, end_row)
    _validate_anchor(anchor)

    chart = ScatterChart()

    chart.title = title
    chart.style = 13

    chart.x_axis.title = str(
        sheet.cell(1, x_index).value or "X"
    )

    chart.y_axis.title = str(
        sheet.cell(1, y_index).value or "Y"
    )

    x_values = Reference(
        sheet,
        min_col=x_index,
        min_row=start_row,
        max_row=end_row,
    )

    y_values = Reference(
        sheet,
        min_col=y_index,
        min_row=start_row,
        max_row=end_row,
    )

    series = Series(
        y_values,
        x_values,
        title=title,
    )

    chart.series.append(series)

    chart.width = 16
    chart.height = 9

    sheet.add_chart(chart, anchor)

    return {
        "sheet_name": sheet_name,
        "chart_type": "scatter",
        "title": title,
        "anchor": anchor,
        "status": "success",
    }


def list_charts(
    workbook: Workbook,
    sheet_name: str,
) -> dict:
    """
    List charts in a worksheet.
    """
    sheet = _get_sheet(workbook, sheet_name)

    charts = []

    for index, chart in enumerate(sheet._charts, start=1):
        charts.append({
            "chart_index": index,
            "chart_type": type(chart).__name__,
        })

    return {
        "sheet_name": sheet_name,
        "chart_count": len(charts),
        "charts": charts,
    }


def remove_chart(
    workbook: Workbook,
    sheet_name: str,
    chart_index: int,
) -> dict:
    """
    Remove a chart by its 1-based index.

    Note: openpyxl stores charts in a private collection.
    """
    sheet = _get_sheet(workbook, sheet_name)

    if not isinstance(chart_index, int) or isinstance(
        chart_index, bool
    ):
        raise ValueError(
            "Chart index must be an integer."
        )

    if not 1 <= chart_index <= len(sheet._charts):
        raise ValueError(
            f"Chart index {chart_index} does not exist."
        )

    sheet._charts.pop(chart_index - 1)

    return {
        "sheet_name": sheet_name,
        "removed_chart_index": chart_index,
        "status": "success",
    }