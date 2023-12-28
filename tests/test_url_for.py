from typing import Any, Dict
from fastapi import FastAPI
import pytest

from fastapi_hypermodel import (
    HyperModel,
    UrlFor,
)

test_app = FastAPI()


@test_app.get("/mock_read/{id_}")
def mock_read_with_path():
    pass


@pytest.fixture()
def app() -> FastAPI:
    HyperModel.init_app(test_app)
    return test_app


@pytest.fixture()
def uri_schema() -> Any:
    return {"type": "string", "format": "uri", "minLength": 1, "maxLength": 2**16}


@pytest.mark.parametrize(
    "endpoint",
    [
        pytest.param("mock_read_with_path", id="Use of a string endpoint"),
        pytest.param(mock_read_with_path, id="Use of a Callable endpoint"),
    ],
)
def test_build_hypermedia_with_endpoint(app: FastAPI, endpoint: str) -> None:
    sample_id = "test"
    url_for = UrlFor(endpoint, {"id_": "<id_>"})
    uri = url_for.__build_hypermedia__(app, {"id_": sample_id})
    assert uri.hypermedia == f"/mock_read/{sample_id}"


def test_build_hypermedia_no_app():
    url_for = UrlFor("mock_read_with_path", {"id_": "<id_>"})
    uri = url_for.__build_hypermedia__(None, {})
    assert uri.hypermedia is None


def test_build_hypermedia_passing_condition(app: FastAPI):
    sample_id = "test"
    locked = True
    url_for = UrlFor(
        "mock_read_with_path",
        {"id_": "<id_>"},
        condition=lambda values: values["locked"],
    )
    uri = url_for.__build_hypermedia__(app, {"id_": sample_id, "locked": locked})
    assert uri.hypermedia == f"/mock_read/{sample_id}"


def test_build_hypermedia_not_passing_condition(app: FastAPI):
    sample_id = "test"
    locked = False
    url_for = UrlFor(
        "mock_read_with_path",
        {"id_": "<id_>"},
        condition=lambda values: values["locked"],
    )
    uri = url_for.__build_hypermedia__(app, {"id_": sample_id, "locked": locked})
    assert uri.hypermedia is None


def test_build_hypermedia_template(app: FastAPI):
    url_for = UrlFor(
        "mock_read_with_path",
        template=True,
    )
    uri = url_for.__build_hypermedia__(app, {})
    assert uri.hypermedia == "/mock_read/{id_}"


def test_json_serialization(app: FastAPI):
    url_for = UrlFor(
        "mock_read_with_path",
        template=True,
    )
    rendered_url = url_for.__build_hypermedia__(app, {})
    assert rendered_url

    uri = rendered_url.model_dump()
    assert uri == "/mock_read/{id_}"


def test_json_serialization_no_build(app: FastAPI):
    url_for = UrlFor(
        "mock_read_with_path",
        template=True,
    )

    uri = url_for.model_dump()
    assert uri == ""


class MockClass(HyperModel):
    id_: str

    href: UrlFor = UrlFor("mock_read_with_path", {"id_": "<id_>"})


def test_openapi_schema(uri_schema: Dict[str, Any]) -> None:
    mock = MockClass(id_="test")
    schema = mock.model_json_schema()
    url_for_schema = schema["$defs"]["UrlFor"]["properties"]["hypermedia"]["anyOf"][0]

    assert all(url_for_schema.get(k) == v for k, v in uri_schema.items())