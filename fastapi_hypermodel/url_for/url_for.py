from typing import (
    Any,
    Callable,
    Mapping,
    Optional,
    Type,
    Union,
)

from pydantic import (
    BaseModel,
    GetJsonSchemaHandler,
    PrivateAttr,
    model_serializer,
)
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema
from starlette.applications import Starlette
from typing_extensions import Self

from fastapi_hypermodel.base import (
    URL_TYPE_SCHEMA,
    AbstractHyperField,
    HasName,
    UrlType,
    get_route_from_app,
)


class UrlForType(BaseModel):
    hypermedia: Optional[UrlType] = None

    @model_serializer
    def serialize(self: Self) -> UrlType:
        return self.hypermedia or UrlType()


class UrlFor(UrlForType, AbstractHyperField[UrlForType]):
    _endpoint: str = PrivateAttr()
    _param_values: Mapping[str, str] = PrivateAttr()
    _condition: Optional[Callable[[Mapping[str, Any]], bool]] = PrivateAttr()
    _templated: bool = PrivateAttr()

    def __init__(
        self: Self,
        endpoint: Union[HasName, str],
        param_values: Optional[Mapping[str, Any]] = None,
        condition: Optional[Callable[[Mapping[str, Any]], bool]] = None,
        templated: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._endpoint = (
            endpoint.__name__ if isinstance(endpoint, HasName) else endpoint
        )
        self._param_values = param_values or {}
        self._condition = condition
        self._templated = templated

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

    def __call__(
        self: Self,
        app: Optional[Starlette],
        values: Mapping[str, Any],
    ) -> Optional[UrlForType]:
        if app is None:
            return None

        if self._condition and not self._condition(values):
            return None

        route = get_route_from_app(app, self._endpoint)

        uri_path = self._get_uri_path(
            templated=self._templated,
            endpoint=self._endpoint,
            app=app,
            values=values,
            params=self._param_values,
            route=route,
        )

        return UrlForType(hypermedia=uri_path)
