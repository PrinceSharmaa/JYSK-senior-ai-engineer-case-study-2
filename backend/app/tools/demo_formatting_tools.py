from backend.app.tools.file_tools import (
    load_spreadsheet,
    save_workbook,
)

from backend.app.tools.formatting_tools import (
    add_conditional_formatting,
    apply_color_scale,
    apply_number_format,
    apply_table_style,
    format_cells,
    freeze_panes,
    set_column_width,
)


# Load workbook created in Phase 2.4
workbook = load_spreadsheet(
    "outputs/sales_with_formulas.xlsx"
)

# 1. Style the header
format_cells(
    workbook,
    "Sales",
    "A1:D1",
    bold=True,
    font_color="FFFFFF",
    fill_color="1F4E78",
    font_size=12,
    horizontal_alignment="center",
)

# 2. Apply borders
format_cells(
    workbook,
    "Sales",
    "A1:D4",
    border=True,
)

# 3. Format revenue as currency
apply_number_format(
    workbook,
    "Sales",
    "D2:D4",
    "currency",
)

# 4. Set column widths
for column, width in {
    "A": 22,
    "B": 15,
    "C": 18,
    "D": 20,
}.items():
    set_column_width(
        workbook,
        "Sales",
        column,
        width,
    )

# 5. Highlight revenue below 1,000
add_conditional_formatting(
    workbook,
    "Sales",
    "D2:D4",
    condition="lessThan",
    threshold=1000,
    fill_color="FFC7CE",
)

# 6. Add a color scale to quantity
apply_color_scale(
    workbook,
    "Sales",
    "B2:B4",
)

# 7. Freeze header row
freeze_panes(
    workbook,
    "Sales",
    "A2",
)

# 8. Create a styled Excel table
apply_table_style(
    workbook,
    "Sales",
    "A1:D4",
    table_name="SalesData",
)

# 9. Save formatted workbook
output_path = save_workbook(
    workbook,
    "outputs/sales_formatted.xlsx",
)

print("\nExcel formatting completed!")
print("Saved workbook:", output_path)