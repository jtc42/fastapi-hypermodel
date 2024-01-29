from __future__ import annotations

from typing import (
    Any,
    Callable,
    Mapping,
    Optional,
    Sequence,
    Type,
    Union,
)

from pydantic import (
    ConfigDict,
    Field,
    PrivateAttr,
    field_validator,
)
from starlette.applications import Starlette
from typing_extensions import Self

from fastapi_hypermodel.base import (
    AbstractHyperField,
    HasName,
    UrlType,
    get_route_from_app,
)

from .siren_base import SirenBase


class SirenLinkType(SirenBase):
    rel: Sequence[str] = Field(default_factory=list)
    href: UrlType = Field(default=UrlType())
    type_: Optional[str] = Field(default=None, alias="type")

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("rel", "href")
    @classmethod
    def mandatory(cls: Type[Self], value: Optional[str]) -> str:
        if not value:
            error_message = "Field rel and href are mandatory"
            raise ValueError(error_message)
        return value


class SirenLinkFor(SirenLinkType, AbstractHyperField[SirenLinkType]):
    # pylint: disable=too-many-instance-attributes
    _endpoint: str = PrivateAttr()
    _param_values: Mapping[str, str] = PrivateAttr()
    _templated: Optional[bool] = PrivateAttr()
    _condition: Optional[Callable[[Mapping[str, Any]], bool]] = PrivateAttr()

    # For details on the folllowing fields, check https://datatracker.ietf.org/doc/html/draft-kelly-json-hal
    _title: Optional[str] = PrivateAttr()
    _type: Optional[str] = PrivateAttr()
    _rel: Sequence[str] = PrivateAttr()
    _class: Optional[Sequence[str]] = PrivateAttr()

    def __init__(
        self: Self,
        endpoint: Union[HasName, str],
        param_values: Optional[Mapping[str, str]] = None,
        templated: Optional[bool] = None,
        condition: Optional[Callable[[Mapping[str, Any]], bool]] = None,
        title: Optional[str] = None,
        type_: Optional[str] = None,
        rel: Optional[Sequence[str]] = None,
        class_: Optional[Sequence[str]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._endpoint = (
            endpoint.__name__ if isinstance(endpoint, HasName) else endpoint
        )
        self._param_values = param_values or {}
        self._templated = templated
        self._condition = condition
        self._title = title
        self._type = type_
        self._rel = rel or []
        self._class = class_

    def __call__(
        self: Self, app: Optional[Starlette], values: Mapping[str, Any]
    ) -> Optional[SirenLinkType]:
        if app is None:
            return None

        if self._condition and not self._condition(values):
            return None

        route = get_route_from_app(app, self._endpoint)

        properties = values.get("properties", values)
        uri_path = self._get_uri_path(
            templated=self._templated,
            endpoint=self._endpoint,
            app=app,
            values=properties,
            params=self._param_values,
            route=route,
        )

        # Using model_validate to avoid conflicts with keyword class
        return SirenLinkType(
            href=uri_path,
            rel=self._rel,
            title=self._title,
            type_=self._type,  # type: ignore
            class_=self._class,  # type: ignore
        )
