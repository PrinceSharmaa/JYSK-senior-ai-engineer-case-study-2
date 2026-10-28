from backend.app.tools.file_tools import (
    load_spreadsheet,
    save_workbook,
)

from backend.app.tools.chart_tools import (
    create_bar_chart,
    create_line_chart,
    create_pie_chart,
    create_scatter_chart,
    list_charts,
)


# Load the workbook from Phase 2.5
workbook = load_spreadsheet(
    "outputs/sales_formatted.xlsx"
)

# Chart 1: Revenue by Product
create_bar_chart(
    workbook,
    "Sales",
    category_column="A",
    value_column="D",
    title="Revenue by Product",
    anchor="F2",
)

# Chart 2: Product Revenue Distribution
create_pie_chart(
    workbook,
    "Sales",
    category_column="A",
    value_column="D",
    title="Revenue Distribution",
    anchor="F20",
)

# Chart 3: Quantity by Product
create_line_chart(
    workbook,
    "Sales",
    category_column="A",
    value_column="B",
    title="Quantity by Product",
    anchor="P2",
)

# Chart 4: Quantity vs Unit Price
create_scatter_chart(
    workbook,
    "Sales",
    x_column="B",
    y_column="C",
    title="Quantity vs Unit Price",
    anchor="P20",
)

print("\n=== CHARTS CREATED ===")
print(list_charts(workbook, "Sales"))

output_path = save_workbook(
    workbook,
    "outputs/sales_dashboard.xlsx",
)

print("\nDashboard saved:", output_path)