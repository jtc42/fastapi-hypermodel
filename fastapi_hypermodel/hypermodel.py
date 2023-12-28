from abc import ABC, abstractmethod
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


@runtime_checkable
class HasName(Protocol):
    __name__: str


class AbstractHyperField(ABC):
    @classmethod
    def __get_pydantic_core_schema__(cls: Type[Self], *_: Any) -> CoreSchema:
        return pydantic_core_schema.any_schema()

    @abstractmethod
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
                error_message = "Empty Fields Cannot be Processed"
                raise ValueError(error_message)

            parameters[field] = extract_value_by_name(self, field)

        return uri_template.format(**parameters)
