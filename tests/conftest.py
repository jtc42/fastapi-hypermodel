import pytest
from fastapi.testclient import TestClient
from .app import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    return TestClient(
        app=app,
    )
