import pytest

from backend.app.tools.file_tools import create_workbook

from backend.app.tools.chart_tools import (
    create_bar_chart,
    create_line_chart,
    create_pie_chart,
    create_scatter_chart,
    list_charts,
    remove_chart,
)


@pytest.fixture
def sales_workbook():
    workbook = create_workbook("Sales")
    sheet = workbook["Sales"]

    sheet.append([
        "Product",
        "Quantity",
        "Price",
        "Revenue",
    ])

    sheet.append(["Laptop", 5, 800, 4000])
    sheet.append(["Mouse", 20, 25, 500])
    sheet.append(["Keyboard", 10, 60, 600])

    return workbook


def test_create_bar_chart(sales_workbook):
    result = create_bar_chart(
        sales_workbook,
        "Sales",
        category_column="A",
        value_column="D",
        title="Revenue by Product",
    )

    assert result["status"] == "success"
    assert len(sales_workbook["Sales"]._charts) == 1


def test_create_horizontal_bar_chart(sales_workbook):
    create_bar_chart(
        sales_workbook,
        "Sales",
        category_column="A",
        value_column="D",
        horizontal=True,
    )

    chart = sales_workbook["Sales"]._charts[0]

    assert chart.type == "bar"


def test_create_line_chart(sales_workbook):
    result = create_line_chart(
        sales_workbook,
        "Sales",
        category_column="A",
        value_column="D",
    )

    assert result["chart_type"] == "line"
    assert len(sales_workbook["Sales"]._charts) == 1


def test_create_pie_chart(sales_workbook):
    result = create_pie_chart(
        sales_workbook,
        "Sales",
        category_column="A",
        value_column="D",
    )

    assert result["chart_type"] == "pie"
    assert len(sales_workbook["Sales"]._charts) == 1


def test_create_scatter_chart(sales_workbook):
    result = create_scatter_chart(
        sales_workbook,
        "Sales",
        x_column="B",
        y_column="C",
    )

    assert result["chart_type"] == "scatter"
    assert len(sales_workbook["Sales"]._charts) == 1


def test_list_charts(sales_workbook):
    create_bar_chart(
        sales_workbook,
        "Sales",
        category_column="A",
        value_column="D",
    )

    create_pie_chart(
        sales_workbook,
        "Sales",
        category_column="A",
        value_column="D",
        anchor="F20",
    )

    result = list_charts(
        sales_workbook,
        "Sales",
    )

    assert result["chart_count"] == 2
    assert result["charts"][0]["chart_type"] == "BarChart"
    assert result["charts"][1]["chart_type"] == "PieChart"


def test_remove_chart(sales_workbook):
    create_bar_chart(
        sales_workbook,
        "Sales",
        category_column="A",
        value_column="D",
    )

    result = remove_chart(
        sales_workbook,
        "Sales",
        chart_index=1,
    )

    assert result["status"] == "success"
    assert len(sales_workbook["Sales"]._charts) == 0


def test_invalid_chart_index(sales_workbook):
    with pytest.raises(ValueError):
        remove_chart(
            sales_workbook,
            "Sales",
            chart_index=1,
        )


def test_invalid_category_column(sales_workbook):
    with pytest.raises(ValueError):
        create_bar_chart(
            sales_workbook,
            "Sales",
            category_column="INVALID",
            value_column="D",
        )


def test_invalid_chart_rows(sales_workbook):
    with pytest.raises(ValueError):
        create_line_chart(
            sales_workbook,
            "Sales",
            category_column="A",
            value_column="D",
            start_row=5,
            end_row=2,
        )


def test_invalid_chart_anchor(sales_workbook):
    with pytest.raises(ValueError):
        create_pie_chart(
            sales_workbook,
            "Sales",
            category_column="A",
            value_column="D",
            anchor="INVALID",
        )


def test_missing_sheet(sales_workbook):
    with pytest.raises(ValueError):
        create_bar_chart(
            sales_workbook,
            "Unknown",
            category_column="A",
            value_column="D",
        )