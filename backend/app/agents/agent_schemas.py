from typing import Any

from pydantic import BaseModel, Field
from pydantic import ConfigDict
from openpyxl.workbook.workbook import Workbook

class AgentAction(BaseModel):
    tool: str
    arguments: dict[str, Any] = Field(
        default_factory=dict
    )


class AgentPlan(BaseModel):
    reasoning: str = Field(
        description="A brief explanation of the action plan."
    )

    actions: list[AgentAction] = Field(
        default_factory=list,
        max_length=10,
    )


class AgentResult(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    success: bool

    message: str

    actions_executed: list[dict[str, Any]] = Field(
        default_factory=list
    )

    errors: list[str] = Field(
        default_factory=list
    )

    workbook: Workbook | None = Field(
        default=None,
        exclude=True,
    )