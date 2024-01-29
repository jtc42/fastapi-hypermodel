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
    Union,
    cast,
    runtime_checkable,
)

from pydantic import (
    BaseModel,
    model_validator,
)
from starlette.applications import Starlette
from starlette.routing import Route
from typing_extensions import Self

from fastapi_hypermodel.base.url_type import UrlType
from fastapi_hypermodel.base.utils import extract_value_by_name, resolve_param_values


@runtime_checkable
class HasName(Protocol):
    __name__: str


T = TypeVar("T", bound=BaseModel)


class AbstractHyperField(ABC, Generic[T]):
    @abstractmethod
    def __call__(
        self: Self, app: Optional[Starlette], values: Mapping[str, Any]
    ) -> Optional[T]:
        raise NotImplementedError

    @staticmethod
    def _get_uri_path(
        *,
        templated: Optional[bool],
        app: Starlette,
        values: Mapping[str, Any],
        route: Union[Route, str],
        params: Mapping[str, str],
        endpoint: str,
    ) -> UrlType:
        if templated and isinstance(route, Route):
            return UrlType(route.path)

        params = resolve_param_values(params, values)
        return UrlType(app.url_path_for(endpoint, **params))


R = TypeVar("R", bound=Callable[..., Any])


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
        self: Self, elements: Union[R, Sequence[R]], properties: Mapping[str, str]
    ) -> List[R]:
        if not isinstance(elements, Sequence):
            elements = [elements]

        validated_elements: List[R] = []
        for element_factory in elements:
            if not callable(element_factory):
                validated_elements.append(element_factory)
                continue
            element = element_factory(self._app, properties)
            if not element:
                continue
            validated_elements.append(element)
        return validated_elements
