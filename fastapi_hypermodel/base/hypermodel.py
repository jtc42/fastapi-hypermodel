import json
from abc import ABC, abstractmethod
from string import Formatter
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Generic,
    List,
    Mapping,
    Optional,
    Protocol,
    Sequence,
    Type,
    TypeVar,
    cast,
    runtime_checkable,
)

import jsonref
import pydantic_core
from pydantic import (
    BaseModel,
    model_validator,
)
from starlette.applications import Starlette
from typing_extensions import Self

from fastapi_hypermodel.base.utils import extract_value_by_name


@runtime_checkable
class HasName(Protocol):
    __name__: str


T = TypeVar("T", bound=BaseModel)


class AbstractHyperField(ABC, Generic[T]):
    @classmethod
    def __get_pydantic_core_schema__(
        cls: Type[Self], *_: Any
    ) -> pydantic_core.CoreSchema:
        return pydantic_core.core_schema.any_schema()

    @classmethod
    def __schema_subclasses__(
        cls: Type[Self], caller_class: Optional[Type[Self]] = None
    ) -> List[Dict[str, Any]]:
        subclasses_schemas: List[Dict[str, Any]] = []
        for subclass in cls.__subclasses__():
            if caller_class and issubclass(subclass, caller_class):
                continue

            if not issubclass(subclass, BaseModel):
                continue

            schema = subclass.model_json_schema()
            schema_dict = json.dumps(schema)
            deref_schema: Dict[str, Any] = jsonref.loads(schema_dict)

            subclasses_schemas.append(deref_schema)

        return subclasses_schemas

    @abstractmethod
    def __call__(
        self: Self, app: Optional[Starlette], values: Mapping[str, Any]
    ) -> Optional[T]:
        raise NotImplementedError


T2 = TypeVar("T2", bound=Callable[..., Any])


class HyperModel(BaseModel):
    _app: ClassVar[Optional[Starlette]] = None

    @model_validator(mode="after")
    def _build_hypermedia(self: Self) -> Self:
        for key, value in self:
            if not isinstance(value, AbstractHyperField):
                setattr(self, key, value)
                continue

            hyper_field = cast(AbstractHyperField[BaseModel], value)

            hypermedia = hyper_field(self._app, vars(self))

            if hypermedia:
                setattr(self, key, hypermedia)
                continue

            delattr(self, key)

        return self

    @classmethod
    def init_app(cls: Type[Self], app: Starlette) -> None:
        """
        Bind a FastAPI app to other HyperModel base class.
        This allows HyperModel to convert endpoint function names into
        working URLs relative to the application root.

        Args:
            app (FastAPI): Application to generate URLs from
        """
        cls._app = app

    @staticmethod
    def _parse_uri(values: Any, uri_template: str) -> str:
        parameters: Dict[str, str] = {}

        for _, field, *_ in Formatter().parse(uri_template):
            if not field:
                error_message = "Empty Fields Cannot be Processed"
                raise ValueError(error_message)

            parameters[field] = extract_value_by_name(values, field)

        return uri_template.format(**parameters)

    def parse_uri(self: Self, uri_template: str) -> str:
        return self._parse_uri(self, uri_template)

    def _validate_factory(
        self: Self, elements: Sequence[T2], properties: Mapping[str, str]
    ) -> List[T2]:
        validated_elements: List[T2] = []
        for element_factory in elements:
            if not callable(element_factory):
                validated_elements.append(element_factory)
                continue
            element = element_factory(self._app, properties)
            if not element:
                continue
            validated_elements.append(element)
        return validated_elements
