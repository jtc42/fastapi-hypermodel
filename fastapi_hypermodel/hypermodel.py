"""
Some functionality is based heavily on Flask-Marshmallow:
https://github.com/marshmallow-code/flask-marshmallow/blob/dev/src/flask_marshmallow/fields.py
"""

import abc
import re
import urllib
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Tuple,
    Union,
    no_type_check,
)

from fastapi import FastAPI
from pydantic import BaseModel, PrivateAttr, root_validator
from pydantic.utils import update_not_none
from pydantic.validators import dict_validator
from starlette.datastructures import URLPath
from starlette.routing import BaseRoute, Host, Mount, Route

_tpl_pattern = re.compile(r"\s*<\s*(\S*)\s*>\s*")

_uri_schema = {"type": "string", "format": "uri", "minLength": 1, "maxLength": 2**16}


class InvalidAttribute(AttributeError):
    pass


class AbstractHyperField(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __build_hypermedia__(self, routes: Dict[str, Route], values: Dict[str, Any]):
        return


class UrlType(str):
    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        update_not_none(
            field_schema,
            **_uri_schema,
        )


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
    def __get_validators__(cls):
        yield cls.validate

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
        self, routes: Dict[str, Route], values: Dict[str, Any]
    ) -> Optional[str]:
        if self.condition is not None and not self.condition(values):
            return None

        route = routes.get(self.endpoint, None)
        if route is None:
            raise ValueError(f"No route found for endpoint {self.endpoint}")

        resolved_params = resolve_param_values(self.param_values, values)
        return route.url_path_for(self.endpoint, **resolved_params)


class HALItem(BaseModel):
    href: Optional[UrlType]
    method: Optional[str]
    description: Optional[str]


class HALFor(HALItem, AbstractHyperField):
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
        self._endpoint: str = endpoint.__name__ if callable(endpoint) else endpoint
        self._param_values: Dict[str, str] = param_values or {}
        self._description = description
        self._condition = condition
        super().__init__()

    def __build_hypermedia__(
        self, routes: Dict[str, Route], values: Dict[str, Any]
    ) -> Optional[HALItem]:
        if self._condition is not None and not self._condition(values):
            return None

        resolved_params = resolve_param_values(self._param_values, values)

        route = routes.get(self._endpoint, None)
        if route is None:
            raise ValueError(f"No route found for endpoint {self._endpoint}")

        return HALItem(
            href=route.url_path_for(self._endpoint, **resolved_params),
            method=next(iter(route.methods), None) if route.methods else None,
            description=self._description,
        )


_LinkSetType = Dict[str, AbstractHyperField]


class LinkSet(_LinkSetType, AbstractHyperField):  # pylint: disable=too-many-ancestors
    @classmethod
    def __get_validators__(cls):
        yield dict_validator

    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        field_schema.update({"additionalProperties": _uri_schema})

    def __build_hypermedia__(
        self, routes: Dict[str, Route], values: Dict[str, Any]
    ) -> Dict[str, str]:
        links = {k: u.__build_hypermedia__(routes, values) for k, u in self.items()}  # type: ignore  # pylint: disable=no-member
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
    _hypermodel_bound_routes: Optional[Dict[str, Route]] = None

    @root_validator
    def _hypermodel_gen_href(cls, values):  # pylint: disable=no-self-argument
        if (
            cls._hypermodel_bound_routes is None
            and getattr(cls, "__hypermodel_bound_app", None) is not None
        ):
            app = getattr(cls, "__hypermodel_bound_app")
            cls._hypermodel_bound_routes = dict(cls.get_all_routes(app.routes))
        for key, value in values.items():
            if isinstance(value, AbstractHyperField):
                values[key] = value.__build_hypermedia__(
                    cls._hypermodel_bound_routes, values
                )
        return values

    @classmethod
    def init_app(cls, app: FastAPI):
        """
        Bind a FastAPI app to other HyperModel base class.
        This allows HyperModel to convert endpoint function names into
        working URLs relative to the application root.

        Args:
            app (FastAPI): Application to generate URLs from
        """
        setattr(cls, "__hypermodel_bound_app", app)

    @staticmethod
    def get_all_routes(app_routes: List[BaseRoute]) -> Iterable[Tuple[str, Route]]:
        """
        Helper to retrieve all routes from app.routes.

        Args:
            app_routes (List[BaseRoute]): List of routes from a FastAPI app.
        """
        for route in app_routes:
            if isinstance(route, (Host, Mount)):
                # Host and Mount have a `routes` property, so we have
                # to iterate on each one of them recursively.
                yield from HyperModel.get_all_routes(route.routes)
            elif isinstance(route, Route):
                yield route.name, route
