"""Posters request/input schemas."""

from typing import Annotated

from pydantic import BaseModel, Field


class PostersDownloadRequest(BaseModel):
    base_url: str = Field(..., min_length=1)
    token: str = Field(..., min_length=1)
    library: str = Field(..., min_length=1)
    output_dir: str = Field(default="posters", min_length=1)
    limit: Annotated[int | None, Field(ge=1)] = None
    dry_run: bool = False
