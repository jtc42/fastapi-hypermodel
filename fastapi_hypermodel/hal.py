from typing import (
    Any,
    Callable,
    Dict,
    Mapping,
    Optional,
    Union,
)

from pydantic import (
    BaseModel,
    Field,
    PrivateAttr,
)
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from typing_extensions import Self

from fastapi_hypermodel.hypermodel import AbstractHyperField, HasName
from fastapi_hypermodel.url_type import UrlType
from fastapi_hypermodel.utils import get_route_from_app, resolve_param_values


class HALResponse(JSONResponse):
    media_type = "application/hal+json"


class HALForType(BaseModel):
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


class HALFor(HALForType, AbstractHyperField[HALForType]):
    # pylint: disable=too-many-instance-attributes
    _endpoint: str = PrivateAttr()
    _param_values: Dict[str, str] = PrivateAttr()
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
        param_values: Optional[Dict[str, str]] = None,
        description: Optional[str] = None,
        condition: Optional[Callable[[Mapping[str, Any]], bool]] = None,
        template: Optional[bool] = None,
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
        self._templated = template
        self._title = title
        self._name = name
        self._type = type_
        self._hreflang = hreflang
        self._profile = profile
        self._deprecation = deprecation

    def __build_hypermedia__(
        self: Self, app: Optional[Starlette], values: Mapping[str, Any]
    ) -> HALForType:
        if app is None:
            return HALForType()

        if self._condition and not self._condition(values):
            return HALForType()

        route = get_route_from_app(app, self._endpoint)
        method = next(iter(route.methods), None) if route.methods else None

        if not self._templated:
            params = resolve_param_values(self._param_values, values)
            uri_path = UrlType(app.url_path_for(self._endpoint, **params))
        else:
            uri_path = UrlType(route.path)

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
