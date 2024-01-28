from __future__ import annotations

from typing import (
    Any,
    Type,
    Union,
)

from pydantic import (
    Field,
)
from pydantic.fields import FieldInfo
from typing_extensions import Self

from .siren_base import SirenBase


class SirenFieldType(SirenBase):
    name: str
    type_: Union[str, None] = Field(default=None, alias="type")
    value: Union[Any, None] = None

    @classmethod
    def from_field_info(cls: Type[Self], name: str, field_info: FieldInfo) -> Self:
        return cls.model_validate({
            "name": name,
            "type": cls.parse_type(field_info.annotation),
            "value": field_info.default,
        })

    @staticmethod
    def parse_type(python_type: Union[Type[Any], None]) -> str:
        type_repr = repr(python_type)

        text_types = ("str",)
        if any(text_type in type_repr for text_type in text_types):
            return "text"

        number_types = ("float", "int")
        if any(number_type in type_repr for number_type in number_types):
            return "number"

        return "text"
