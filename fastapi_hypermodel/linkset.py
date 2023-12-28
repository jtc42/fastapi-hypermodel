from typing import (
    Any,
    Dict,
    Generator,
    Mapping,
    Optional,
    Tuple,
    Type,
)

from fastapi import FastAPI
from pydantic import (
    BaseModel,
    Field,
    GetJsonSchemaHandler,
)
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema
from typing_extensions import Self

from fastapi_hypermodel.hypermodel import AbstractHyperField

_uri_schema = {"type": "string", "format": "uri", "minLength": 1, "maxLength": 2**16}


class LinkSetType(BaseModel):
    mapping: Dict[str, AbstractHyperField] = Field(default={})

    def __iter__(self: Self) -> Generator[Tuple[str, AbstractHyperField], None, None]:
        yield from dict(self.mapping).items()


class LinkSet(LinkSetType, AbstractHyperField):
    def __init__(
        self: Self, mapping: Optional[Dict[str, AbstractHyperField]] = None
    ) -> None:
        mapping = mapping or {}
        super().__init__(mapping=mapping)

    @classmethod
    def __get_pydantic_json_schema__(
        cls: Type[Self], __core_schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        json_schema = handler(__core_schema)
        json_schema = handler.resolve_ref_schema(json_schema)
        json_schema["additionalProperties"] = _uri_schema

        return json_schema

    def __build_hypermedia__(
        self: Self, app: Optional[FastAPI], values: Mapping[str, Any]
    ) -> Optional[Any]:
        links: Dict[str, AbstractHyperField] = {}

        for key, value in self:
            hypermedia = value.__build_hypermedia__(app, values)

            if not hypermedia:
                continue

            links[key] = hypermedia

        return links
