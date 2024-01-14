from __future__ import annotations

from itertools import starmap
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Literal,
    Mapping,
    Optional,
    Sequence,
    Type,
    Union,
    cast,
)

from fastapi.routing import APIRoute
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    field_validator,
    model_serializer,
    model_validator,
)
from pydantic.fields import FieldInfo
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from typing_extensions import Self

from fastapi_hypermodel.hypermodel import AbstractHyperField, HasName, HyperModel
from fastapi_hypermodel.url_type import UrlType
from fastapi_hypermodel.utils import (
    get_route_from_app,
    resolve_param_values,
)


class SirenBase(BaseModel):
    class_: Optional[Sequence[str]] = Field(default=None, alias="class")
    title: Optional[str] = Field(default=None)

    @model_serializer
    def serialize(self: Self) -> Mapping[str, Any]:
        return {self.model_fields[k].alias or k: v for k, v in self if v}


class SirenLinkType(SirenBase):
    rel: Sequence[str] = Field(default_factory=list)
    href: UrlType = Field(default=UrlType())
    type_: Optional[str] = Field(default=None, alias="type")

    @field_validator("rel", "href")
    @classmethod
    def mandatory(cls: Type[Self], value: Optional[str]) -> str:
        if not value:
            error_message = "Field rel and href are mandatory"
            raise ValueError(error_message)
        return value


class SirenLinkFor(SirenLinkType, AbstractHyperField[SirenLinkType]):
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

        properties = values.get("properties", values)
        uri_path = self._get_uri_path(app, properties, route)

        # Using model_validate to avoid conflicts with keyword class
        return SirenLinkType.model_validate({
            "href": uri_path,
            "rel": self._rel,
            "title": self._title,
            "type": self._type,
            "class": self._class,
        })


FieldType = Literal[
    "hidden",
    "text",
    "search",
    "tel",
    "url",
    "email",
    "password",
    "datetime",
    "date",
    "month",
    "week",
    "time",
    "datetime-local",
    "number",
    "range",
    "color",
    "checkbox",
    "radio",
    "file",
]


class SirenFieldType(SirenBase):
    name: str
    type_: Optional[FieldType] = Field(default=None, alias="type")
    value: Optional[Any] = None

    @classmethod
    def from_field_info(cls: Type[Self], name: str, field_info: FieldInfo) -> Self:
        return cls.model_validate({
            "name": name,
            "type": cls.parse_type(field_info.annotation),
            "value": field_info.default,
        })

    @staticmethod
    def parse_type(python_type: Optional[Type[Any]]) -> FieldType:
        type_repr = repr(python_type)
        if "str" in type_repr:
            return "text"

        if "float" in type_repr or "int" in type_repr:
            return "number"

        return "text"


class SirenActionType(SirenBase):
    name: str = Field(default="")
    method: Optional[str] = Field(default=None)
    href: UrlType = Field(default=UrlType())
    type_: Optional[str] = Field(
        default="application/x-www-form-urlencoded", alias="type"
    )
    fields: Optional[Sequence[SirenFieldType]] = Field(default=None)

    @field_validator("name", "href")
    @classmethod
    def mandatory(cls: Type[Self], value: Optional[str]) -> str:
        if not value:
            error_message = f"Field name and href are mandatory, {value}"
            raise ValueError(error_message)
        return value


