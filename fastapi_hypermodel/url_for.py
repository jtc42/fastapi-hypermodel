from typing import (
    Any,
    Callable,
    Dict,
    Mapping,
    Optional,
    Type,
    Union,
)

from fastapi import FastAPI
from pydantic import (
    BaseModel,
    GetJsonSchemaHandler,
    PrivateAttr,
    model_serializer,
)
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema
from typing_extensions import Self

from fastapi_hypermodel.hypermodel import (
    URL_TYPE_SCHEMA,
    AbstractHyperField,
    HasName,
    UrlType,
)
from fastapi_hypermodel.utils import get_route_from_app, resolve_param_values


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
        self._param_values = param_values or {}
        self._condition = condition
        self._template = template

    @classmethod
    def __get_pydantic_json_schema__(
        cls: Type[Self], __core_schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        json_schema = handler(__core_schema)
        json_schema = handler.resolve_ref_schema(json_schema)
        json_schema.update(URL_TYPE_SCHEMA)

        nested_properties_value = "properties"
        if nested_properties_value in json_schema:
            del json_schema[nested_properties_value]

        return json_schema

    def __build_hypermedia__(
        self: Self,
        app: Optional[FastAPI],
        values: Mapping[str, Any],
    ) -> UrlForType:
        if app is None:
            return self

        if self._condition and not self._condition(values):
            return self

        if not self._template:
            resolved_params = resolve_param_values(self._param_values, values)
            uri_for = app.url_path_for(self._endpoint, **resolved_params)
            return UrlForType(hypermedia=UrlType(uri_for))

        route = get_route_from_app(app, self._endpoint)
        href = UrlType(route.path)

        return UrlForType(hypermedia=href)
