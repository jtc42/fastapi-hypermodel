"""
Some functionality is based heavily on Flask-Marshmallow:
https://github.com/marshmallow-code/flask-marshmallow/blob/dev/src/flask_marshmallow/fields.py
"""

import re
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from pydantic import AnyUrl, BaseModel, root_validator

# Type alias, for convenience
HyperRef = Optional[AnyUrl]

_tpl_pattern = re.compile(r"\s*<\s*(\S*)\s*>\s*")


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


class HyperModel(BaseModel):
    _hypermodel_bound_app: Optional[FastAPI] = None

    @root_validator
    def _hypermodel_gen_href(cls, values):  # pylint: disable=no-self-argument
        if hasattr(cls, "Href") and cls.Href and cls._hypermodel_bound_app:
            # Pull out hypermodel config from Href class
            field: str = getattr(cls.Href, "field", "href")
            # Don't bother building URL if it's not included in the model
            if field in cls.__fields__:
                path_params: Dict[str, str] = getattr(cls.Href, "values", {})
                endpoint: str = getattr(cls.Href, "endpoint", None)
                # Make sure we have an endpoint
                if not endpoint:
                    raise AttributeError(
                        "`endpoint` attribute must be specified in Href class"
                    )

                # Resolve param values
                param_values = {}
                for name, attr_tpl in path_params.items():
                    attr_name = _tpl(str(attr_tpl))
                    if attr_name:
                        attribute_value = _get_value(values, attr_name, default=None)
                        if attribute_value is None:
                            raise AttributeError(
                                "{attr_name!r} is not a valid "
                                "attribute of {obj!r}".format(
                                    attr_name=attr_name, obj=values
                                )
                            )
                        param_values[name] = attribute_value

                # Dump href field into output
                values[field] = cls._hypermodel_bound_app.url_path_for(
                    endpoint, **param_values
                )

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

    class Href:
        pass
