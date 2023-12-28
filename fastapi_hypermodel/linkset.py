from typing import (
    Any,
    Dict,
    Mapping,
    Optional,
    Type,
)

from fastapi import FastAPI
from pydantic import (
    GetJsonSchemaHandler,
)
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema
from pydantic_core import core_schema as pydantic_core_schema
from typing_extensions import Self

from fastapi_hypermodel.hypermodel import AbstractHyperField

_uri_schema = {"type": "string", "format": "uri", "minLength": 1, "maxLength": 2**16}

LinkSetType = Dict[str, AbstractHyperField]


class LinkSet(LinkSetType, AbstractHyperField):
    @classmethod
    def __get_pydantic_core_schema__(cls: Type[Self], *_: Any) -> CoreSchema:
        return pydantic_core_schema.dict_schema(
            keys_schema=pydantic_core_schema.str_schema(),
            values_schema=pydantic_core_schema.str_schema(),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls: Type[Self], core_schema_obj: CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        json_schema = handler(core_schema_obj)
        json_schema = handler.resolve_ref_schema(json_schema)
        json_schema["additionalProperties"] = _uri_schema

        return json_schema

    def __build_hypermedia__(
        self: Self, app: Optional[FastAPI], values: Mapping[str, Any]
    ) -> Optional[Any]:
        links = {k: u.__build_hypermedia__(app, values) for k, u in self.items()}
        return {k: u for k, u in links.items() if u is not None}
