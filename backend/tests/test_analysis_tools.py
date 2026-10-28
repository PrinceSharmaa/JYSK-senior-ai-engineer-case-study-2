import pytest

from backend.app.tools.file_tools import create_workbook

from backend.app.tools.analysis_tools import (
    workbook_to_dataframe,
    get_summary_statistics,
    group_and_aggregate,
    filter_rows,
    get_top_n,
    analyze_missing_values,
    calculate_correlation,
)


@pytest.fixture
def sales_workbook():

    workbook = create_workbook("Sales")

    sheet = workbook["Sales"]

    sheet.append([
        "Region",
        "Product",
        "Revenue",
        "Quantity",
    ])

    sheet.append([
        "North",
        "Laptop",
        5000,
        5,
    ])

    sheet.append([
        "South",
        "Mouse",
        2000,
        20,
    ])

    sheet.append([
        "North",
        "Keyboard",
        3000,
        10,
    ])

    sheet.append([
        "West",
        "Monitor",
        4000,
        8,
    ])

    return workbook


def test_workbook_to_dataframe(sales_workbook):

    dataframe = workbook_to_dataframe(
        sales_workbook,
        "Sales",
    )

    assert len(dataframe) == 4
    assert len(dataframe.columns) == 4
    assert dataframe.iloc[0]["Region"] == "North"


def test_summary_statistics(sales_workbook):

    result = get_summary_statistics(
        sales_workbook,
        "Sales",
    )

    revenue = result["numeric_statistics"]["Revenue"]

    assert revenue["sum"] == 14000
    assert revenue["mean"] == 3500
    assert revenue["min"] == 2000
    assert revenue["max"] == 5000


def test_group_and_aggregate(sales_workbook):

    result = group_and_aggregate(
        sales_workbook,
        "Sales",
        group_by="Region",
        value_column="Revenue",
        aggregation="sum",
    )

    results = {
        row["Region"]: row["Revenue"]
        for row in result["results"]
    }

    assert results["North"] == 8000
    assert results["South"] == 2000
    assert results["West"] == 4000


def test_filter_rows(sales_workbook):

    result = filter_rows(
        sales_workbook,
        "Sales",
        column="Revenue",
        operator=">",
        value=3000,
    )

    assert result["total_matches"] == 2


def test_get_top_n(sales_workbook):

    result = get_top_n(
        sales_workbook,
        "Sales",
        column="Revenue",
        n=2,
    )

    assert len(result["rows"]) == 2
    assert result["rows"][0]["Revenue"] == 5000
    assert result["rows"][1]["Revenue"] == 4000


def test_missing_values():

    workbook = create_workbook("Data")

    sheet = workbook["Data"]

    sheet.append(["Product", "Revenue"])
    sheet.append(["Laptop", 1000])
    sheet.append(["Mouse", None])
    sheet.append(["Keyboard", 500])

    result = analyze_missing_values(
        workbook,
        "Data",
    )

    revenue = result["missing_values"][1]

    assert revenue["missing_count"] == 1

    assert revenue["missing_percentage"] == pytest.approx(
        33.33
    )


def test_correlation(sales_workbook):

    result = calculate_correlation(
        sales_workbook,
        "Sales",
        column_a="Revenue",
        column_b="Quantity",
    )

    assert -1 <= result["correlation"] <= 1
    assert result["sample_size"] == 4


def test_invalid_column(sales_workbook):

    with pytest.raises(ValueError):

        get_top_n(
            sales_workbook,
            "Sales",
            column="Unknown",
        )


def test_invalid_aggregation(sales_workbook):

    with pytest.raises(ValueError):

        group_and_aggregate(
            sales_workbook,
            "Sales",
            group_by="Region",
            value_column="Revenue",
            aggregation="execute_code",
        )


def test_invalid_filter_operator(sales_workbook):

    with pytest.raises(ValueError):

        filter_rows(
            sales_workbook,
            "Sales",
            column="Revenue",
            operator="eval",
            value=100,
        )


def test_duplicate_headers():

    workbook = create_workbook("Data")

    sheet = workbook["Data"]

    sheet.append(["Revenue", "Revenue"])
    sheet.append([100, 200])

    with pytest.raises(ValueError):

        workbook_to_dataframe(
            workbook,
            "Data",
        )


def test_missing_sheet(sales_workbook):

    with pytest.raises(ValueError):

        workbook_to_dataframe(
            sales_workbook,
            "Missing",
        )