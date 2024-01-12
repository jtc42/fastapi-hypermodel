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
    cast,
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    model_serializer,
    model_validator,
)
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from typing_extensions import Self

from fastapi_hypermodel.hypermodel import AbstractHyperField, HasName, HyperModel
from fastapi_hypermodel.url_type import UrlType
from fastapi_hypermodel.utils import get_route_from_app, resolve_param_values


class SirenBase(BaseModel):
    class_: Optional[Sequence[str]] = Field(default=None, alias="class")
    title: Optional[str] = None


class SirenLinkType(SirenBase):
    rel: Sequence[str] = Field(default_factory=list)
    href: UrlType = Field(default=UrlType())
    type_: Optional[str] = Field(default=None, alias="type")

    @model_serializer
    def serialize(self: Self) -> Mapping[str, Any]:
        return {self.model_fields[k].alias or k: v for k, v in self if v}


class SirenFor(SirenLinkType, AbstractHyperField[SirenLinkType]):
    # pylint: disable=too-many-instance-attributes
    _endpoint: str = PrivateAttr()
    _param_values: Mapping[str, str] = PrivateAttr()
    _templated: bool = PrivateAttr()
    _condition: Optional[Callable[[Mapping[str, Any]], bool]] = PrivateAttr()

    # For details on the folllowing fields, check https://datatracker.ietf.org/doc/html/draft-kelly-json-hal
    _title: Optional[str] = PrivateAttr()
    _type: Optional[str] = PrivateAttr()
    _rel: Sequence[str] = PrivateAttr()
    _class: Optional[Sequence[str]] = PrivateAttr()

    def __init__(
        self: Self,
        endpoint: Union[HasName, str],
        param_values: Optional[Mapping[str, str]] = None,
        templated: bool = False,
        condition: Optional[Callable[[Mapping[str, Any]], bool]] = None,
        title: Optional[str] = None,
        type_: Optional[str] = None,
        rel: Optional[Sequence[str]] = None,
        class_: Optional[Sequence[str]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._endpoint = (
            endpoint.__name__ if isinstance(endpoint, HasName) else endpoint
        )
        self._param_values = param_values or {}
        self._templated = templated
        self._condition = condition
        self._title = title
        self._type = type_
        self._rel = rel or []
        self._class = class_

    def _get_uri_path(
        self: Self, app: Starlette, values: Mapping[str, Any], route: Union[Route, str]
    ) -> UrlType:
        if self._templated and isinstance(route, Route):
            return UrlType(route.path)

        params = resolve_param_values(self._param_values, values)
        return UrlType(app.url_path_for(self._endpoint, **params))

    def __call__(
        self: Self, app: Optional[Starlette], values: Mapping[str, Any]
    ) -> Optional[SirenLinkType]:
        if app is None:
            return None

        if self._condition and not self._condition(values):
            return None

        route = get_route_from_app(app, self._endpoint)

        uri_path = self._get_uri_path(app, values, route)

        # Using model_validate to avoid conflicts with keyword class
        return SirenLinkType.model_validate({
            "href": uri_path,
            "rel": self._rel,
            "title": self._title,
            "type": self._type,
            "class": self._class,
        })


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
    links_: Optional[Sequence[Self]] = Field(default=None, alias="links")
    actions: Optional[Sequence[SirenActionType]] = None

    # This config is needed to use the Self in Embedded
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # @model_validator(mode="after")
    # def add_properties(self: Self) -> Self:
    #     properties: Dict[str, Any] = {}
    #     for key, field in self:
    #         value: Sequence[Any] = (
    #             field if isinstance(field, Sequence) else [field]
    #         )
    #         if any(isinstance(value_, AbstractHyperField) for value_ in value):
    #             continue

    #         properties[key] = value

    #         delattr(self, key)

    #     self.properties = properties

    #     return self

    @model_validator(mode="after")
    def add_links(self: Self) -> Self:
        for name, value in self:
            key = self.model_fields[name].alias or name

            if key != "links" or not value:
                continue

            links = cast(Sequence[SirenFor], value)

            self.links = [link(self._app, vars(self)) for link in links]

        return self

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

        self.entities = entities

        if not self.entities:
            delattr(self, "entities")

        return self


class SirenResponse(JSONResponse):
    media_type = "application/siren+json"

    def _validate(self: Self, content: Any) -> None:
        pass

    def render(self: Self, content: Any) -> bytes:
        self._validate(content)
        return super().render(content)
