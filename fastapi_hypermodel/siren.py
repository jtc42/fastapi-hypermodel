from __future__ import annotations

from enum import Enum
from typing import (
    Any,
    Mapping,
    Optional,
    Sequence,
    Union,
)

from pydantic import BaseModel, Field

from fastapi_hypermodel.url_type import UrlType


class SirenBase(BaseModel):
    class_: Optional[Sequence[str]] = Field(default=None, alias="class")
    title: Optional[str] = None


POSSIBLE_FIELDS = [
    "hidden"
    "text"
    "search"
    "tel"
    "url"
    "email"
    "password"
    "datetime"
    "date"
    "month"
    "week"
    "time"
    "datetime-local"
    "number"
    "range"
    "color"
    "checkbox"
    "radio"
    "file"
]
FieldType = Enum("FieldType", POSSIBLE_FIELDS)


class SirenFieldType(SirenBase):
    name: str
    type_: Optional[FieldType] = Field(default=None, alias="type")
    value: Optional[str] = None


DEFAULT_ACTION_TYPE = "application/x-www-form-urlencoded"


class SirenActionType(SirenBase):
    name: str
    method: Optional[str] = None
    href: UrlType
    type_: Optional[str] = Field(default=DEFAULT_ACTION_TYPE, alias="type")
    fields: Optional[Sequence[SirenFieldType]]


class SirenLinkType(SirenBase):
    rel: Sequence[str]
    href: UrlType = Field(default=UrlType())
    type_: Optional[str] = Field(default=None, alias="type")


class SirenEntityType(SirenBase):
    properties: Optional[Mapping[str, Any]] = None
    entities: Optional[Sequence[Union[SirenEmbeddedType, SirenLinkType]]] = None
    links: Optional[Sequence[SirenLinkType]] = None
    actions: Optional[Sequence[SirenActionType]] = None


class SirenEmbeddedType(SirenEntityType):
    rel: str = Field()
