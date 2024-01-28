from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Mapping,
    Optional,
    Sequence,
    Type,
    Union,
    cast,
)

from frozendict import frozendict
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, model_validator
from starlette.applications import Starlette
from starlette.routing import Route
from typing_extensions import Annotated, Self

from fastapi_hypermodel.base import (
    AbstractHyperField,
    HasName,
    HyperModel,
    UrlType,
    get_route_from_app,
    resolve_param_values,
)


class HALForType(BaseModel):
    href: UrlType = Field(default=UrlType())
    templated: Optional[bool] = None
    title: Optional[str] = None
    name: Optional[str] = None
    type_: Union[str, None] = Field(default=None, alias="type")
    hreflang: Optional[str] = None
    profile: Optional[str] = None
    deprecation: Optional[str] = None

    model_config = ConfigDict(
        populate_by_name=True,
    )

    def __bool__(self: Self) -> bool:
        return bool(self.href)


class HALFor(HALForType, AbstractHyperField[HALForType]):
    # pylint: disable=too-many-instance-attributes
    _endpoint: str = PrivateAttr()
    _param_values: Mapping[str, str] = PrivateAttr()
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
        endpoint: Union[HasName, str],
        param_values: Optional[Mapping[str, str]] = None,
        description: Optional[str] = None,
        condition: Optional[Callable[[Mapping[str, Any]], bool]] = None,
        templated: Optional[bool] = None,
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
        self._templated = templated
        self._title = title
        self._name = name
        self._type = type_
        self._hreflang = hreflang
        self._profile = profile
        self._deprecation = deprecation

    def _get_uri_path(
        self: Self, app: Starlette, values: Mapping[str, Any], route: Union[Route, str]
    ) -> UrlType:
        if self._templated and isinstance(route, Route):
            return UrlType(route.path)

        params = resolve_param_values(self._param_values, values)
        return UrlType(app.url_path_for(self._endpoint, **params))

    def __call__(
        self: Self, app: Optional[Starlette], values: Mapping[str, Any]
    ) -> HALForType:
        if app is None:
            return HALForType()

        if self._condition and not self._condition(values):
            return HALForType()

        route = get_route_from_app(app, self._endpoint)

        uri_path = self._get_uri_path(app, values, route)

        return HALForType(
            href=uri_path,
            templated=self._templated,
            title=self._title,
            name=self._name,
            type_=self._type,  # type: ignore
            hreflang=self._hreflang,
            profile=self._profile,
            deprecation=self._deprecation,
        )


HALLinkType = Union[HALFor, Sequence[HALFor]]

HALLinks = Annotated[Union[Dict[str, HALLinkType], None], Field(alias="_links")]


class HalHyperModel(HyperModel):
    curies_: ClassVar[Optional[Sequence[HALForType]]] = None
    links: HALLinks = None
    embedded: Mapping[str, Union[Self, Sequence[Self]]] = Field(
        default_factory=dict, alias="_embedded"
    )

    # This config is needed to use the Self in Embedded
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def register_curies(cls: Type[Self], curies: Sequence[HALForType]) -> None:
        cls.curies_ = curies

    @classmethod
    def curies(cls: Type[Self]) -> Sequence[HALForType]:
        return cls.curies_ or []

    @model_validator(mode="after")
    def add_links(self: Self) -> Self:
        links_key = "_links"
        if not self.links:
            self.links = {}

        for name, value in self:
            alias = self.model_fields[name].alias or name

            if alias != links_key or not value:
                continue

            links = cast(Mapping[str, HALLinkType], value)
            for link_name, link_ in links.items():
                is_sequence = isinstance(link_, Sequence)

                link_sequence: Sequence[HALFor] = link_ if is_sequence else [link_]
                valid_links = self._validate_factory(link_sequence, vars(self))

                if not valid_links:
                    continue

                first_link, *_ = valid_links
                self.links[link_name] = valid_links if is_sequence else first_link

            self.links["curies"] = HalHyperModel.curies()  # type: ignore

        return self

    @model_validator(mode="after")
    def add_hypermodels_to_embedded(self: Self) -> Self:
        embedded: Dict[str, Union[Self, Sequence[Self]]] = {}
        for name, field in self:
            value: Sequence[Union[Any, Self]] = (
                field if isinstance(field, Sequence) else [field]
            )

            if not all(isinstance(element, HalHyperModel) for element in value):
                continue

            key = self.model_fields[name].alias or name
            embedded[key] = value
            delattr(self, name)

        self.embedded = embedded

        if not self.embedded:
            delattr(self, "embedded")

        return self


EmbeddedRawType = Union[Mapping[str, Union[Sequence[Any], Any]], Any]
LinksRawType = Union[Mapping[str, Union[Any, Sequence[Any]]], Any]
