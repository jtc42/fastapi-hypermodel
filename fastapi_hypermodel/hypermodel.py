from abc import ABC, abstractmethod
from string import Formatter
from typing import (
    Any,
    ClassVar,
    Dict,
    Generic,
    List,
    Mapping,
    Optional,
    Protocol,
    Type,
    TypeVar,
    cast,
    runtime_checkable,
)

import pydantic_core
from pydantic import (
    BaseModel,
    model_validator,
)
from starlette.applications import Starlette
from typing_extensions import Self

from fastapi_hypermodel.utils import extract_value_by_name


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
            subclasses_schemas.append(schema)

        return subclasses_schemas

    @abstractmethod
    def __call__(
        self: Self, app: Optional[Starlette], values: Mapping[str, Any]
    ) -> Optional[T]:
        raise NotImplementedError


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

    def parse_uri(self: Self, uri_template: str) -> str:
        parameters: Dict[str, str] = {}

        for _, field, *_ in Formatter().parse(uri_template):
            if not field:
                error_message = "Empty Fields Cannot be Processed"
                raise ValueError(error_message)

            parameters[field] = extract_value_by_name(self, field)

        return uri_template.format(**parameters)
