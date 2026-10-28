import inspect
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class ColumnWidthArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sheet_name: str = Field(min_length=1)
    column: str = Field(pattern=r"^[A-Za-z]{1,3}$")
    width: float = Field(gt=0, le=255)


class FormulaArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sheet_name: str = Field(min_length=1)
    cell: str = Field(pattern=r"^[A-Za-z]{1,3}[1-9][0-9]*$")
    formula: str = Field(min_length=2, max_length=1000)


class FormulaColumnArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sheet_name: str = Field(min_length=1)
    formula_template: str = Field(min_length=2, max_length=1000)
    start_row: int = Field(default=2, ge=1, le=1048576)
    end_row: int | None = Field(default=None, ge=1, le=1048576)
    header: str | None = None
    target_column: str = Field(
    ...,
    pattern=r"^[A-Za-z]{1,3}$",
    description=(
        "Excel column letter where formulas will be written, "
        "such as D, E, F, or AA. "
        "Never use a header name such as Revenue. "
        "Use the separate header argument for the column name."
    ),
)


STRICT_SCHEMAS = {
    "set_column_width": ColumnWidthArgs,
    "write_formula": FormulaArgs,
    "apply_formula_to_column": FormulaColumnArgs,
}


def validate_tool_call(
    tool_name: str,
    arguments: dict[str, Any],
    tool_registry: dict,
) -> dict[str, Any]:
    """
    Validate tool names and arguments before execution.
    """

    if tool_name not in tool_registry:
        raise ValueError(f"Unknown tool: {tool_name}")

    if not isinstance(arguments, dict):
        raise ValueError("Tool arguments must be an object.")

    if "workbook" in arguments:
        raise ValueError(
            "The workbook argument cannot be overridden."
        )

    tool = tool_registry[tool_name]

    signature = inspect.signature(tool)

    allowed_arguments = {
        name
        for name in signature.parameters
        if name != "workbook"
    }

    unknown_arguments = set(arguments) - allowed_arguments

    if unknown_arguments:
        raise ValueError(
            f"Unexpected arguments for {tool_name}: "
            f"{sorted(unknown_arguments)}"
        )

    required_arguments = {
        name
        for name, parameter in signature.parameters.items()
        if (
            name != "workbook"
            and parameter.default is inspect.Parameter.empty
        )
    }

    missing_arguments = required_arguments - set(arguments)

    if missing_arguments:
        raise ValueError(
            f"Missing arguments for {tool_name}: "
            f"{sorted(missing_arguments)}"
        )

    schema = STRICT_SCHEMAS.get(tool_name)

    if schema is not None:
        try:
            validated = schema.model_validate(arguments)
        except ValidationError as exc:
            raise ValueError(
                f"Invalid arguments for {tool_name}: {exc}"
            ) from exc

        return validated.model_dump(exclude_unset=True)

    return arguments.copy()