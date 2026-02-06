"""Libraries request/input schemas."""

from pydantic import BaseModel, Field


class LibrariesListRequest(BaseModel):
    base_url: str = Field(..., min_length=1)
    token: str = Field(..., min_length=1)
