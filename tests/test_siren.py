from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastapi_hypermodel import (
    SirenHyperModel,
    SirenLinkFor,
    SirenLinkType,
    SirenResponse,
)

SAMPLE_ENDPOINT = "/mock_read_with_path_siren/{id_}"


class MockClass(SirenHyperModel):
    id_: str


@pytest.fixture()
def sample_endpoint_uri() -> str:
    return SAMPLE_ENDPOINT


@pytest.fixture()
def siren_app(app: FastAPI, sample_endpoint_uri: str) -> FastAPI:
    @app.get(sample_endpoint_uri, response_class=SirenResponse)
    def mock_read_with_path_siren() -> Any:  # pragma: no cover
        return {}

    SirenHyperModel.init_app(app)

    return app


@pytest.fixture()
def siren_client(siren_app: FastAPI) -> TestClient:
    return TestClient(app=siren_app)


def test_content_type(siren_client: TestClient) -> None:
    response = siren_client.get("mock_read_with_path_siren/test")

    content_type = response.headers.get("content-type")
    assert content_type == "application/siren+json"


# SirenLinkFor


def test_siren_link_for(siren_app: FastAPI) -> None:
    mock = MockClass(id_="test")

    siren_link_for = SirenLinkFor(
        "mock_read_with_path_siren", {"id_": "<id_>"}, rel=["test"]
    )
    siren_link_for_type = siren_link_for(siren_app, vars(mock))

    assert isinstance(siren_link_for_type, SirenLinkType)
    assert siren_link_for_type.href == "/mock_read_with_path_siren/test"
    assert siren_link_for_type.rel == ["test"]


def test_siren_link_for_missing_rel(siren_app: FastAPI) -> None:
    mock = MockClass(id_="test")

    siren_link_for = SirenLinkFor("mock_read_with_path_siren", {"id_": "<id_>"})

    with pytest.raises(ValueError, match="Field rel and href are mandatory"):
        siren_link_for(siren_app, vars(mock))
