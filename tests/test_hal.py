from typing import Any, Dict
from fastapi import FastAPI
import pytest

from fastapi_hypermodel import (
    HyperModel,
    HALFor,
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
def href_schema() -> Any:
    return {"type": "string", "format": "uri", "minLength": 1, "maxLength": 2**16}


class MockClass(HyperModel):
    id_: str

    href: HALFor = HALFor("mock_read_with_path", {"id_": "<id_>"})

@pytest.mark.usefixtures("app")
def test_openapi_schema(href_schema: Dict[str, Any]) -> None:
    mock = MockClass(id_="test")
    schema = mock.model_json_schema()
    url_for_schema = schema["$defs"]["HALFor"]["properties"]["href"]["anyOf"][0]

    assert all(url_for_schema.get(k) == v for k, v in href_schema.items())
