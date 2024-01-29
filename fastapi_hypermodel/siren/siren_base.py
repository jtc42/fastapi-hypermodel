from __future__ import annotations

from typing import (
    Any,
    Mapping,
    Sequence,
    Union,
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_serializer,
)
from typing_extensions import Self


class SirenBase(BaseModel):
    class_: Union[Sequence[str], None] = Field(default=None, alias="class")
    title: Union[str, None] = Field(default=None)

    model_config = ConfigDict(populate_by_name=True)

    @model_serializer
    def serialize(self: Self) -> Mapping[str, Any]:
        return {self.model_fields[k].alias or k: v for k, v in self if v}
