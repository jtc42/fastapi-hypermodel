from typing import Any

import pytest
from fastapi.testclient import TestClient

from examples.url_for import (
    ItemSummary,
    Person,
    app,
)
from examples.url_for import (
    items as items_,
)
from examples.url_for import (
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


@pytest.fixture(params=items_["items"])
def item(request: Any) -> ItemSummary:
    return ItemSummary(**request.param)


@pytest.fixture()
def people() -> Any:
    return people_.values()


@pytest.fixture(
    params=[person for person in people_["people"] if person.get("is_locked")]
)
def locked_person(request: Any) -> Person:
    return Person(**request.param)


@pytest.fixture(
    params=[person for person in people_["people"] if not person.get("is_locked")]
)
def unlocked_person(request: Any) -> Person:
    return Person(**request.param)
