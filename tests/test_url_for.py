from typing import Any, Mapping

import pytest
from fastapi import FastAPI

from fastapi_hypermodel import (
    HyperModel,
    UrlFor,
)


@pytest.mark.parametrize(
    "endpoint",
    [
        pytest.param("mock_read_with_path", id="Use of a string endpoint"),
    ],
)
def test_build_hypermedia_with_endpoint(app: FastAPI, endpoint: str) -> None:
    sample_id = "test"
    url_for = UrlFor(endpoint, {"id_": "<id_>"})
    uri = url_for(app, {"id_": sample_id})
    assert uri
    assert uri.hypermedia == f"/mock_read/{sample_id}"


def test_build_hypermedia_no_app() -> None:
    url_for = UrlFor("mock_read_with_path", {"id_": "<id_>"})
    uri = url_for(None, {})
    assert uri is None


def test_build_hypermedia_passing_condition(app: FastAPI) -> None:
    sample_id = "test"
    locked = True
    url_for = UrlFor(
        "mock_read_with_path",
        {"id_": "<id_>"},
        condition=lambda values: values["locked"],
    )
    uri = url_for(app, {"id_": sample_id, "locked": locked})
    assert uri
    assert uri.hypermedia == f"/mock_read/{sample_id}"


def test_build_hypermedia_not_passing_condition(app: FastAPI) -> None:
    sample_id = "test"
    locked = False
    url_for = UrlFor(
        "mock_read_with_path",
        {"id_": "<id_>"},
        condition=lambda values: values["locked"],
    )
    uri = url_for(app, {"id_": sample_id, "locked": locked})
    assert uri is None


def test_build_hypermedia_template(app: FastAPI) -> None:
    url_for = UrlFor(
        "mock_read_with_path",
        templated=True,
    )
    uri = url_for(app, {})
    assert uri
    assert uri.hypermedia == "/mock_read/{id_}"


def test_json_serialization(app: FastAPI) -> None:
    url_for = UrlFor(
        "mock_read_with_path",
        templated=True,
    )
    rendered_url = url_for(app, {})
    assert rendered_url

    uri = rendered_url.model_dump()
    assert uri == "/mock_read/{id_}"


def test_json_serialization_no_build() -> None:
    url_for = UrlFor(
        "mock_read_with_path",
        templated=True,
    )

    uri = url_for.model_dump()
    assert uri == ""


class MockClass(HyperModel):
    id_: str

    href: UrlFor = UrlFor("mock_read_with_path", {"id_": "<id_>"})


def test_openapi_schema(url_type_schema: Mapping[str, Any]) -> None:
    mock = MockClass(id_="test")
    schema = mock.model_json_schema()
    url_for_schema = schema["$defs"]["UrlFor"]

    assert all(url_for_schema.get(k) == v for k, v in url_type_schema.items())
