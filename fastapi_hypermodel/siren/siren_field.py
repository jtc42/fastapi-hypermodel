from __future__ import annotations

from typing import (
    Any,
    Optional,
    Type,
)

from pydantic import (
    ConfigDict,
    Field,
)
from pydantic.fields import FieldInfo
from typing_extensions import Self

from .siren_base import SirenBase


class SirenFieldType(SirenBase):
    name: str
    type_: Optional[str] = Field(default=None, alias="type")
    value: Optional[Any] = None

    model_config = ConfigDict(populate_by_name=True)

    @classmethod
    def from_field_info(cls: Type[Self], name: str, field_info: FieldInfo) -> Self:
        return cls(
            name=name,
            type_=cls.parse_type(field_info.annotation),  # type: ignore
            value=field_info.default,
        )

    @staticmethod
    def parse_type(python_type: Optional[Type[Any]]) -> str:
        type_repr = repr(python_type)

        text_types = ("str",)
        if any(text_type in type_repr for text_type in text_types):
            return "text"

        number_types = ("float", "int")
        if any(number_type in type_repr for number_type in number_types):
            return "number"

        return "text"
