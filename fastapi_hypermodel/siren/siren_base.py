from __future__ import annotations

from typing import (
    Sequence,
    Union,
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class SirenBase(BaseModel):
    class_: Union[Sequence[str], None] = Field(default=None, alias="class")
    title: Union[str, None] = Field(default=None)

    model_config = ConfigDict(populate_by_name=True)
