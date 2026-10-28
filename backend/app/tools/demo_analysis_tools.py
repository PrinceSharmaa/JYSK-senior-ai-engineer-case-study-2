from backend.app.tools.file_tools import load_spreadsheet

from backend.app.tools.analysis_tools import (
    get_summary_statistics,
    get_top_n,
    analyze_missing_values,
    calculate_correlation,
)


workbook = load_spreadsheet(
    "outputs/sample_sales.xlsx"
)

print("\n=== SUMMARY STATISTICS ===")

print(
    get_summary_statistics(
        workbook,
        "Sales",
    )
)

print("\n=== TOP PRODUCTS BY QUANTITY ===")

print(
    get_top_n(
        workbook,
        "Sales",
        column="Quantity",
        n=3,
    )
)

print("\n=== MISSING VALUES ===")

print(
    analyze_missing_values(
        workbook,
        "Sales",
    )
)

print("\n=== QUANTITY VS UNIT PRICE CORRELATION ===")

print(
    calculate_correlation(
        workbook,
        "Sales",
        column_a="Quantity",
        column_b="Unit Price",
    )
)