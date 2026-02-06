"""Request/input schemas for posters repositories."""

from typing import Annotated

from pydantic import BaseModel, Field


class PostersDownloadRequest(BaseModel):
    base_url: str = Field(..., min_length=1)
    token: str = Field(..., min_length=1)
    library: str | None = Field(default=None, min_length=1)
    all_libraries: bool = False
    output_dir: str = Field(default="posters", min_length=1)
    limit: Annotated[int | None, Field(ge=1)] = None
    dry_run: bool = False
