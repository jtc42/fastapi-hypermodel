from __future__ import annotations

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

import pydantic_core
from frozendict import frozendict
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    GetCoreSchemaHandler,
    PrivateAttr,
    field_serializer,
    model_serializer,
    model_validator,
)
from starlette.applications import Starlette
from typing_extensions import Annotated, Self

from fastapi_hypermodel.base import (
    AbstractHyperField,
    HasName,
    HyperModel,
    UrlType,
    get_route_from_app,
)


class HALForType(BaseModel):
    href: UrlType = Field(default=UrlType())
    templated: Optional[bool] = None
    title: Optional[str] = None
    name: Optional[str] = None
    type_: Optional[str] = Field(default=None, alias="type")
    hreflang: Optional[str] = None
    profile: Optional[str] = None
    deprecation: Optional[str] = None

    model_config = ConfigDict(
        populate_by_name=True,
    )

    def __bool__(self: Self) -> bool:
        return bool(self.href)

    @model_serializer
    def serialize(self: Self) -> Union[Mapping[str, Any], Sequence[Mapping[str, Any]]]:
        if isinstance(self, Sequence):
            return [
                {value.model_fields[k].alias or k: v for k, v in value if v}  # type: ignore
                for value in self
            ]
        return {self.model_fields[k].alias or k: v for k, v in self if v}


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
        self._condition = condition
        self._templated = templated
        self._title = title
        self._name = name
        self._type = type_
        self._hreflang = hreflang
        self._profile = profile
        self._deprecation = deprecation

    def __call__(
        self: Self, app: Optional[Starlette], values: Mapping[str, Any]
    ) -> Optional[HALForType]:
        if app is None:
            return None

        if self._condition and not self._condition(values):
            return None

        route = get_route_from_app(app, self._endpoint)

        uri_path = self._get_uri_path(
            templated=self._templated,
            endpoint=self._endpoint,
            app=app,
            values=values,
            params=self._param_values,
            route=route,
        )

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


class FrozenDict(frozendict):  # type: ignore
    @classmethod
    def __get_pydantic_core_schema__(
        cls: Type[Self],
        __source: Type[BaseModel],
        __handler: GetCoreSchemaHandler,
    ) -> pydantic_core.CoreSchema:
        hal_for_schema = HALFor.__get_pydantic_core_schema__(__source, __handler)
        hal_for_type_schema = HALForType.__get_pydantic_core_schema__(
            __source, __handler
        )
        hal_link_schema = pydantic_core.core_schema.union_schema([
            hal_for_schema,
            hal_for_type_schema,
        ])
        link_schema = pydantic_core.core_schema.union_schema([
            hal_link_schema,
            pydantic_core.core_schema.list_schema(hal_link_schema),
        ])
        return pydantic_core.core_schema.dict_schema(
            keys_schema=pydantic_core.core_schema.str_schema(),
            values_schema=link_schema,
        )


HALLinks = Annotated[Optional[FrozenDict], Field(alias="_links")]


class HALHyperModel(HyperModel):
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

        validated_links: Dict[str, HALLinkType] = {}
        for name, value in self:
            alias = self.model_fields[name].alias or name

            if alias != links_key or not value:
                continue

            links = cast(Mapping[str, HALLinkType], value)
            for link_name, link_ in links.items():
                valid_links = self._validate_factory(link_, vars(self))

                if not valid_links:
                    continue

                first_link, *_ = valid_links
                validated_links[link_name] = (
                    valid_links if isinstance(link_, Sequence) else first_link
                )

            validated_links["curies"] = HALHyperModel.curies()  # type: ignore

            self.links = FrozenDict(validated_links)

        return self

    @model_validator(mode="after")
    def add_hypermodels_to_embedded(self: Self) -> Self:
        embedded: Dict[str, Union[Self, Sequence[Self]]] = {}
        for name, field in self:
            value: Sequence[Union[Any, Self]] = (
                field if isinstance(field, Sequence) else [field]
            )

            if not all(isinstance(element, HALHyperModel) for element in value):
                continue

            key = self.model_fields[name].alias or name
            embedded[key] = value
            delattr(self, name)

        self.embedded = embedded

        if not self.embedded:
            delattr(self, "embedded")

        return self

    @field_serializer("links")
    @staticmethod
    def serialize_links(links: HALLinks) -> Dict[str, HALLinkType]:
        if not links:
            return {}
        return dict(links.items())
