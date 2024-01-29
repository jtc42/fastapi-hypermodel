from __future__ import annotations

from typing import (
    Optional,
    Sequence,
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class SirenBase(BaseModel):
    class_: Optional[Sequence[str]] = Field(default=None, alias="class")
    title: Optional[str] = Field(default=None)

    model_config = ConfigDict(populate_by_name=True)
