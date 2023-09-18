"""
Some functionality is based heavily on Flask-Marshmallow:
https://github.com/marshmallow-code/flask-marshmallow/blob/dev/src/flask_marshmallow/fields.py
"""

import abc
import re
import urllib
from typing import Any, Callable, Dict, List, Optional, Union, no_type_check

from fastapi import FastAPI
from pydantic import (
    BaseModel,
    GetCoreSchemaHandler,
    GetJsonSchemaHandler,
    PrivateAttr,
    model_validator,
)
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema, core_schema
from starlette.datastructures import URLPath
from starlette.routing import Route

_tpl_pattern = re.compile(r"\s*<\s*(\S*)\s*>\s*")

_uri_schema = {"type": "string", "format": "uri", "minLength": 1, "maxLength": 2**16}

class InvalidAttribute(AttributeError):
    pass


class AbstractHyperField(metaclass=abc.ABCMeta):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.any_schema()

    @abc.abstractmethod
    def __build_hypermedia__(self, app: Optional[FastAPI], values: Dict[str, Any]):
        return


class UrlType(str):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.str_schema(min_length=1, max_length=2**16)

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        json_schema = handler(core_schema)
        json_schema = handler.resolve_ref_schema(json_schema)
        json_schema.update({"format": "uri"})

        return json_schema

class UrlFor(UrlType, AbstractHyperField):
    def __init__(
        self,
        endpoint: Union[Callable, str],
        param_values: Optional[Dict[str, str]] = None,
        condition: Optional[Callable[[Dict[str, Any]], bool]] = None,
    ):
        self.endpoint: str = endpoint.__name__ if callable(endpoint) else endpoint
        self.param_values: Dict[str, str] = param_values or {}
        self.condition: Optional[Callable[[Dict[str, Any]], bool]] = condition
        super().__init__()

    @no_type_check
    def __new__(cls, *_, **__):
        return str.__new__(cls)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        str_schema = core_schema.str_schema(min_length=1, max_length=2**16)
        return core_schema.no_info_after_validator_function(cls.validate, str_schema)

    @classmethod
    def validate(cls, value: Any) -> "UrlFor":
        """
        Validate UrlFor object against itself.
        The UrlFor field type will only accept UrlFor instances.
        """
        # Return original object if it's already a UrlFor instance
        if value.__class__ == URLPath:
            return value
        # Otherwise raise an exception
        raise ValueError(
            f"UrlFor field should resolve to a starlette.datastructures.URLPath instance. Instead got {value.__class__}"
        )

    def __build_hypermedia__(
        self, app: Optional[FastAPI], values: Dict[str, Any]
    ) -> Optional[str]:
        if app is None:
            return None
        if self.condition is not None and not self.condition(values):
            return None
        resolved_params = resolve_param_values(self.param_values, values)
        return app.url_path_for(self.endpoint, **resolved_params)


class HALType(BaseModel):
    href: Optional[UrlType] = None
    method: Optional[str] = None
    description: Optional[str] = None


class HALFor(HALType, AbstractHyperField):
    _endpoint: str = PrivateAttr()
    _param_values: Optional[Dict[str, str]] = PrivateAttr()
    _description: Optional[str] = PrivateAttr()
    _condition: Optional[Callable[[Dict[str, Any]], bool]] = PrivateAttr()

    def __init__(
        self,
        endpoint: Union[Callable, str],
        param_values: Optional[Dict[str, str]] = None,
        description: Optional[str] = None,
        condition: Optional[Callable[[Dict[str, Any]], bool]] = None,
    ):
        super().__init__()  # type: ignore
        self._endpoint: str = endpoint.__name__ if callable(endpoint) else endpoint
        self._param_values: Dict[str, str] = param_values or {}
        self._description = description
        self._condition = condition

    def __build_hypermedia__(
        self, app: Optional[FastAPI], values: Dict[str, Any]
    ) -> Optional[HALType]:
        if app is None:
            return None
        if self._condition is not None and not self._condition(values):
            return None

        resolved_params = resolve_param_values(self._param_values, values)

        this_route = next(
            (
                route
                for route in app.routes
                if isinstance(route, Route) and route.name == self._endpoint
            ),
            None,
        )
        if not this_route:
            raise ValueError(f"No route found for endpoint {self._endpoint}")

        return HALType(
            href=UrlType(app.url_path_for(self._endpoint, **resolved_params)),
            method=next(iter(this_route.methods), None) if this_route.methods else None,
            description=self._description,
        )


