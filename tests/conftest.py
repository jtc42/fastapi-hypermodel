from typing import Any
from fastapi import FastAPI
import pytest

from fastapi_hypermodel import (
    HyperModel,
)

from fastapi_hypermodel import URL_TYPE_SCHEMA


app_ = FastAPI()


@app_.get("/mock_read/{id_}")
def mock_read_with_path():
    pass


@pytest.fixture()
def app() -> FastAPI:
    HyperModel.init_app(app_)
    return app_


@pytest.fixture()
def unregistered_app() -> FastAPI:
    return FastAPI()


@pytest.fixture()
def url_type_schema() -> Any:
    return URL_TYPE_SCHEMA
