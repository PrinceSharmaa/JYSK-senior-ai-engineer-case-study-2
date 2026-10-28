from backend.app.tools.file_tools import (
    load_spreadsheet,
    save_workbook,
)

from backend.app.agents.excel_agent import (
    run_excel_agent,
)


workbook = load_spreadsheet(
    "outputs/sample_sales.xlsx"
)

user_request = """
Create a Revenue column in column D.
Calculate Revenue as Quantity multiplied by Unit Price.
Make the header row bold with a dark blue background.
Set the Product column width to 25.
"""

print("\nUSER REQUEST:")
print(user_request)

print("\nRUNNING SHEETPILOT AI...\n")

result = run_excel_agent(
    workbook=workbook,
    user_request=user_request,
)

print("SUCCESS:", result.success)
print("MESSAGE:", result.message)

print("\nEXECUTED ACTIONS:")

for action in result.actions_executed:
    print(
        "-",
        action["tool"],
        action["arguments"],
    )

if result.errors:
    print("\nERRORS:")
    for error in result.errors:
        print("-", error)

if result.success and result.workbook is not None:
    output_path = save_workbook(
        result.workbook,
        "outputs/agent_generated_sales.xlsx",
    )

    print("\nOUTPUT FILE:", output_path)
