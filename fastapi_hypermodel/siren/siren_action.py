from __future__ import annotations

from itertools import starmap
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Mapping,
    Optional,
    Sequence,
    Type,
    Union,
    cast,
)

from fastapi.routing import APIRoute
from pydantic import (
    ConfigDict,
    Field,
    PrivateAttr,
    field_validator,
)
from pydantic.fields import FieldInfo
from starlette.applications import Starlette
from starlette.routing import Route
from typing_extensions import Self

from fastapi_hypermodel.base import (
    AbstractHyperField,
    HasName,
    UrlType,
    get_route_from_app,
)

from .siren_base import SirenBase
from .siren_field import SirenFieldType


class SirenActionType(SirenBase):
    name: str = Field(default="")
    method: str = Field(default="GET")
    href: UrlType = Field(default=UrlType())
    type_: Union[str, None] = Field(default=None, alias="type")
    fields: Union[Sequence[SirenFieldType], None] = Field(default=None)
    templated: Optional[bool] = Field(default=None)

    model_config = ConfigDict(
        populate_by_name=True,
    )

    @field_validator("name", "href")
    @classmethod
    def mandatory(cls: Type[Self], value: Union[str, None]) -> str:
        if not value:
            error_message = f"Field name and href are mandatory, {value}"
            raise ValueError(error_message)
        return value


class SirenActionFor(SirenActionType, AbstractHyperField[SirenActionType]):  # pylint: disable=too-many-instance-attributes
    _endpoint: str = PrivateAttr()
    _param_values: Mapping[str, str] = PrivateAttr()
    _templated: Optional[bool] = PrivateAttr()
    _condition: Union[Callable[[Mapping[str, Any]], bool], None] = PrivateAttr()
    _populate_fields: bool = PrivateAttr()

    # For details on the folllowing fields, check https://github.com/kevinswiber/siren
    _class: Union[Sequence[str], None] = PrivateAttr()
    _title: Union[str, None] = PrivateAttr()
    _name: str = PrivateAttr()
    _method: Union[str, None] = PrivateAttr()
    _type: Union[str, None] = PrivateAttr()
    _fields: Union[Sequence[SirenFieldType], None] = PrivateAttr()

    def __init__(
        self: Self,
        endpoint: Union[HasName, str],
        param_values: Union[Mapping[str, str], None] = None,
        templated: Optional[bool] = None,
        condition: Union[Callable[[Mapping[str, Any]], bool], None] = None,
        populate_fields: bool = True,
        title: Union[str, None] = None,
        type_: Union[str, None] = None,
        class_: Union[Sequence[str], None] = None,
        fields: Union[Sequence[SirenFieldType], None] = None,
        method: Union[str, None] = None,
        name: str = "",
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._endpoint = (
            endpoint.__name__ if isinstance(endpoint, HasName) else endpoint
        )
        self._param_values = param_values or {}
        self._templated = templated
        self._condition = condition
        self._populate_fields = populate_fields
        self._title = title
        self._type = type_
        self._fields = fields or []
        self._method = method
        self._name = name
        self._class = class_

    def _prepopulate_fields(
        self: Self, fields: Sequence[SirenFieldType], values: Mapping[str, Any]
    ) -> List[SirenFieldType]:
        if not self._populate_fields:
            return list(fields)

        for field in fields:
            value = values.get(field.name) or field.value
            field.value = str(value)
        return list(fields)

    def _compute_fields(
        self: Self, route: Route, values: Mapping[str, Any]
    ) -> List[SirenFieldType]:
        if not isinstance(route, APIRoute):  # pragma: no cover
            route.body_field = ""  # type: ignore
            route = cast(APIRoute, route)

        body_field = route.body_field
        if not body_field:
            return []

        annotation: Any = body_field.field_info.annotation or {}
        model_fields: Any = annotation.model_fields if annotation else {}
        model_fields = cast(Dict[str, FieldInfo], model_fields)

        fields = list(starmap(SirenFieldType.from_field_info, model_fields.items()))
        return self._prepopulate_fields(fields, values)

    def __call__(
        self: Self, app: Union[Starlette, None], values: Mapping[str, Any]
    ) -> Union[SirenActionType, None]:
        if app is None:
            return None

        if self._condition and not self._condition(values):
            return None

        route = get_route_from_app(app, self._endpoint)

        if not self._method:
            self._method = next(iter(route.methods or {}), "GET")

        uri_path = self._get_uri_path(
            templated=self._templated,
            endpoint=self._endpoint,
            app=app,
            values=values,
            params=self._param_values,
            route=route,
        )

        if not self._fields:
            self._fields = self._compute_fields(route, values)

        if not self._type and self._fields:
            self._type = "application/x-www-form-urlencoded"

        return SirenActionType(
            href=uri_path,
            name=self._name,
            fields=self._fields,
            method=self._method,
            title=self._title,
            type_=self._type,  # type: ignore
            class_=self._class,  # type: ignore
            templated=self._templated,
        )
