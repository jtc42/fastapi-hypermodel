from typing import Any, Dict
from fastapi import FastAPI
import pytest

from fastapi_hypermodel import (
    HyperModel,
    HALFor,
)

app_ = FastAPI()


@app_.get("/mock_read/{id_}")
def mock_read_with_path():
    pass


@pytest.fixture()
def app() -> FastAPI:
    HyperModel.init_app(app_)
    return app_


@pytest.fixture()
def href_schema() -> Any:
    return {"type": "string", "format": "uri", "minLength": 1, "maxLength": 2**16}


class MockClass(HyperModel):
    id_: str

    href: HALFor = HALFor("mock_read_with_path", {"id_": "<id_>"})


def test_hal_for(app: FastAPI):
    mock = MockClass(id_="test")

    hal_for = HALFor("mock_read_with_path", {"id_": "<id_>"})
    hal_for.__build_hypermedia__(app, vars(mock))


def test_hal_for_no_app():
    mock = MockClass(id_="test")

    hal_for = HALFor("mock_read_with_path", {"id_": "<id_>"})
    hypermedia = hal_for.__build_hypermedia__(None, vars(mock))

    assert hypermedia.href is None


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
    assert uri.href is None


@pytest.mark.usefixtures("app")
def test_openapi_schema(href_schema: Dict[str, Any]) -> None:
    mock = MockClass(id_="test")
    schema = mock.model_json_schema()
    hal_for_schema = schema["$defs"]["HALFor"]["properties"]["href"]["anyOf"][0]

    assert all(hal_for_schema.get(k) == v for k, v in href_schema.items())
