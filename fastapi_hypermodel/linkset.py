from typing import (
    Any,
    Dict,
    Mapping,
    Optional,
    Sequence,
    Type,
    Union,
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

LinkType = Union[AbstractHyperField[Any], Sequence[AbstractHyperField[Any]]]


class LinkSetType(BaseModel):
    mapping: Mapping[str, LinkType] = Field(default_factory=dict)

    @model_serializer
    def serialize(self: Self) -> Mapping[str, LinkType]:
        return self if isinstance(self, Mapping) else self.mapping


class LinkSet(LinkSetType, AbstractHyperField[LinkSetType]):
    _mapping: Mapping[str, LinkType] = PrivateAttr(default_factory=dict)

    def __init__(
        self: Self,
        mapping: Optional[Mapping[str, LinkType]] = None,
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
        links: Dict[str, LinkType] = {}

        for key, hyperfields in self._mapping.items():
            if isinstance(hyperfields, Sequence):
                hypermedia = [hyperfield(app, values) for hyperfield in hyperfields]
            else:
                hypermedia = hyperfields(app, values)

            if not hypermedia:
                continue

            links[key] = hypermedia

        return LinkSetType(mapping=links)
