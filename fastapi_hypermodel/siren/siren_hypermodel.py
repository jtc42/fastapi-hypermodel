from __future__ import annotations

from typing import (
    Any,
    Dict,
    List,
    Mapping,
    Sequence,
    Union,
    cast,
)

from pydantic import (
    ConfigDict,
    Field,
    model_serializer,
    model_validator,
)
from typing_extensions import Self

from fastapi_hypermodel.base import AbstractHyperField, HyperModel

from .siren_action import SirenActionFor, SirenActionType
from .siren_base import SirenBase
from .siren_link import SirenLinkFor, SirenLinkType


class SirenEntityType(SirenBase):
    properties: Union[Mapping[str, Any], None] = None
    entities: Union[Sequence[Union[SirenEmbeddedType, SirenLinkType]], None] = None
    links: Union[Sequence[SirenLinkType], None] = None
    actions: Union[Sequence[SirenActionType], None] = None


class SirenEmbeddedType(SirenEntityType):
    rel: Sequence[str] = Field()


SIREN_RESERVED_FIELDS = {
    "properties",
    "entities",
    "links",
    "actions",
}


class SirenHyperModel(HyperModel):
    properties: Dict[str, Any] = Field(default_factory=dict)
    entities: Sequence[Union[SirenEmbeddedType, SirenLinkType]] = Field(
        default_factory=list
    )
    links: Sequence[SirenLinkFor] = Field(default_factory=list)
    actions: Sequence[SirenActionFor] = Field(default_factory=list)

    # This config is needed to use the Self in Embedded
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @model_validator(mode="after")
    def add_hypermodels_to_entities(self: Self) -> Self:
        entities: List[Union[SirenEmbeddedType, SirenLinkType]] = []
        for name, field in self:
            alias = self.model_fields[name].alias or name

            if alias in SIREN_RESERVED_FIELDS:
                continue

            value: Sequence[Union[Any, Self]] = (
                field if isinstance(field, Sequence) else [field]
            )

            if not all(
                isinstance(element, (SirenHyperModel, SirenLinkType))
                for element in value
            ):
                continue

            for field_ in value:
                if isinstance(field_, SirenLinkType):
                    entities.append(field_)
                    continue

                child = self.as_embedded(field_, alias)
                entities.append(child)

            delattr(self, name)

        self.entities = entities

        return self

    @model_validator(mode="after")
    def add_properties(self: Self) -> Self:
        properties = {}
        for name, field in self:
            alias = self.model_fields[name].alias or name

            if alias in SIREN_RESERVED_FIELDS:
                continue

            value: Sequence[Any] = field if isinstance(field, Sequence) else [field]

            omit_types: Any = (
                AbstractHyperField,
                SirenLinkFor,
                SirenLinkType,
                SirenActionFor,
                SirenActionType,
                SirenHyperModel,
            )
            if any(isinstance(value_, omit_types) for value_ in value):
                continue

            properties[alias] = value if isinstance(field, Sequence) else field

            delattr(self, name)

        if not self.properties:
            self.properties = {}

        self.properties.update(properties)

        return self

    @model_validator(mode="after")
    def add_links(self: Self) -> Self:
        links_key = "links"
        validated_links: List[SirenLinkFor] = []
        for name, value in self:
            alias = self.model_fields[name].alias or name

            if alias != links_key or not value:
                continue

            links = cast(Sequence[SirenLinkFor], value)
            properties = self.properties or {}
            validated_links = self._validate_factory(links, properties)
            self.links = validated_links

        self.validate_has_self_link(validated_links)

        return self

    @staticmethod
    def validate_has_self_link(links: Sequence[SirenLinkFor]) -> None:
        if not links:
            return

        if any(link.rel == ["self"] for link in links):
            return

        error_message = "If links are present, a link with rel self must be present"
        raise ValueError(error_message)

    @model_validator(mode="after")
    def add_actions(self: Self) -> Self:
        actions_key = "actions"
        for name, value in self:
            alias = self.model_fields[name].alias or name

            if alias != actions_key or not value:
                continue

            properties = self.properties or {}
            actions = cast(Sequence[SirenActionFor], value)
            self.actions = self._validate_factory(actions, properties)

        return self

    @model_validator(mode="after")
    def no_action_outside_of_actions(self: Self) -> Self:
        for _, field in self:
            if not isinstance(field, (SirenActionFor, SirenActionType)):
                continue

            error_message = "All actions must be inside the actions property"
            raise ValueError(error_message)

        return self

    @model_serializer
    def serialize(self: Self) -> Mapping[str, Any]:
        return {self.model_fields[k].alias or k: v for k, v in self if v}

    @staticmethod
    def as_embedded(field: SirenHyperModel, rel: str) -> SirenEmbeddedType:
        return SirenEmbeddedType(rel=[rel], **field.model_dump())

    def parse_uri(self: Self, uri_template: str) -> str:
        return self._parse_uri(self.properties, uri_template)
