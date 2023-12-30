from typing import Any
import pytest
from fastapi.testclient import TestClient

from examples.url_for import (
    ItemSummary,
    Person,
    app,
    items as items_,
    people as people_,
)
from fastapi_hypermodel import HyperModel


@pytest.fixture()
def url_for_client() -> TestClient:
    HyperModel.init_app(app)

    return TestClient(app=app, base_url="http://urlfortestserver")


@pytest.fixture()
def items() -> Any:
    return items_.values()


@pytest.fixture(params=list(items_.values()))
def item(request: Any) -> ItemSummary:
    return ItemSummary(**request.param)


@pytest.fixture()
def people() -> Any:
    return people_.values()


@pytest.fixture(params=list(people_.values()))
def locked_person(request: Any) -> Person:
    return Person(**request.param)


@pytest.fixture(
    params=[person for person in people_.values() if person.get("is_locked")]
)
def locked_person(request: Any) -> Person:
    return Person(**request.param)


@pytest.fixture(
    params=[person for person in people_.values() if not person.get("is_locked")]
)
def unlocked_person(request: Any) -> Person:
    return Person(**request.param)