LinkSetType = Dict[str, AbstractHyperField]


class LinkSet(LinkSetType, AbstractHyperField):  # pylint: disable=too-many-ancestors
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.dict_schema(
            keys_schema=core_schema.str_schema(), values_schema=core_schema.str_schema()
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema_obj: CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        json_schema = handler(core_schema_obj)
        json_schema = handler.resolve_ref_schema(json_schema)
        json_schema['additionalProperties'] = _uri_schema

        return json_schema

    def __build_hypermedia__(
        self, app: Optional[FastAPI], values: Dict[str, Any]
    ) -> Dict[str, str]:
        links = {k: u.__build_hypermedia__(app, values) for k, u in self.items()}  # type: ignore  # pylint: disable=no-member
        return {k: u for k, u in links.items() if u is not None}


def _tpl(val):
    """Return value within ``< >`` if possible, else return ``None``."""
    match = _tpl_pattern.match(val)
    if match:
        return match.groups()[0]
    return None


def _get_value(obj: Any, key: str, default: Optional[Any] = None):
    """Slightly-modified version of marshmallow.utils.get_value.
    If a dot-delimited ``key`` is passed and any attribute in the
    path is `None`, return `None`.
    """
    if "." in key:
        return _get_value_for_keys(obj, key.split("."), default)
    return _get_value_for_key(obj, key, default)


def _get_value_for_keys(obj: Any, keys: List[str], default: Any):
    if len(keys) == 1:
        return _get_value_for_key(obj, keys[0], default)
    value = _get_value_for_key(obj, keys[0], default)
    if value is None:
        return None
    return _get_value_for_keys(value, keys[1:], default)


def _get_value_for_key(obj: Any, key: str, default: Any):
    if not hasattr(obj, "__getitem__"):
        return getattr(obj, key, default)

    try:
        return obj[key]
    except (KeyError, IndexError, TypeError, AttributeError):
        return getattr(obj, key, default)


def _clean_attribute_value(value: Any) -> str:
    if isinstance(value, str):
        return urllib.parse.quote(value)
    return value


def resolve_param_values(
    param_values_template: Optional[Dict[str, str]], data_object: Dict[str, Any]
) -> Dict[str, str]:
    """
    Converts a dictionary of URL parameter substitution templates and a dictionary of real data values
    into a dictionary of recursively-populated URL parameter values.

    E.g. when passed the template {'person_id': '<id>'} and the data {'name': 'Bob', 'id': 'person02'},
    the function will return {'person_id': 'person02'}

    Args:
        param_values_template (Dict[str, str]): Dictionary of URL parameter substitution templates
        data_object (Dict[str, Any]): Dictionary containing name-to-value mapping of all fields

    Returns:
        Dict[str, str]: Populated dictionary of URL parameters
    """
    param_values = {}
    if param_values_template:
        for name, attr_tpl in param_values_template.items():
            attr_name = _tpl(str(attr_tpl))
            if attr_name:
                attribute_value = _get_value(data_object, attr_name, default=None)
                if attribute_value is None:
                    raise InvalidAttribute(
                        f"{attr_name} is not a valid attribute of {data_object}"
                    )
                param_values[name] = _clean_attribute_value(attribute_value)
    return param_values


class HyperModel(BaseModel):
    _hypermodel_bound_app: Optional[FastAPI] = None

    @classmethod
    def _generate_url(cls, endpoint, param_values, values):
        if cls._hypermodel_bound_app:
            return cls._hypermodel_bound_app.url_path_for(
                endpoint, **resolve_param_values(param_values, values)
            )
        return None

    @model_validator(mode='after')
    def _hypermodel_gen_href(self) -> 'HyperModel':
        new_values: dict[str, Any] = dict()

        for key, value in self:
            if isinstance(value, AbstractHyperField):
                new_values[key] = value.__build_hypermedia__(
                    self._hypermodel_bound_app, vars(self)
                )
            else:
                new_values[key] = value

        return self.model_construct(**new_values)

    @classmethod
    def init_app(cls, app: FastAPI):
        """
        Bind a FastAPI app to other HyperModel base class.
        This allows HyperModel to convert endpoint function names into
        working URLs relative to the application root.

        Args:
            app (FastAPI): Application to generate URLs from
        """
        cls._hypermodel_bound_app = app
