from backend.app.tools.file_tools import load_spreadsheet
from backend.app.tools.read_tools import (
    inspect_columns,
    list_sheets,
    preview_sheet,
    read_cell_range,
)


workbook = load_spreadsheet(
    "outputs/sample_sales.xlsx"
)

print("\n=== AVAILABLE SHEETS ===")
print(list_sheets(workbook))

print("\n=== PREVIEW DATA ===")
print(preview_sheet(workbook, "Sales", limit=5))

print("\n=== COLUMN ANALYSIS ===")
print(inspect_columns(workbook, "Sales"))

print("\n=== CELL RANGE ===")
print(read_cell_range(workbook, "Sales", "A1:C3"))