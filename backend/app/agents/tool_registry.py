from backend.app.tools.read_tools import (
    list_sheets,
    preview_sheet,
    inspect_columns,
)

from backend.app.tools.analysis_tools import (
    get_summary_statistics,
    group_and_aggregate,
    filter_rows,
    get_top_n,
    analyze_missing_values,
    calculate_correlation,
)

from backend.app.tools.formula_tools import (
    write_formula,
    write_cell_values,
    create_sheet,
    apply_formula_to_column,
)

from backend.app.tools.formatting_tools import (
    format_cells,
    apply_number_format,
    set_column_width,
    add_conditional_formatting,
    apply_color_scale,
    freeze_panes,
    apply_table_style,
)

from backend.app.tools.chart_tools import (
    create_bar_chart,
    create_line_chart,
    create_pie_chart,
    create_scatter_chart,
    list_charts,
)

from backend.app.tools.advanced_excel_tools import (
    rename_sheet,
    duplicate_sheet,
    delete_sheet,
    move_sheet,
    find_and_replace,
    apply_auto_filter,
    clear_auto_filter,
    filter_rows_to_sheet,
)


TOOL_REGISTRY = {
    # Reading
    "list_sheets": list_sheets,
    "preview_sheet": preview_sheet,
    "inspect_columns": inspect_columns,

    # Analysis
    "get_summary_statistics": get_summary_statistics,
    "group_and_aggregate": group_and_aggregate,
    "filter_rows": filter_rows,
    "get_top_n": get_top_n,
    "analyze_missing_values": analyze_missing_values,
    "calculate_correlation": calculate_correlation,

    # Formulas
    "write_formula": write_formula,
    "write_cell_values": write_cell_values,
    "create_sheet": create_sheet,
    "apply_formula_to_column": apply_formula_to_column,

    # Formatting
    "format_cells": format_cells,
    "apply_number_format": apply_number_format,
    "set_column_width": set_column_width,
    "add_conditional_formatting": add_conditional_formatting,
    "apply_color_scale": apply_color_scale,
    "freeze_panes": freeze_panes,
    "apply_table_style": apply_table_style,

    # Charts
    "create_bar_chart": create_bar_chart,
    "create_line_chart": create_line_chart,
    "create_pie_chart": create_pie_chart,
    "create_scatter_chart": create_scatter_chart,
    "list_charts": list_charts,
        # Phase 8.3 — Advanced Excel operations
    "rename_sheet": rename_sheet,
    "duplicate_sheet": duplicate_sheet,
    "delete_sheet": delete_sheet,
    "move_sheet": move_sheet,
    "find_and_replace": find_and_replace,
    "apply_auto_filter": apply_auto_filter,
    "clear_auto_filter": clear_auto_filter,
    "filter_rows_to_sheet": filter_rows_to_sheet,
}


def get_tool(tool_name: str):
    """
    Retrieve a registered Excel tool.
    """

    if tool_name not in TOOL_REGISTRY:
        raise ValueError(
            f"Unknown tool: {tool_name}"
        )

    return TOOL_REGISTRY[tool_name]


def get_available_tools() -> list[str]:
    """
    Return the available tool names.
    """

    return list(TOOL_REGISTRY.keys())