import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def app():
    from .app import test_app

    return test_app


@pytest.fixture()
def client(app):
    return TestClient(app=app)
