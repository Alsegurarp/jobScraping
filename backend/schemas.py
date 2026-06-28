from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Portal(str, Enum):
    INDEED = "indeed"
    LINKEDIN = "linkedin"
    OCC = "occ"
    COMPUTRABAJO = "computrabajo"
    GLASSDOOR = "glassdoor"


class RequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SearchParams(RequestModel):
    portals: list[Portal] = Field(min_length=1)
    max_results: int = Field(default=10, ge=1, le=50)
    refresh_cache: bool = False
    browser: bool = False
    research: bool = False

    @field_validator("portals")
    @classmethod
    def portals_must_be_unique(cls, value: list[Portal]) -> list[Portal]:
        if len(value) != len(set(value)):
            raise ValueError("portals cannot contain duplicates")
        return value


class ExtractLinksParams(RequestModel):
    browser: bool = False
    research: bool = False


class RunRecord(BaseModel):
    run_id: str
    type: Literal["search", "extract_links", "apply_approved_dry_run"]
    status: Literal["pending", "running", "completed", "failed"]
    command: list[str]
    params: dict[str, Any]
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    stdout: str = ""
    stderr: str = ""
    output_file: str
    result_file: str | None = None
    error: str | None = None
    return_code: int | None = None


class ResultSheet(BaseModel):
    name: str
    columns: list[str]
    rows: list[dict[str, Any]]


class ResultsPayload(BaseModel):
    run_id: str | None = None
    output_file: str
    sheets: dict[str, ResultSheet]
