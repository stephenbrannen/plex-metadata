"""Shared request/input schemas."""

from pydantic import BaseModel, Field


class PosterDownloadRequest(BaseModel):
    output_dir: str = Field(default="posters", min_length=1)
