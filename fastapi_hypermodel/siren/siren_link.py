from __future__ import annotations

from typing import (
    Any,
    Callable,
    Mapping,
    Sequence,
    Type,
    Union,
)

from pydantic import (
    Field,
    PrivateAttr,
    field_validator,
)
from starlette.applications import Starlette
from starlette.routing import Route
from typing_extensions import Self

from fastapi_hypermodel.base import (
    AbstractHyperField,
    HasName,
    UrlType,
    get_route_from_app,
    resolve_param_values,
)

from .siren_base import SirenBase


class SirenLinkType(SirenBase):
    rel: Sequence[str] = Field(default_factory=list)
    href: UrlType = Field(default=UrlType())
    type_: Union[str, None] = Field(default=None, alias="type")

    @field_validator("rel", "href")
    @classmethod
    def mandatory(cls: Type[Self], value: Union[str, None]) -> str:
        if not value:
            error_message = "Field rel and href are mandatory"
            raise ValueError(error_message)
        return value


class SirenLinkFor(SirenLinkType, AbstractHyperField[SirenLinkType]):
    # pylint: disable=too-many-instance-attributes
    _endpoint: str = PrivateAttr()
    _param_values: Mapping[str, str] = PrivateAttr()
    _templated: bool = PrivateAttr()
    _condition: Union[Callable[[Mapping[str, Any]], bool], None] = PrivateAttr()

    # For details on the folllowing fields, check https://datatracker.ietf.org/doc/html/draft-kelly-json-hal
    _title: Union[str, None] = PrivateAttr()
    _type: Union[str, None] = PrivateAttr()
    _rel: Sequence[str] = PrivateAttr()
    _class: Union[Sequence[str], None] = PrivateAttr()

    def __init__(
        self: Self,
        endpoint: Union[HasName, str],
        param_values: Union[Mapping[str, str], None] = None,
        templated: bool = False,
        condition: Union[Callable[[Mapping[str, Any]], bool], None] = None,
        title: Union[str, None] = None,
        type_: Union[str, None] = None,
        rel: Union[Sequence[str], None] = None,
        class_: Union[Sequence[str], None] = None,
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
        self: Self, app: Union[Starlette, None], values: Mapping[str, Any]
    ) -> Union[SirenLinkType, None]:
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
