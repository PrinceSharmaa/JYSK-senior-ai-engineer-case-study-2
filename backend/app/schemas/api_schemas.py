from typing import Any

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    file_id: str

    filename: str

    size_bytes: int

    message: str = (
        "File uploaded successfully."
    )


class AgentRequest(BaseModel):
    file_id: str

    instruction: str = Field(
        min_length=1,
        max_length=3000,
    )


class AgentExecutionResponse(BaseModel):
    success: bool

    file_id: str

    message: str

    actions_executed: list[
        dict[str, Any]
    ] = Field(
        default_factory=list
    )

    errors: list[str] = Field(
        default_factory=list
    )

    download_url: str | None = None