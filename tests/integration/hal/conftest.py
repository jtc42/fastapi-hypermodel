from typing import Any

import pytest
from fastapi.testclient import TestClient

from examples.hal import (
    ItemSummary,
    Person,
    app,
    curies,
)
from examples.hal import (
    items as items_,
)
from examples.hal import (
    people as people_,
)
from fastapi_hypermodel import HalHyperModel


@pytest.fixture()
def hal_client() -> TestClient:
    HalHyperModel.init_app(app)
    HalHyperModel.register_curies(curies)

    return TestClient(app=app, base_url="http://haltestserver")


@pytest.fixture()
def items() -> Any:
    return items_["sc:items"]


@pytest.fixture(params=items_["sc:items"])
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
