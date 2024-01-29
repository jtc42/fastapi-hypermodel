from __future__ import annotations

from typing import (
    Any,
    Optional,
)

import jsonschema
from starlette.responses import JSONResponse
from typing_extensions import Self

from .siren_action import SirenActionType
from .siren_link import SirenLinkType
from .siren_schema import schema


class SirenResponse(JSONResponse):
    media_type = "application/siren+json"

    @staticmethod
    def _validate(content: Any) -> None:
        jsonschema.validate(instance=content, schema=schema)

    def render(self: Self, content: Any) -> bytes:
        self._validate(content)
        return super().render(content)


def get_siren_link(response: Any, link_name: str) -> Optional[SirenLinkType]:
    links = response.get("links", [])
    link = next((link for link in links if link_name in link.get("rel")), None)
    return SirenLinkType.model_validate(link) if link else None


def get_siren_action(response: Any, action_name: str) -> Optional[SirenActionType]:
    actions = response.get("actions", [])
    action = next(
        (action for action in actions if action_name in action.get("name")), None
    )
    return SirenActionType.model_validate(action) if action else None
