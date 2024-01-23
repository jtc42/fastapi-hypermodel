from typing import Any

import pytest
from fastapi.testclient import TestClient

from examples.siren import (
    ItemSummary,
    Person,
    app,
)
from examples.siren import items as items_
from examples.siren import people as people_
from fastapi_hypermodel import SirenHyperModel


@pytest.fixture()
def siren_client() -> TestClient:
    SirenHyperModel.init_app(app)

    return TestClient(app=app, base_url="http://sirentestserver")


@pytest.fixture()
def items() -> Any:
    return items_["items"]


@pytest.fixture(params=items_["items"])
def item(request: Any) -> ItemSummary:
    return ItemSummary(**request.param)


@pytest.fixture()
def people() -> Any:
    return people_["people"]


@pytest.fixture(params=list(people_["people"]))
def person(request: Any) -> Person:
    return Person(**request.param)


@pytest.fixture(params=[person for person in people_["people"] if person["is_locked"]])
def locked_person(request: Any) -> Person:
    return Person(**request.param)


@pytest.fixture(
    params=[person for person in people_["people"] if not person["is_locked"]]
)
def unlocked_person(request: Any) -> Person:
    return Person(**request.param)
