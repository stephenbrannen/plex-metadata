"""Posters request/input schemas."""

from pydantic import BaseModel, Field


class PostersDownloadRequest(BaseModel):
    output_dir: str = Field(default="posters", min_length=1)
