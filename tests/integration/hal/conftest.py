from typing import Any
import pytest
from fastapi.testclient import TestClient

from examples.hal import ItemSummary, Person, app, items as items_, people as people_
from fastapi_hypermodel import HyperModel


@pytest.fixture()
def hal_client() -> TestClient:
    HyperModel.init_app(app)

    return TestClient(app=app, base_url="http://haltestserver")


@pytest.fixture()
def items() -> Any:
    return items_["_embedded"]["items"]


@pytest.fixture(params=items_["_embedded"]["items"])
def item(request: Any) -> ItemSummary:
    return ItemSummary(**request.param)


@pytest.fixture()
def people() -> Any:
    return people_["_embedded"]["people"]


@pytest.fixture(params=[person for person in people_["_embedded"]["people"]])
def person(request: Any) -> Person:
    return Person(**request.param)


@pytest.fixture(
    params=[person for person in people_["_embedded"]["people"] if person["is_locked"]]
)
def locked_person(request: Any) -> Person:
    return Person(**request.param)


@pytest.fixture(
    params=[
        person for person in people_["_embedded"]["people"] if not person["is_locked"]
    ]
)
def unlocked_person(request: Any) -> Person:
    return Person(**request.param)
