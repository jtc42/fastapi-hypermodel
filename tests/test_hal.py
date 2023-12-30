from typing import Any, Dict
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from fastapi_hypermodel import HyperModel, HALFor, HALResponse


class MockClass(HyperModel):
    id_: str

    href: HALFor = HALFor("mock_read_with_path", {"id_": "<id_>"})


@pytest.fixture()
def hal_for_properties() -> Any:
    return {
        "href": {
            "default": "",
            "format": "uri",
            "maxLength": 65536,
            "minLength": 1,
            "title": "Href",
            "type": "string",
        },
        "templated": {
            "anyOf": [{"type": "boolean"}, {"type": "null"}],
            "default": None,
            "title": "Templated",
        },
        "method": {
            "anyOf": [{"type": "string"}, {"type": "null"}],
            "default": None,
            "title": "Method",
        },
        "description": {
            "anyOf": [{"type": "string"}, {"type": "null"}],
            "default": None,
            "title": "Description",
        },
        "title": {
            "anyOf": [{"type": "string"}, {"type": "null"}],
            "default": None,
            "title": "Title",
        },
        "name": {
            "anyOf": [{"type": "string"}, {"type": "null"}],
            "default": None,
            "title": "Name",
        },
        "type": {
            "anyOf": [{"type": "string"}, {"type": "null"}],
            "default": None,
            "title": "Type",
        },
        "hreflang": {
            "anyOf": [{"type": "string"}, {"type": "null"}],
            "default": None,
            "title": "Hreflang",
        },
        "profile": {
            "anyOf": [{"type": "string"}, {"type": "null"}],
            "default": None,
            "title": "Profile",
        },
        "deprecation": {
            "anyOf": [{"type": "string"}, {"type": "null"}],
            "default": None,
            "title": "Deprecation",
        },
    }


@pytest.fixture()
def hal_for_schema(hal_for_properties: Dict[str, Any]) -> Any:
    return {"type": "object", "properties": hal_for_properties, "title": "HALFor"}


def test_hal_response(app: FastAPI):
    @app.get("/test_response", response_class=HALResponse)
    def _():
        pass

    test_client = TestClient(app)

    response = test_client.get("/test_response")

    content_type = response.headers.get("content-type")
    assert content_type == "application/hal+json"


def test_hal_for(app: FastAPI):
    mock = MockClass(id_="test")

    hal_for = HALFor("mock_read_with_path", {"id_": "<id_>"})
    hal_for.__build_hypermedia__(app, vars(mock))


def test_hal_for_no_app():
    mock = MockClass(id_="test")

    hal_for = HALFor("mock_read_with_path", {"id_": "<id_>"})
    hypermedia = hal_for.__build_hypermedia__(None, vars(mock))

    assert hypermedia.href == ""


def test_build_hypermedia_passing_condition(app: FastAPI):
    sample_id = "test"
    hal_for = HALFor(
        "mock_read_with_path",
        {"id_": "<id_>"},
        condition=lambda values: values["locked"],
    )
    uri = hal_for.__build_hypermedia__(app, {"id_": sample_id, "locked": True})
    assert uri.href == f"/mock_read/{sample_id}"


def test_build_hypermedia_template(app: FastAPI):
    hal_for = HALFor(
        "mock_read_with_path",
        template=True,
    )
    uri = hal_for.__build_hypermedia__(app, {})
    assert uri.href == "/mock_read/{id_}"


def test_build_hypermedia_not_passing_condition(app: FastAPI):
    sample_id = "test"
    hal_for = HALFor(
        "mock_read_with_path",
        {"id_": "<id_>"},
        condition=lambda values: values["locked"],
    )
    uri = hal_for.__build_hypermedia__(app, {"id_": sample_id, "locked": False})
    assert uri.href == ""


@pytest.mark.usefixtures("app")
def test_openapi_schema(hal_for_schema: Dict[str, Any]) -> None:
    mock = MockClass(id_="test")
    schema = mock.model_json_schema()
    hal_for_definition = schema["$defs"]["HALFor"]

    assert all(hal_for_definition.get(k) == v for k, v in hal_for_schema.items())
