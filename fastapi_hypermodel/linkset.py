from typing import (
    Any,
    Dict,
    Mapping,
    Optional,
    Type,
)

from pydantic import (
    BaseModel,
    Field,
    GetJsonSchemaHandler,
    PrivateAttr,
    model_serializer,
)
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema
from starlette.applications import Starlette
from typing_extensions import Self

from fastapi_hypermodel.hypermodel import AbstractHyperField


class LinkSetType(BaseModel):
    mapping: Mapping[str, AbstractHyperField[Any]] = Field(default_factory=dict)

    @model_serializer
    def serialize(self: Self) -> Mapping[str, AbstractHyperField[Any]]:
        return self if isinstance(self, Mapping) else self.mapping


class LinkSet(LinkSetType, AbstractHyperField[LinkSetType]):
    _mapping: Mapping[str, AbstractHyperField[Any]] = PrivateAttr(default_factory=dict)

    def __init__(
        self: Self,
        mapping: Optional[Mapping[str, AbstractHyperField[Any]]] = None,
    ) -> None:
        super().__init__()
        self._mapping = mapping or {}

    @classmethod
    def __get_pydantic_json_schema__(
        cls: Type[Self], __core_schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        json_schema = handler(__core_schema)
        json_schema = handler.resolve_ref_schema(json_schema)
        json_schema["type"] = "object"

        subclasses_schemas = AbstractHyperField.__schema_subclasses__(cls)
        json_schema["additionalProperties"] = {"anyOf": subclasses_schemas}

        nested_properties_value = "properties"
        if nested_properties_value in json_schema:
            del json_schema[nested_properties_value]

        return json_schema

    def __call__(
        self: Self, app: Optional[Starlette], values: Mapping[str, Any]
    ) -> LinkSetType:
        links: Dict[str, AbstractHyperField[Any]] = {}

        for key, hyperfield in self._mapping.items():
            hypermedia = hyperfield(app, values)

            if not hypermedia:
                continue

            links[key] = hypermedia

        return LinkSetType(mapping=links)
