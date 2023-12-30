from typing import Any
from fastapi.testclient import TestClient
from examples.url_for import Person

import pytest

import uuid


@pytest.fixture()
def people_uri() -> str:
    return "/people"


@pytest.fixture()
def find_uri_template(url_for_client: TestClient, people_uri: str) -> str:
    find_uri = url_for_client.get(people_uri).json().get("find")
    assert find_uri
    return find_uri


@pytest.fixture()
def update_uri_template(url_for_client: TestClient, people_uri: str) -> str:
    update_uri = url_for_client.get(people_uri).json().get("update")
    assert update_uri
    return update_uri


def test_get_people(url_for_client: TestClient, people_uri: str) -> None:
    response = url_for_client.get(people_uri).json()

    self_uri = response.get("href")
    assert self_uri == people_uri

    find_uri = response.get("find")
    assert find_uri

    update_uri = response.get("update")
    assert update_uri


def test_get_person(
    url_for_client: TestClient,
    find_uri_template: str,
    locked_person: Person,
    people_uri: str,
) -> None:
    find_uri = locked_person.parse_uri(find_uri_template)
    person_response = url_for_client.get(find_uri).json()

    person_href = person_response.get("href")

    assert people_uri in person_href and locked_person.id_ in person_href
    assert person_response.get("id_") == locked_person.id_

    items = person_response.get("items")
    assert items


def test_update_person_from_uri_template(
    url_for_client: TestClient,
    find_uri_template: str,
    update_uri_template: str,
    locked_person: Person,
) -> None:
    find_uri = locked_person.parse_uri(find_uri_template)
    before = url_for_client.get(find_uri).json()

    new_data = {"name": f"updated_{uuid.uuid4().hex}"}
    update_uri = locked_person.parse_uri(update_uri_template)
    response = url_for_client.put(update_uri, json=new_data).json()

    assert response.get("name") == new_data.get("name")
    assert response.get("name") != before.get("name")

    before_uri = before.get("href")
    after_uri = response.get("href")

    assert before_uri == after_uri


def test_update_person_from_update_uri(
    url_for_client: TestClient, find_uri_template: str, locked_person: Person
) -> None:
    find_uri = locked_person.parse_uri(find_uri_template)
    before = url_for_client.get(find_uri).json()

    new_data = {"name": f"updated_{uuid.uuid4().hex}"}

    update_uri = before.get("update")
    response = url_for_client.put(update_uri, json=new_data).json()

    assert response.get("name") == new_data.get("name")
    assert response.get("name") != before.get("name")

    before_uri = before.get("href")
    after_uri = response.get("href")

    assert before_uri == after_uri


def test_get_person_items(
    url_for_client: TestClient, find_uri_template: str, locked_person: Person
) -> None:
    find_uri = locked_person.parse_uri(find_uri_template)
    person_response = url_for_client.get(find_uri).json()

    person_items = person_response.get("items")

    assert isinstance(person_items, list) and person_items

    first_item, *_ = person_items
    first_item_uri = first_item.get("href")
    first_item_response = url_for_client.get(first_item_uri).json()

    assert first_item.get("id_") == first_item_response.get("id_")
    assert first_item.get("name") == first_item_response.get("name")


@pytest.fixture()
def existing_item() -> Any:
    return {"id_": "item04"}


@pytest.fixture()
def non_existing_item() -> Any:
    return {"id_": "item05"}


def test_add_item_to_unlocked_person(
    url_for_client: TestClient,
    find_uri_template: str,
    unlocked_person: Person,
    existing_item: Any,
) -> None:
    find_uri = unlocked_person.parse_uri(find_uri_template)
    before = url_for_client.get(find_uri).json()
    before_items = before.get("items", [])
    add_item_uri = before.get("add_item")

    assert add_item_uri

    after_items = url_for_client.put(add_item_uri, json=existing_item).json()
    assert after_items

    lenght_before = len(before_items)
    lenght_after = len(after_items)
    assert lenght_before + 1 == lenght_after

    assert after_items[-1].get("id_") == existing_item.get("id_")


def test_add_item_to_unlocked_person_nonexisting_item(
    url_for_client: TestClient,
    find_uri_template: str,
    unlocked_person: Person,
    non_existing_item: Any,
) -> None:
    find_uri = unlocked_person.parse_uri(find_uri_template)
    before = url_for_client.get(find_uri).json()
    add_item_uri = before.get("add_item")

    assert add_item_uri

    after_items = url_for_client.put(add_item_uri, json=non_existing_item).json()
    assert not after_items


def test_add_item_to_locked_person(
    url_for_client: TestClient,
    find_uri_template: str,
    locked_person: Person,
) -> None:
    find_uri = locked_person.parse_uri(find_uri_template)
    before = url_for_client.get(find_uri).json()
    add_item_uri = before.get("add_item")

    assert not add_item_uri
