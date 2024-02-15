import uuid
from typing import Any

import pytest
from fastapi.testclient import TestClient

from examples.hal import Person
from fastapi_hypermodel import UrlType, get_hal_link


@pytest.fixture()
def people_uri() -> str:
    return "/people"


@pytest.fixture()
def find_uri_template(hal_client: TestClient, people_uri: str) -> UrlType:
    find_uri = get_hal_link(hal_client.get(people_uri).json(), "find")
    assert find_uri
    return find_uri.href


@pytest.fixture()
def update_uri_template(hal_client: TestClient, people_uri: str) -> UrlType:
    update_uri = get_hal_link(hal_client.get(people_uri).json(), "update")
    assert update_uri
    return update_uri.href


def test_people_content_type(hal_client: TestClient, people_uri: str) -> None:
    response = hal_client.get(people_uri)
    content_type = response.headers.get("content-type")
    assert content_type == "application/hal+json"


def test_get_people(hal_client: TestClient, people_uri: str) -> None:
    response = hal_client.get(people_uri).json()

    self_link = get_hal_link(response, "self")
    assert self_link
    assert self_link.href == people_uri

    find_uri = response.get("_links", {}).get("find", {})
    assert find_uri.get("templated")
    assert people_uri in find_uri.get("href")


def test_get_person(
    hal_client: TestClient, find_uri_template: str, person: Person, people_uri: str
) -> None:
    find_uri = person.parse_uri(find_uri_template)
    person_response = hal_client.get(find_uri).json()

    self_link = get_hal_link(person_response, "self")

    assert self_link
    assert people_uri in self_link.href
    assert person.id_ in self_link.href
    assert person_response.get("id_") == person.id_

    embedded = person_response.get("_embedded")
    assert embedded

    items = embedded.get("sc:items")
    assert items


def test_update_person_from_uri_template(
    hal_client: TestClient,
    find_uri_template: str,
    update_uri_template: str,
    person: Person,
) -> None:
    find_uri = person.parse_uri(find_uri_template)
    before = hal_client.get(find_uri).json()

    new_data = {"name": f"updated_{uuid.uuid4().hex}"}
    update_uri = person.parse_uri(update_uri_template)
    response = hal_client.put(update_uri, json=new_data).json()

    assert response.get("name") == new_data.get("name")
    assert response.get("name") != before.get("name")

    before_uri = get_hal_link(before, "self")
    after_uri = get_hal_link(response, "self")

    assert before_uri == after_uri


def test_update_person_from_update_uri(
    hal_client: TestClient, find_uri_template: str, person: Person
) -> None:
    find_uri = person.parse_uri(find_uri_template)
    before = hal_client.get(find_uri).json()

    new_data = {"name": f"updated_{uuid.uuid4().hex}"}

    update_link = get_hal_link(before, "update")
    assert update_link
    response = hal_client.put(update_link.href, json=new_data).json()

    assert response.get("name") == new_data.get("name")
    assert response.get("name") != before.get("name")

    before_uri = get_hal_link(before, "self")
    after_uri = get_hal_link(response, "self")

    assert before_uri == after_uri


def test_get_person_items(
    hal_client: TestClient, find_uri_template: str, person: Person
) -> None:
    find_uri = person.parse_uri(find_uri_template)
    person_response = hal_client.get(find_uri).json()

    person_items = person_response.get("_embedded").get("sc:items")

    assert person_items
    assert isinstance(person_items, list)

    first_item, *_ = person_items
    first_item_link = get_hal_link(first_item, "self")
    assert first_item_link
    first_item_response = hal_client.get(first_item_link.href).json()

    assert first_item == first_item_response


@pytest.fixture()
def existing_item() -> Any:
    return {"id_": "item04"}


@pytest.fixture()
def non_existing_item() -> Any:
    return {"id_": "item05"}


def test_add_item_to_unlocked_person(
    hal_client: TestClient,
    find_uri_template: str,
    unlocked_person: Person,
    existing_item: Any,
) -> None:
    find_uri = unlocked_person.parse_uri(find_uri_template)
    before = hal_client.get(find_uri).json()
    before_items = before.get("_embedded", {}).get("sc:items", [])
    add_item_link = get_hal_link(before, "add_item")

    assert add_item_link

    after = hal_client.put(add_item_link.href, json=existing_item).json()
    after_items = after.get("_embedded", {}).get("sc:items", [])
    assert after_items

    lenght_before = len(before_items)
    lenght_after = len(after_items)
    assert lenght_before + 1 == lenght_after

    assert after_items[-1].get("id_") == existing_item.get("id_")


def test_add_item_to_unlocked_person_nonexisting_item(
    hal_client: TestClient,
    find_uri_template: str,
    unlocked_person: Person,
    non_existing_item: Any,
) -> None:
    find_uri = unlocked_person.parse_uri(find_uri_template)
    before = hal_client.get(find_uri).json()
    add_item_link = get_hal_link(before, "add_item")

    assert add_item_link

    response = hal_client.put(add_item_link.href, json=non_existing_item)
    assert response.status_code == 404
    assert response.json() == {"detail": "No item found with id item05"}


def test_add_item_to_locked_person(
    hal_client: TestClient,
    find_uri_template: str,
    locked_person: Person,
) -> None:
    find_uri = locked_person.parse_uri(find_uri_template)
    before = hal_client.get(find_uri).json()
    add_item_uri = get_hal_link(before, "add_item")

    assert not add_item_uri
