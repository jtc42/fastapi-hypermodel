import abc
from string import Formatter
from typing import (
    Any,
    ClassVar,
    Dict,
    Mapping,
    Optional,
    Protocol,
    Type,
    runtime_checkable,
)

from fastapi import FastAPI
from pydantic import (
    BaseModel,
    GetCoreSchemaHandler,
    GetJsonSchemaHandler,
    model_validator,
)
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema
from pydantic_core import core_schema as pydantic_core_schema
from typing_extensions import Self

from fastapi_hypermodel.utils import extract_value_by_name

_uri_schema = {"type": "string", "format": "uri", "minLength": 1, "maxLength": 2**16}


@runtime_checkable
class HasName(Protocol):
    __name__: str


class AbstractHyperField(metaclass=abc.ABCMeta):
    @classmethod
    def __get_pydantic_core_schema__(cls: Type[Self], *_: Any) -> CoreSchema:
        return pydantic_core_schema.any_schema()

    @abc.abstractmethod
    def __build_hypermedia__(
        self: Self, app: Optional[FastAPI], values: Mapping[str, Any]
    ) -> Optional[Any]:
        return None


class UrlType(str):
    @classmethod
    def __get_pydantic_core_schema__(
        cls: Type[Self], source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        # pylint: disable=unused-argument
        return pydantic_core_schema.str_schema(min_length=1, max_length=2**16)

    @classmethod
    def __get_pydantic_json_schema__(
        cls: Type[Self], core_schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        json_schema = handler(core_schema)
        json_schema = handler.resolve_ref_schema(json_schema)
        json_schema.update({"format": "uri"})

        return json_schema


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


class HyperModel(BaseModel):
    _hypermodel_bound_app: ClassVar[Optional[FastAPI]] = None

    @model_validator(mode="after")
    def _build_hypermedia(self: Self) -> Self:
        for key, value in self:
            if not isinstance(value, AbstractHyperField):
                setattr(self, key, value)
                continue

            hypermedia = value.__build_hypermedia__(
                self._hypermodel_bound_app, vars(self)
            )
            setattr(self, key, hypermedia)

        return self

    @classmethod
    def init_app(cls: Type[Self], app: FastAPI) -> None:
        """
        Bind a FastAPI app to other HyperModel base class.
        This allows HyperModel to convert endpoint function names into
        working URLs relative to the application root.

        Args:
            app (FastAPI): Application to generate URLs from
        """
        cls._hypermodel_bound_app = app

    def parse_uri(self: Self, uri_template: str) -> str:
        parameters: Dict[str, str] = {}

        for _, field, *_ in Formatter().parse(uri_template):
            if not field:
                continue

            parameters[field] = extract_value_by_name(self, field)

        return uri_template.format(**parameters)
