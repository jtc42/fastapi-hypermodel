from __future__ import annotations

from enum import Enum
from typing import (
    Any,
    Callable,
    List,
    Mapping,
    Optional,
    Sequence,
    Union,
)

from pydantic import BaseModel, Field, PrivateAttr, model_validator
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from typing_extensions import Self

from fastapi_hypermodel.hypermodel import AbstractHyperField, HasName, HyperModel
from fastapi_hypermodel.url_type import UrlType
from fastapi_hypermodel.utils import get_route_from_app, resolve_param_values


class SirenForType(BaseModel):
    href: UrlType = Field(default=UrlType())
    templated: Optional[bool] = None
    title: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    hreflang: Optional[str] = None
    profile: Optional[str] = None
    deprecation: Optional[str] = None
    method: Optional[str] = None
    description: Optional[str] = None

    def __bool__(self: Self) -> bool:
        return bool(self.href)


class SirenFor(SirenForType, AbstractHyperField[SirenForType]):
    # pylint: disable=too-many-instance-attributes
    _endpoint: str = PrivateAttr()
    _param_values: Mapping[str, str] = PrivateAttr()
    _description: Optional[str] = PrivateAttr()
    _condition: Optional[Callable[[Mapping[str, Any]], bool]] = PrivateAttr()
    _templated: Optional[bool] = PrivateAttr()
    # For details on the folllowing fields, check https://datatracker.ietf.org/doc/html/draft-kelly-json-hal
    _title: Optional[str] = PrivateAttr()
    _name: Optional[str] = PrivateAttr()
    _type: Optional[str] = PrivateAttr()
    _hreflang: Optional[str] = PrivateAttr()
    _profile: Optional[str] = PrivateAttr()
    _deprecation: Optional[str] = PrivateAttr()

    def __init__(
        self: Self,
        endpoint: Union[HasName, str],
        param_values: Optional[Mapping[str, str]] = None,
        description: Optional[str] = None,
        condition: Optional[Callable[[Mapping[str, Any]], bool]] = None,
        templated: Optional[bool] = None,
        title: Optional[str] = None,
        name: Optional[str] = None,
        type_: Optional[str] = None,
        hreflang: Optional[str] = None,
        profile: Optional[str] = None,
        deprecation: Optional[str] = None,
    ) -> None:
        super().__init__()
        self._endpoint = (
            endpoint.__name__ if isinstance(endpoint, HasName) else endpoint
        )
        self._param_values = param_values or {}
        self._description = description
        self._condition = condition
        self._templated = templated
        self._title = title
        self._name = name
        self._type = type_
        self._hreflang = hreflang
        self._profile = profile
        self._deprecation = deprecation

    def _get_uri_path(
        self: Self, app: Starlette, values: Mapping[str, Any], route: Union[Route, str]
    ) -> UrlType:
        if self._templated and isinstance(route, Route):
            return UrlType(route.path)

        params = resolve_param_values(self._param_values, values)
        return UrlType(app.url_path_for(self._endpoint, **params))

    def __call__(
        self: Self, app: Optional[Starlette], values: Mapping[str, Any]
    ) -> HALForType:
        if app is None:
            return HALForType()

        if self._condition and not self._condition(values):
            return HALForType()

        route = get_route_from_app(app, self._endpoint)
        method = next(iter(route.methods), "GET") if route.methods else "GET"

        uri_path = self._get_uri_path(app, values, route)

        return HALForType(
            href=uri_path,
            method=method,
            description=self._description,
            templated=self._templated,
            title=self._title,
            name=self._name,
            type=self._type,
            hreflang=self._hreflang,
            profile=self._profile,
            deprecation=self._deprecation,
        )


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


class SirenHyperModel(HyperModel):
    properties: Optional[Mapping[str, Any]] = None
    entities: Optional[Sequence[Union[SirenEmbeddedType, SirenLinkType]]] = None
    links: Optional[Sequence[SirenLinkType]] = None
    actions: Optional[Sequence[SirenActionType]] = None

    @model_validator(mode="after")
    def add_hypermodels_to_entities(self: Self) -> Self:
        entities: List[Union[SirenEmbeddedType, SirenLinkType]] = []
        for name, field in self:
            value: Sequence[Union[Any, Self]] = (
                field if isinstance(field, Sequence) else [field]
            )

            if not all(isinstance(element, SirenHyperModel) for element in value):
                continue

            entities.extend(value)
            delattr(self, name)

        self.embedded = entities

        if not self.embedded:
            delattr(self, "entities")

        return self


class SirenResponse(JSONResponse):
    media_type = "application/siren+json"

    def _validate(self: Self, content: Any) -> None:
        pass

    def render(self: Self, content: Any) -> bytes:
        self._validate(content)
        return super().render(content)
