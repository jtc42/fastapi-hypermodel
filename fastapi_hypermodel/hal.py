from typing import (
    Any,
    Callable,
    Dict,
    Mapping,
    Optional,
    Union,
)

from fastapi import FastAPI
from pydantic import (
    BaseModel,
    PrivateAttr,
)
from typing_extensions import Self

from fastapi_hypermodel.hypermodel import AbstractHyperField, HasName, UrlType
from fastapi_hypermodel.utils import get_route_from_app, resolve_param_values


class HALType(BaseModel):
    href: Optional[UrlType] = None
    method: Optional[str] = None
    description: Optional[str] = None
    templated: Optional[bool] = None


class HALFor(HALType, AbstractHyperField):
    _endpoint: str = PrivateAttr()
    _param_values: Dict[str, str] = PrivateAttr()
    _description: Optional[str] = PrivateAttr()
    _condition: Optional[Callable[[Mapping[str, Any]], bool]] = PrivateAttr()
    _template: Optional[bool] = PrivateAttr()

    def __init__(
        self: Self,
        endpoint: Union[HasName, str],
        param_values: Optional[Dict[str, str]] = None,
        description: Optional[str] = None,
        condition: Optional[Callable[[Mapping[str, Any]], bool]] = None,
        template: Optional[bool] = None,
    ) -> None:
        super().__init__()
        self._endpoint: str = (
            endpoint.__name__ if isinstance(endpoint, HasName) else endpoint
        )
        self._param_values: Dict[str, str] = param_values or {}
        self._description = description
        self._condition = condition
        self._template = template

    def __build_hypermedia__(
        self: Self, app: Optional[FastAPI], values: Mapping[str, Any]
    ) -> HALType:
        if app is None:
            return self

        if self._condition and not self._condition(values):
            return self

        route = get_route_from_app(app, self._endpoint)
        method = next(iter(route.methods), None) if route.methods else None

        if not self._template:
            params = resolve_param_values(self._param_values, values)
            uri_path = UrlType(app.url_path_for(self._endpoint, **params))
        else:
            uri_path = UrlType(route.path)

        return HALType(
            href=uri_path,
            method=method,
            description=self._description,
            templated=self._template,
        )
