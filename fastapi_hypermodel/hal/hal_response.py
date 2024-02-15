from collections import defaultdict
from itertools import chain
from typing import (
    Any,
    Dict,
    List,
    Mapping,
    Optional,
    Sequence,
    Union,
)

from starlette.responses import JSONResponse
from typing_extensions import Self

from .hal_hypermodel import HALForType

EmbeddedRawType = Union[Mapping[str, Union[Sequence[Any], Any]], Any]
LinksRawType = Union[Mapping[str, Union[Any, Sequence[Any]]], Any]


class HALResponse(JSONResponse):
    media_type = "application/hal+json"

    @staticmethod
    def _validate_embedded(
        content: Any,
    ) -> Dict[str, List[Any]]:
        embedded: EmbeddedRawType = content.get("_embedded")

        if embedded is None:
            return {}

        if not embedded:
            error_message = "If embedded is specified it must not be empty"
            raise TypeError(error_message)

        if not isinstance(embedded, Mapping):
            error_message = "Embedded must be a mapping"
            raise TypeError(error_message)

        validated_embedded: Dict[str, List[Any]] = defaultdict(list)
        for name, embedded_ in embedded.items():
            embedded_sequence = (
                embedded_ if isinstance(embedded_, Sequence) else [embedded_]
            )
            validated_embedded[name].extend(embedded_sequence)

        return validated_embedded

    @staticmethod
    def _validate_links(content: Any) -> Dict[str, List[HALForType]]:
        links: LinksRawType = content.get("_links")

        if links is None:
            return {}

        if not isinstance(links, Mapping):
            error_message = "Links must be a Mapping"
            raise TypeError(error_message)

        self_link_raw = links.get("self")

        if not self_link_raw:
            error_message = "If _links is present, self link must be specified"
            raise TypeError(error_message)

        self_link = HALForType.model_validate(self_link_raw)

        if self_link.templated:
            error_message = "Self link must not be templated"
            raise TypeError(error_message)

        if not self_link.href:
            error_message = "Self link must have non-empty href"
            raise TypeError(error_message)

        if not all(name for name in links):
            error_message = "All Links must have non-empty names"
            raise TypeError(error_message)

        validated_links: Dict[str, List[HALForType]] = defaultdict(list)
        for name, links_ in links.items():
            link_sequence = links_ if isinstance(links_, Sequence) else [links_]
            hal_for_type = [HALForType.model_validate(link_) for link_ in link_sequence]
            validated_links[name].extend(hal_for_type)

        return validated_links

    @staticmethod
    def _extract_curies(
        links: Mapping[str, Sequence[HALForType]],
    ) -> Sequence[HALForType]:
        curies = links.get("curies")

        if curies is None:
            return []

        for link in curies:
            if not link.templated:
                error_message = "Curies must be templated"
                raise TypeError(error_message)

            if not link.name:
                error_message = "Curies must have a name"
                raise TypeError(error_message)

            if not link.href:
                error_message = "Curies must have href"
                raise TypeError(error_message)

            key_in_template = "rel"
            if key_in_template not in link.href:
                error_message = "Curies must be have 'rel' parameter in href"
                raise TypeError(error_message)

        return curies

    @staticmethod
    def _validate_name_in_curies(curies: Sequence[HALForType], name: str) -> None:
        expected_name, separator, _ = name.partition(":")
        if not separator:
            return

        curie_names = [curie.name for curie in curies]
        if not curie_names:
            error_message = "CURIEs were used but none was specified"
            raise TypeError(error_message)

        if any(expected_name == name for name in curie_names):
            return

        error_message = f"No CURIE found for '{expected_name}' in _links"
        raise TypeError(error_message)

    def _validate(
        self: Self, content: Any, parent_curies: Optional[Sequence[HALForType]] = None
    ) -> None:
        if not content:
            return

        parent_curies = parent_curies or []

        links = self._validate_links(content)
        curies = self._extract_curies(links)
        combined_curies = list(chain(curies, parent_curies))

        for link_name in links:
            self._validate_name_in_curies(combined_curies, link_name)

        embedded = self._validate_embedded(content)

        for embedded_name in embedded:
            self._validate_name_in_curies(combined_curies, embedded_name)

        for embedded_ in embedded.values():
            for element in embedded_:
                self._validate(element, parent_curies=combined_curies)

    def render(self: Self, content: Any) -> bytes:
        self._validate(content)
        return super().render(content)


def get_hal_link(response: Any, link_name: str) -> Optional[HALForType]:
    links = response.get("_links", {})
    link = links.get(link_name, {})
    return HALForType.model_validate(link) if link else None
