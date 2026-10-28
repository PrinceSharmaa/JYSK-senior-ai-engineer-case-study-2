from backend.app.tools.file_tools import (
    create_workbook,
    get_workbook_info,
    load_spreadsheet,
    save_workbook,
)


# Create workbook
workbook = create_workbook("Sales")

worksheet = workbook["Sales"]

# Add sample data
worksheet.append([
    "Product",
    "Quantity",
    "Unit Price",
])

worksheet.append([
    "Laptop",
    5,
    800,
])

worksheet.append([
    "Mouse",
    20,
    25,
])

worksheet.append([
    "Keyboard",
    10,
    60,
])

# Save workbook
output_path = save_workbook(
    workbook,
    "outputs/sample_sales.xlsx",
)

print("Workbook saved:", output_path)

# Reload workbook
loaded = load_spreadsheet(output_path)

# Inspect workbook
info = get_workbook_info(loaded)

print("\nWorkbook information:")

print(info)

print("\nExcel file operations successful!")