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
from starlette.routing import Route
from typing_extensions import Self

from fastapi_hypermodel.hypermodel import AbstractHyperField, HasName, UrlType
from fastapi_hypermodel.utils import resolve_param_values


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
    ) -> Optional[Any]:
        if app is None:
            return None
        if self._condition is not None and not self._condition(values):
            return None

        resolved_params = resolve_param_values(self._param_values, values)

        this_route = next(
            (
                route
                for route in app.routes
                if isinstance(route, Route) and route.name == self._endpoint
            ),
            None,
        )
        if not this_route:
            error_message = f"No route found for endpoint {self._endpoint}"
            raise ValueError(error_message)

        if not self._template:
            href = UrlType(app.url_path_for(self._endpoint, **resolved_params))
        else:
            href = UrlType(this_route.path)

        return HALType(
            href=UrlType(href),
            method=next(iter(this_route.methods), None) if this_route.methods else None,
            description=self._description,
            templated=self._template,
        )
