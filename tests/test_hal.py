from typing import Any, Dict
import uuid
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from fastapi_hypermodel import HyperModel, HALFor, HALResponse, HALForType, UrlType

from pydantic import ValidationError

from pytest_lazy_fixtures import lf


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


@pytest.fixture
def invalid_links_empty() -> Any:
    return {"_links": {}}


@pytest.fixture
def invalid_links() -> Any:
    return {"_links": {"test_link": {"name": "test_name"}}}


@pytest.fixture
def invalid_links_list() -> Any:
    return {"_links": {"test_link": [{"name": "test_name"}]}}


@pytest.fixture()
def invalid_embedded_links(invalid_links: Any) -> Any:
    return {"_embedded": {"test": invalid_links}}


@pytest.fixture()
def invalid_embedded_links_list(invalid_links_list: Any) -> Any:
    return {"_embedded": {"test": invalid_links_list}}


@pytest.fixture()
def invalid_embedded_links_empty(invalid_links_empty: Any) -> Any:
    return {"_embedded": {"test": invalid_links_empty}}


@pytest.fixture
def invalid_embedded_empty() -> Any:
    return {"_embedded": {}}


def test_hal_response_empty(app: FastAPI):
    @app.get("/test_response", response_class=HALResponse)
    def _():
        pass

    test_client = TestClient(app)

    response = test_client.get("/test_response")

    content_type = response.headers.get("content-type")
    assert content_type == "application/hal+json"


def test_hal_response_single_link(app: FastAPI):
    @app.get("/test_response_single_link", response_class=HALResponse)
    def _():  # pragma: no cover
        return {"_links": {"self": HALForType(href=UrlType("test"))}}

    test_client = TestClient(app)

    response = test_client.get("/test_response_single_link")

    content_type = response.headers.get("content-type")
    assert content_type == "application/hal+json"


def test_hal_response_link_list(app: FastAPI):
    @app.get("/test_response_link_list", response_class=HALResponse)
    def _():  # pragma: no cover
        return {"_links": {"self": [HALForType(href=UrlType("test"))]}}

    test_client = TestClient(app)

    response = test_client.get("/test_response_link_list")

    content_type = response.headers.get("content-type")
    assert content_type == "application/hal+json"


def test_hal_response_embedded(app: FastAPI):
    @app.get("/test_response_single_link_list", response_class=HALResponse)
    def _():  # pragma: no cover
        return {"_embedded": {"self": [HALForType(href=UrlType())]}}

    test_client = TestClient(app)

    response = test_client.get("/test_response_single_link_list")

    content_type = response.headers.get("content-type")
    assert content_type == "application/hal+json"


@pytest.mark.parametrize(
    "invalid_response",
    [
        lf("invalid_links_empty"),
        lf("invalid_links"),
        lf("invalid_links_list"),
        lf("invalid_embedded_links"),
        lf("invalid_embedded_links_list"),
        lf("invalid_embedded_links_empty"),
        lf("invalid_embedded_empty"),
    ],
)
def test_hal_response_invalid(app: FastAPI, invalid_response: Any):
    suffix = uuid.uuid4().hex
    endpoint = f"/test_response_invalid_{suffix}"

    @app.get(endpoint, response_class=HALResponse)
    def _():
        return invalid_response

    test_client = TestClient(app)

    with pytest.raises((ValidationError, ValueError)):
        test_client.get(endpoint)


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
