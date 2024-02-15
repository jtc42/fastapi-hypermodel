import re
import urllib
from typing import (
    Any,
    Dict,
    Mapping,
    Optional,
    Sequence,
    Union,
)

from starlette.applications import Starlette
from starlette.routing import Route


class InvalidAttribute(AttributeError):
    pass


_tpl_pattern = re.compile(r"\s*<\s*(\S*)\s*>\s*")


def _parse_template(val: str) -> Optional[str]:
    """Return value within ``< >`` if possible, else return ``None``."""
    match = _tpl_pattern.match(val)
    return match.groups()[0] if match else None


def _get_value(obj: Any, key: str, default: Optional[Any] = None) -> Any:
    """Slightly-modified version of marshmallow.utils.get_value.
    If a dot-delimited ``key`` is passed and any attribute in the
    path is `None`, return `None`.
    """
    separator = "."
    if separator in key:
        return _get_value_for_keys(obj, key.split("."), default)
    return _get_value_for_key(obj, key, default)


def _get_value_for_keys(obj: Any, keys: Sequence[str], default: Any) -> Any:
    first, *rest = keys
    value = _get_value_for_key(obj, first, default)

    if not rest:
        return value

    return _get_value_for_keys(value, rest, default)


def _get_value_for_key(obj: Any, key: str, default: Any) -> Any:
    if hasattr(obj, "__getitem__"):
        return obj.get(key, default)

    return getattr(obj, key, default)


def _clean_attribute_value(value: Any) -> Union[str, Any]:
    return urllib.parse.quote(value) if isinstance(value, str) else value


def resolve_param_values(
    param_values_template: Optional[Mapping[str, Any]],
    data_object: Any,
) -> Dict[str, Any]:
    """
    Converts a dictionary of URL parameter substitution templates and a
    dictionary of real data values into a dictionary of recursively-populated
    URL parameter values.

    E.g. when passed the template {'person_id': '<id>'} and the data {'name':
    'Bob', 'id': 'person02'}, the function will return {'person_id': 'person02'}

    Args:
        param_values_template (Dict[str, str]): Dictionary of URL parameter
            substitution templates data_object (Dict[str, Any]): Dictionary
            containing name-to-value mapping of all fields

    Returns:
        Dict[str, str]: Populated dictionary of URL parameters
    """
    if not param_values_template:
        return {}

    param_values: Dict[str, Any] = {}
    for name, attribute_template in param_values_template.items():
        attribute = _parse_template(str(attribute_template))
        if not attribute:
            continue

        value = extract_value_by_name(data_object, attribute)
        param_values[name] = value

    return param_values


def extract_value_by_name(
    data_object: Any, attribute: str, default: Optional[Any] = None
) -> Union[str, Any]:
    if not isinstance(data_object, Mapping):
        data_object = vars(data_object)

    attribute_value = _get_value(data_object, attribute, default)

    if not attribute_value:
        error_message = f"{attribute} is not a valid attribute of {data_object}"
        raise InvalidAttribute(error_message)

    return _clean_attribute_value(attribute_value)


def get_route_from_app(app: Starlette, endpoint_function: str) -> Route:
    for route in app.routes:
        if isinstance(route, Route) and route.name == endpoint_function:
            break
    else:
        error_message = f"No route found for endpoint {endpoint_function}"
        raise ValueError(error_message)

    return route
