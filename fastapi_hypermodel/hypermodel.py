"""
Some functionality is based heavily on Flask-Marshmallow:
https://github.com/marshmallow-code/flask-marshmallow/blob/dev/src/flask_marshmallow/fields.py
"""

import re
import urllib
from typing import Any, Dict, List, Optional, no_type_check

from fastapi import FastAPI
from pydantic import BaseModel, root_validator
from pydantic.utils import update_not_none
from pydantic.validators import dict_validator
from starlette.datastructures import URLPath

_tpl_pattern = re.compile(r"\s*<\s*(\S*)\s*>\s*")


class InvalidAttribute(AttributeError):
    pass


class UrlFor(str):
    min_length = 1
    max_length = 2 ** 16

    def __init__(self, endpoint: str, param_values: Optional[Dict[str, str]] = None):
        self.endpoint: str = endpoint
        self.param_values: Dict[str, str] = param_values or {}
        super().__init__()

    @no_type_check
    def __new__(cls, *_):
        return str.__new__(cls)

    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        update_not_none(
            field_schema,
            minLength=cls.min_length,
            maxLength=cls.max_length,
            format="uri",
        )

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


_LinkSetType = Dict[str, UrlFor]


class LinkSet(_LinkSetType):  # pylint: disable=too-many-ancestors
    @classmethod
    def __get_validators__(cls):
        yield dict_validator

    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        field_schema.update(
            {"additionalProperties": {"type": "string", "format": "uri"}}
        )


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


def _clean_attribute_value(value: Any):
    if isinstance(value, str):
        return urllib.parse.quote(value)
    return value


def _resolve_param_values(param_values_template, data_object):
    param_values = {}
    for name, attr_tpl in param_values_template.items():
        attr_name = _tpl(str(attr_tpl))
        if attr_name:
            attribute_value = _get_value(data_object, attr_name, default=None)
            if attribute_value is None:
                raise InvalidAttribute(
                    "{attr_name!r} is not a valid "
                    "attribute of {obj!r}".format(attr_name=attr_name, obj=data_object)
                )
            param_values[name] = _clean_attribute_value(attribute_value)
    return param_values


class HyperModel(BaseModel):
    _hypermodel_bound_app: Optional[FastAPI] = None

    @classmethod
    def _generate_url(cls, endpoint, param_values, values):
        if cls._hypermodel_bound_app:
            return cls._hypermodel_bound_app.url_path_for(
                endpoint, **_resolve_param_values(param_values, values)
            )
        return None

    @root_validator
    def _hypermodel_gen_href(cls, values):  # pylint: disable=no-self-argument
        for key, value in values.items():
            if isinstance(value, UrlFor):
                values[key] = cls._generate_url(
                    value.endpoint, value.param_values, values
                )
            elif isinstance(value, LinkSet):
                values[key] = {
                    k: cls._generate_url(u.endpoint, u.param_values, values)
                    for k, u in value.items()
                }
        return values

    @classmethod
    def init_app(cls, app: FastAPI):
        """
        Bind a FastAPI app to othe HyperModel base class.
        This allows HyperModel to convert endpoint function names into
        working URLs relative to the application root.

        Args:
            app (FastAPI): Application to generate URLs from
        """
        cls._hypermodel_bound_app = app
