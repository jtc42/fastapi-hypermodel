from typing import (
    Any,
    Callable,
    Dict,
    Mapping,
    Optional,
    Sequence,
    Union,
    cast,
)

from fastapi import FastAPI
from pydantic import (
    BaseModel,
    PrivateAttr,
    model_serializer,
)
from starlette.routing import Route
from typing_extensions import Self

from fastapi_hypermodel.hypermodel import AbstractHyperField, HasName, UrlType
from fastapi_hypermodel.utils import resolve_param_values


class UrlForType(BaseModel):
    hypermedia: Optional[UrlType] = None

    @model_serializer
    def serialize(self: Self) -> UrlType:
        return self.hypermedia or UrlType()


class UrlFor(UrlForType, AbstractHyperField):
    _endpoint: str = PrivateAttr()
    _param_values: Dict[str, str] = PrivateAttr()
    _condition: Optional[Callable[[Mapping[str, Any]], bool]] = PrivateAttr()
    _template: Optional[bool] = PrivateAttr()

    def __init__(
        self: Self,
        endpoint: Union[HasName, str],
        param_values: Optional[Dict[str, Any]] = None,
        condition: Optional[Callable[[Mapping[str, Any]], bool]] = None,
        template: Optional[bool] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._endpoint = (
            endpoint.__name__ if isinstance(endpoint, HasName) else endpoint
        )
        self._param_values: Dict[str, Any] = param_values or {}
        self._condition = condition
        self._template = template

    def __build_hypermedia__(
        self: Self,
        app: Optional[FastAPI],
        values: Mapping[str, Any],
    ) -> UrlForType:
        if app is None:
            return self

        if self._condition is not None and not self._condition(values):
            return self

        if not self._template:
            resolved_params = resolve_param_values(self._param_values, values)
            uri_for = app.url_path_for(self._endpoint, **resolved_params)
            return UrlForType(hypermedia=UrlType(uri_for))

        routes = cast(Sequence[Route], app.router.routes)
        uri = next(
            (route.path for route in routes if route.name == self._endpoint),
            None,
        )
        return UrlForType(hypermedia=UrlType(uri))
