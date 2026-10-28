from backend.app.tools.file_tools import (
    load_spreadsheet,
    save_workbook,
)

from backend.app.tools.formula_tools import (
    apply_formula_to_column,
    create_sheet,
    preview_arithmetic_formula,
    write_formula,
)


workbook = load_spreadsheet(
    "outputs/sample_sales.xlsx"
)

# 1. Create Revenue column
result = apply_formula_to_column(
    workbook,
    sheet_name="Sales",
    target_column="D",
    formula_template="=B{row}*C{row}",
    header="Revenue",
)

print("\n=== FORMULAS CREATED ===")
print(result)

# 2. Preview calculations
print("\n=== REVENUE PREVIEW ===")

for row in range(2, 5):
    preview = preview_arithmetic_formula(
        workbook,
        "Sales",
        f"=B{row}*C{row}",
    )

    print(
        f"Row {row}: {preview['preview_result']}"
    )

# 3. Add Summary sheet
create_sheet(
    workbook,
    "Summary",
)

# 4. Add Excel SUM formula
write_formula(
    workbook,
    "Summary",
    "B2",
    "=SUM(Sales!D2:D4)",
)

workbook["Summary"]["A2"] = "Total Revenue"

# 5. Save
output_path = save_workbook(
    workbook,
    "outputs/sales_with_formulas.xlsx",
)

print("\nSaved:", output_path)
print("Open the workbook in Excel to calculate formulas.")