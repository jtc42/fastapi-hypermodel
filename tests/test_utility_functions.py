from dataclasses import dataclass
from typing import Any
import pytest

from fastapi_hypermodel import (
    HyperModel,
    resolve_param_values,
    extract_value_by_name,
    get_hal_link_href,
    InvalidAttribute,
)


@dataclass
class MockClass:
    name: str


@pytest.fixture()
def hal_response() -> Any:
    return {"_links": {"self": {"href": "/self"}}}


def test_resolve_param_values_flat() -> None:
    actual = resolve_param_values({"id_": "<id_>"}, {"name": "Bob", "id_": "person02"})
    expected = {"id_": "person02"}
    assert actual == expected


@pytest.mark.parametrize(
    "template", ["<id_>", " <id_>", "<id_> ", "< id_>", "<id_  >", "< id_ >"]
)
def test_resolve_param_values_different_templates(template: str):
    actual = resolve_param_values({"id_": template}, {"name": "Bob", "id_": "person02"})
    expected = {"id_": "person02"}
    assert actual == expected


def test_resolve_param_values_url_escape() -> None:
    actual = resolve_param_values(
        {"id_": "<id_>"}, {"name": "Bob", "id_": 'person"02"'}
    )
    expected = {"id_": "person%2202%22"}
    assert actual == expected


def test_extract_value_by_name() -> None:
    value = extract_value_by_name({"name": "Bob"}, "name")
    assert value == "Bob"


def test_extract_value_by_name_missing_with_default() -> None:
    value = extract_value_by_name({}, "name", default="Bob")
    assert value == "Bob"


def test_extract_value_by_name_with_object() -> None:
    mock_object = MockClass(name="Bob")
    value = extract_value_by_name(mock_object, "name")
    assert value == "Bob"


def test_extract_value_by_name_missing() -> None:
    with pytest.raises(InvalidAttribute, match="is not a valid attribute of"):
        extract_value_by_name({"name": "Bob"}, "id_")


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
