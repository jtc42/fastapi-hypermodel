from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional

import pytest
from fastapi import FastAPI

from fastapi_hypermodel import (
    HyperModel,
    InvalidAttribute,
    extract_value_by_name,
    get_hal_link_href,
    get_route_from_app,
    resolve_param_values,
)


@dataclass
class MockClass:
    name: Optional[str]


@dataclass
class MockContainer:
    mock: MockClass


@pytest.fixture()
def hal_response() -> Any:
    return {"_links": {"self": {"href": "/self"}}}


@pytest.fixture()
def params() -> Dict[str, str]:
    return {"name": "Bob", "id_": "person02"}


@pytest.fixture()
def sample_object() -> Dict[str, str]:
    return {"name": "Bob"}


def test_resolve_param_values_flat(params: Mapping[str, str]) -> None:
    actual = resolve_param_values({"id_": "<id_>"}, params)
    expected = {"id_": "person02"}
    assert actual == expected


@pytest.mark.parametrize(
    "template", ["<id_>", " <id_>", "<id_> ", "< id_>", "<id_  >", "< id_ >"]
)
def test_resolve_param_values_different_templates(
    template: str, params: Mapping[str, str]
) -> None:
    actual = resolve_param_values({"id_": template}, params)
    expected = {"id_": "person02"}
    assert actual == expected


def test_resolve_param_values_url_escape() -> None:
    actual = resolve_param_values(
        {"id_": "<id_>"}, {"name": "Bob", "id_": 'person"02"'}
    )
    expected = {"id_": "person%2202%22"}
    assert actual == expected


def test_resolve_param_values_empty_attribute(params: Mapping[str, str]) -> None:
    actual = resolve_param_values({"id_": "<>"}, params)
    expected = {}
    assert actual == expected


def test_resolve_param_values_nested_objects() -> None:
    sample_object = MockContainer(MockClass("test"))
    actual = resolve_param_values({"id_": "<mock.name>"}, sample_object)
    expected = {"id_": "test"}
    assert actual == expected


def test_resolve_param_values_empty_params(params: Mapping[str, str]) -> None:
    actual = resolve_param_values({}, params)
    expected = {}
    assert actual == expected


def test_extract_value_by_name(sample_object: Mapping[str, str]) -> None:
    value = extract_value_by_name(sample_object, "name")
    assert value == "Bob"


def test_extract_value_by_name_missing_with_default() -> None:
    value = extract_value_by_name({}, "name", default="Bob")
    assert value == "Bob"


def test_extract_value_by_name_with_object() -> None:
    mock_object = MockClass(name="Bob")
    value = extract_value_by_name(mock_object, "name")
    assert value == "Bob"


def test_extract_value_by_name_missing(sample_object: Mapping[str, str]) -> None:
    with pytest.raises(InvalidAttribute, match="is not a valid attribute of"):
        extract_value_by_name(sample_object, "id_")


def test_extract_value_by_name_invalid() -> None:
    with pytest.raises(InvalidAttribute, match="is not a valid attribute of"):
        extract_value_by_name({"name": "Bob", "id_": None}, "id_")


def test_get_hal_link_href(hal_response: Any) -> None:
    actual = get_hal_link_href(hal_response, "self")
    expected = "/self"

    assert actual == expected


def test_get_hal_link_href_not_found(hal_response: Any) -> None:
    actual = get_hal_link_href(hal_response, "update")
    expected = ""

    assert actual == expected


class MockModel(HyperModel):
    id_: str


def test_parse_uri() -> None:
    sample_uri = "/items/{id_}"
    mock_model = MockModel(id_="123")
    actual = mock_model.parse_uri(sample_uri)
    expected = f"/items/{mock_model.id_}"

    assert actual == expected


def test_get_route_from_app(app: FastAPI) -> Any:
    route = get_route_from_app(app, "mock_read_with_path")

    assert route.path == "/mock_read/{id_}"


def test_get_route_from_app_non_existing(app: FastAPI) -> Any:
    with pytest.raises(ValueError, match="No route found for endpoint "):
        get_route_from_app(app, "mock_read")
