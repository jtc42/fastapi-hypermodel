from typing import (
    Any,
    Type,
)

import pydantic_core
from pydantic import GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from typing_extensions import Self

URL_TYPE_SCHEMA = {
    "type": "string",
    "format": "uri",
    "minLength": 1,
    "maxLength": 2**16,
}


class UrlType(str):
    @classmethod
    def __get_pydantic_core_schema__(
        cls: Type[Self], *_: Any
    ) -> pydantic_core.CoreSchema:
        return pydantic_core.core_schema.str_schema()

    @classmethod
    def __get_pydantic_json_schema__(
        cls: Type[Self],
        core_schema: pydantic_core.CoreSchema,
        handler: GetJsonSchemaHandler,
    ) -> JsonSchemaValue:
        json_schema = handler(core_schema)
        json_schema = handler.resolve_ref_schema(json_schema)
        json_schema.update(URL_TYPE_SCHEMA)

        return json_schema