class SirenActionFor(SirenActionType, AbstractHyperField[SirenActionType]):
    _endpoint: str = PrivateAttr()
    _param_values: Mapping[str, str] = PrivateAttr()
    _templated: bool = PrivateAttr()
    _condition: Optional[Callable[[Mapping[str, Any]], bool]] = PrivateAttr()

    # For details on the folllowing fields, check https://github.com/kevinswiber/siren
    _class: Optional[Sequence[str]] = PrivateAttr()
    _title: Optional[str] = PrivateAttr()
    _name: Optional[str] = PrivateAttr()
    _method: Optional[str] = PrivateAttr()
    _type: Optional[str] = PrivateAttr()
    _fields: Optional[Sequence[SirenFieldType]] = PrivateAttr()

    def __init__(
        self: Self,
        endpoint: Union[HasName, str],
        param_values: Optional[Mapping[str, str]] = None,
        templated: bool = False,
        condition: Optional[Callable[[Mapping[str, Any]], bool]] = None,
        title: Optional[str] = None,
        type_: Optional[str] = None,
        class_: Optional[Sequence[str]] = None,
        fields: Optional[Sequence[SirenFieldType]] = None,
        method: Optional[str] = None,
        name: Optional[str] = None,
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
        self._fields = fields or []
        self._method = method
        self._name = name
        self._class = class_

    def _get_uri_path(
        self: Self, app: Starlette, values: Mapping[str, Any], route: Union[Route, str]
    ) -> UrlType:
        if self._templated and isinstance(route, Route):
            return UrlType(route.path)

        params = resolve_param_values(self._param_values, values)
        return UrlType(app.url_path_for(self._endpoint, **params))

    def _prepopulate_fields(
        self: Self, fields: Sequence[SirenFieldType], values: Mapping[str, Any]
    ) -> List[SirenFieldType]:
        for field in fields:
            field.value = values.get(field.name) or field.value
        return list(fields)

    def _compute_fields(
        self: Self, route: Route, values: Mapping[str, Any]
    ) -> List[SirenFieldType]:
        if not isinstance(route, APIRoute):
            return []

        body_field = route.body_field
        if not body_field:
            return []

        annotation = body_field.field_info.annotation

        if not annotation:
            return []

        model_fields = cast(Optional[Dict[str, FieldInfo]], annotation.model_fields)  # type: ignore
        if not model_fields:
            return []

        fields = list(starmap(SirenFieldType.from_field_info, model_fields.items()))
        return self._prepopulate_fields(fields, values)

    def __call__(
        self: Self, app: Optional[Starlette], values: Mapping[str, Any]
    ) -> Optional[SirenActionType]:
        if app is None:
            return None

        if self._condition and not self._condition(values):
            return None

        route = get_route_from_app(app, self._endpoint)

        if not self._method:
            self._method = next(iter(route.methods or {}), None)

        uri_path = self._get_uri_path(app, values, route)

        if not self._fields:
            self._fields = self._compute_fields(route, values)

        # Using model_validate to avoid conflicts with class and type
        return SirenActionType.model_validate({
            "href": uri_path,
            "name": self._name,
            "fields": self._fields,
            "method": self._method,
            "title": self._title,
            "type": self._type,
            "class": self._class,
        })


class SirenEntityType(SirenBase):
    properties: Optional[Mapping[str, Any]] = None
    entities: Optional[Sequence[Union[SirenEmbeddedType, SirenLinkType]]] = None
    links: Optional[Sequence[SirenLinkType]] = None
    actions: Optional[Sequence[SirenActionType]] = None


class SirenEmbeddedType(SirenEntityType):
    rel: str = Field()


class SirenHyperModel(HyperModel):
    properties: Optional[Dict[str, Any]] = None
    entities: Optional[Sequence[Union[SirenEmbeddedType, SirenLinkType]]] = None
    links_: Optional[Sequence[Self]] = Field(default=None, alias="links")
    actions_: Optional[Sequence[SirenActionType]] = Field(default=None, alias="actions")

    # This config is needed to use the Self in Embedded
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @model_validator(mode="after")
    def add_properties(self: Self) -> Self:
        properties = {}
        for name, field in self:
            value: Sequence[Any] = field if isinstance(field, Sequence) else [field]

            omit_types: Any = (
                AbstractHyperField,
                SirenLinkFor,
                SirenActionFor,
                SirenHyperModel,
            )
            if any(isinstance(value_, omit_types) for value_ in value):
                continue

            built_in_types = {
                "properties",
                "entities",
                "links_",
                "actions_",
            }
            if name in built_in_types:
                continue

            alias = self.model_fields[name].alias or name
            properties[alias] = value if isinstance(field, Sequence) else field

            delattr(self, name)

        if not self.properties:
            self.properties = {}

        self.properties.update(properties)

        return self

    @model_validator(mode="after")
    def add_links(self: Self) -> Self:
        for name, value in self:
            key = self.model_fields[name].alias or name

            if key != "links" or not value:
                continue

            links = cast(Sequence[SirenLinkFor], value)

            self.properties = self.properties or {}

            self.links = [link(self._app, self.properties) for link in links]

        return self

    @model_validator(mode="after")
    def add_actions(self: Self) -> Self:
        for name, value in self:
            key = self.model_fields[name].alias or name

            if key != "actions" or not value:
                continue

            actions = cast(Sequence[SirenActionFor], value)

            self.properties = self.properties or {}

            self.actions = [action(self._app, self.properties) for action in actions]

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

            rel = self.model_fields[name].alias or name
            embedded = [self.as_embedded(field, rel) for field in value]
            entities.extend(embedded)
            delattr(self, name)

        self.entities = entities

        if not self.entities:
            delattr(self, "entities")

        return self

    @model_serializer
    def serialize(self: Self) -> Mapping[str, Any]:
        return {self.model_fields[k].alias or k: v for k, v in self if v}

    @staticmethod
    def as_embedded(field: SirenHyperModel, rel: str) -> SirenEmbeddedType:
        return SirenEmbeddedType(rel=rel, **field.model_dump())


class SirenResponse(JSONResponse):
    media_type = "application/siren+json"

    def _validate(self: Self, content: Any) -> None:
        pass

    def render(self: Self, content: Any) -> bytes:
        self._validate(content)
        return super().render(content)
