from typing import (
    Any,
    Callable,
    Dict,
    List,
    Mapping,
    Optional,
    Tuple,
    Union,
)

from pydantic import (
    BaseModel,
    Field,
    PrivateAttr,
)
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from typing_extensions import Self

from fastapi_hypermodel.hypermodel import AbstractHyperField, HasName
from fastapi_hypermodel.url_type import UrlType
from fastapi_hypermodel.utils import get_route_from_app, resolve_param_values


class HALForType(BaseModel):
    href: UrlType = Field(default=UrlType())
    templated: Optional[bool] = None
    title: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    hreflang: Optional[str] = None
    profile: Optional[str] = None
    deprecation: Optional[str] = None
    method: Optional[str] = None
    description: Optional[str] = None

    def __bool__(self: Self) -> bool:
        return bool(self.href)


class HALFor(HALForType, AbstractHyperField[HALForType]):
    # pylint: disable=too-many-instance-attributes
    _endpoint: Optional[str] = PrivateAttr()
    _param_values: Dict[str, str] = PrivateAttr()
    _description: Optional[str] = PrivateAttr()
    _condition: Optional[Callable[[Mapping[str, Any]], bool]] = PrivateAttr()
    _templated: Optional[bool] = PrivateAttr()
    # For details on the folllowing fields, check https://datatracker.ietf.org/doc/html/draft-kelly-json-hal
    _title: Optional[str] = PrivateAttr()
    _name: Optional[str] = PrivateAttr()
    _type: Optional[str] = PrivateAttr()
    _hreflang: Optional[str] = PrivateAttr()
    _profile: Optional[str] = PrivateAttr()
    _deprecation: Optional[str] = PrivateAttr()

    def __init__(
        self: Self,
        endpoint: Optional[Union[HasName, str]] = None,
        param_values: Optional[Dict[str, str]] = None,
        description: Optional[str] = None,
        condition: Optional[Callable[[Mapping[str, Any]], bool]] = None,
        template: Optional[bool] = None,
        title: Optional[str] = None,
        name: Optional[str] = None,
        type_: Optional[str] = None,
        hreflang: Optional[str] = None,
        profile: Optional[str] = None,
        deprecation: Optional[str] = None,
    ) -> None:
        super().__init__()
        self._endpoint = (
            endpoint.__name__ if isinstance(endpoint, HasName) else endpoint
        )
        self._param_values = param_values or {}
        self._description = description
        self._condition = condition
        self._templated = template
        self._title = title
        self._name = name
        self._type = type_
        self._hreflang = hreflang
        self._profile = profile
        self._deprecation = deprecation

    def _get_uri_path(
        self: Self, app: Starlette, values: Mapping[str, Any], route: Route
    ) -> UrlType:
        if self.href:
            return UrlType(self.href)

        if self._templated:
            return UrlType(route.path)

        if self._endpoint:
            params = resolve_param_values(self._param_values, values)
            return UrlType(app.url_path_for(self._endpoint, **params))

        error_message = "No valid configurations found to generate Href"
        raise ValueError(error_message)

    def _get_route_and_method(self: Self, app: Starlette) -> Tuple[Route, str]:
        if not self._endpoint:
            return Route(path=self.href, endpoint=self), "GET"

        route = get_route_from_app(app, self._endpoint)
        method = next(iter(route.methods), "GET") if route.methods else "GET"
        return route, method

    def __call__(
        self: Self, app: Optional[Starlette], values: Mapping[str, Any]
    ) -> HALForType:
        if app is None:
            return HALForType()

        if self._condition and not self._condition(values):
            return HALForType()

        route, method = self._get_route_and_method(app)

        uri_path = self._get_uri_path(app, values, route)

        return HALForType(
            href=uri_path,
            method=method,
            description=self._description,
            templated=self._templated,
            title=self._title,
            name=self._name,
            type=self._type,
            hreflang=self._hreflang,
            profile=self._profile,
            deprecation=self._deprecation,
        )


class HALForCurieType(HALFor, AbstractHyperField[HALForType]):
    templated: Optional[bool] = True

    def __bool__(self: Self) -> bool:
        return bool(self.href) and bool(self.name) and bool(self.templated)


class HALResponse(JSONResponse):
    media_type = "application/hal+json"

    def _is_link_valid(
        self: Self, link: Union[Dict[str, Any], List[Dict[str, Any]]]
    ) -> None:
        if not isinstance(link, list):
            if not link.get("href"):
                error_message = "Links must contain a href attribute"
                raise ValueError(error_message)

            HALForType.model_validate(link)
            return

        for link_item in link:
            self._is_link_valid(link_item)

    @staticmethod
    def _validate_curies(links: Union[Dict[str, Any], List[Dict[str, Any]]]) -> None:
        if not isinstance(links, list):
            error_message = "Curies must be a list of Links"
            raise ValueError(error_message)  # noqa: TRY004

        for curie_link in links:
            HALForCurieType.model_validate(links)

            if not curie_link.get("name"):
                error_message = "Curies must have a name"
                raise ValueError(error_message)

            if not curie_link.get("templated"):
                error_message = "Curies must be templated"
                raise ValueError(error_message)

            curie_uri_field_name = "rel"
            if curie_uri_field_name not in curie_link.get("href", ""):
                error_message = "Curies must have a templated URI with rel field"
                raise ValueError(error_message)

    @staticmethod
    def _validate_curie_name_exists(
        links: Optional[Dict[str, List[Dict[str, Any]]]], name: str
    ) -> None:
        expected_curie_name, separator, _ = name.partition(":")
        if not separator:
            return

        if not links:
            error_message = "CURIEs were used but there is no _links field"
            raise ValueError(error_message)

        curies = links.get("curies")
        if not curies:
            error_message = "CURIEs were used but not defined in _links"
            raise ValueError(error_message)

        for curie_link in curies:
            curie_name = curie_link.get("name")
            if expected_curie_name == curie_name:
                return

        error_message = "No CURIE found for {curie} in _links"
        raise ValueError(error_message)

    def _validate_links(self: Self, content: Dict[str, Any]) -> None:
        links = content.get("_links")

        if not links and links is not None:
            error_message = "If _links is present, it must not be empty"
            raise ValueError(error_message)

        if not links:
            return

        curies = links.get("curies")
        if curies:
            self._validate_curies(curies)

        for name, link in links.items():
            self._is_link_valid(link)
            self._validate_curie_name_exists(links, name)

    def _validate_embedded(self: Self, content: Dict[str, Any]) -> None:
        embedded_content = content.get("_embedded")

        if not embedded_content and embedded_content is not None:
            error_message = "If _embedded is present, it must not be empty"
            raise ValueError(error_message)

        if not embedded_content:
            return

        links = content.get("_links")
        for name, value in embedded_content.items():
            self._validate_curie_name_exists(links, name)
            self.validate(value)

    def validate(
        self: Self, content: Union[List[Dict[str, Any]], Dict[str, Any]]
    ) -> None:
        if not content:
            return

        if isinstance(content, dict):
            self._validate_links(content)
            self._validate_embedded(content)
            return

        for element in content:
            self.validate(element)

    def render(self: Self, content: Any) -> bytes:
        self.validate(content)
        return super().render(content)
