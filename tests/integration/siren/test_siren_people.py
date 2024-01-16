import uuid
from typing import Any, Mapping, Sequence

import pytest
from fastapi.testclient import TestClient

from examples.siren import Person
from fastapi_hypermodel import get_siren_action, get_siren_link


@pytest.fixture()
def people_uri() -> str:
    return "/people"


@pytest.fixture()
def find_uri_template(siren_client: TestClient, people_uri: str) -> Mapping[str, str]:
    reponse = siren_client.get(people_uri).json()
    find_uri = get_siren_action(reponse, "find")
    assert find_uri
    return find_uri


@pytest.fixture()
def update_uri_template(siren_client: TestClient, people_uri: str) -> Mapping[str, str]:
    reponse = siren_client.get(people_uri).json()
    update_uri = get_siren_action(reponse, "update")
    assert update_uri
    return update_uri


def test_people_content_type(siren_client: TestClient, people_uri: str) -> None:
    response = siren_client.get(people_uri)
    content_type = response.headers.get("content-type")
    assert content_type == "application/siren+json"


def test_get_people(siren_client: TestClient, people_uri: str) -> None:
    response = siren_client.get(people_uri).json()

    people = response.get("entities", [])
    assert len(people) == 2
    assert all(person.get("rel") == "people" for person in people)

    self_uri = get_siren_link(response, "self").get("href")
    assert self_uri == people_uri

    find_uri = get_siren_action(response, "find")
    assert find_uri.get("templated")
    assert people_uri in find_uri.get("href", "")


def test_get_person(
    siren_client: TestClient,
    find_uri_template: Mapping[str, str],
    person: Person,
    people_uri: str,
) -> None:
    find_uri_href = find_uri_template.get("href", "")
    find_uri = person.parse_uri(find_uri_href)

    find_method = find_uri_template.get("method", "")
    person_response = siren_client.request(find_method, find_uri).json()

    person_href = get_siren_link(person_response, "self").get("href", "")

    assert people_uri in person_href

    assert person.properties

    person_id = person.properties.get("id_", "")
    assert person_id in person_href
    assert person_response.get("properties").get("id_") == person_id

    entities = person_response.get("entities")
    assert entities
    assert len(entities) == 2


def test_update_person_from_uri_template(
    siren_client: TestClient,
    find_uri_template: Mapping[str, str],
    update_uri_template: Mapping[str, str],
    person: Person,
) -> None:
    find_uri_href = find_uri_template.get("href", "")
    find_uri = person.parse_uri(find_uri_href)

    find_method = find_uri_template.get("method", "")
    before = siren_client.request(find_method, find_uri).json()

    new_data = {"name": f"updated_{uuid.uuid4().hex}"}

    update_uri_href = update_uri_template.get("href", "")
    update_uri = person.parse_uri(update_uri_href)

    update_method = update_uri_template.get("method", "")
    response = siren_client.request(update_method, update_uri, json=new_data).json()

    assert response.get("properties").get("name") == new_data.get("name")
    assert response.get("properties").get("name") != before.get("name")

    before_uri = get_siren_link(before, "self").get("href")
    after_uri = get_siren_link(response, "self").get("href")

    assert before_uri == after_uri


def test_update_person_from_update_uri(
    siren_client: TestClient, find_uri_template: Mapping[str, str], person: Person
) -> None:
    find_uri_href = find_uri_template.get("href", "")
    find_uri = person.parse_uri(find_uri_href)

    find_method = find_uri_template.get("method", "")
    before = siren_client.request(find_method, find_uri).json()

    new_data = {"name": f"updated_{uuid.uuid4().hex}"}

    update_action = get_siren_action(before, "update")
    update_href = update_action.get("href", "")
    update_method = update_action.get("method", "")
    response = siren_client.request(update_method, update_href, json=new_data).json()

    assert response.get("properties").get("name") == new_data.get("name")
    assert response.get("properties").get("name") != before.get("name")

    before_uri = get_siren_link(before, "self").get("href")
    after_uri = get_siren_link(response, "self").get("href")

    assert before_uri == after_uri


def test_get_person_items(
    siren_client: TestClient, find_uri_template: Mapping[str, str], person: Person
) -> None:
    find_uri_href = find_uri_template.get("href", "")
    find_uri = person.parse_uri(find_uri_href)

    find_method = find_uri_template.get("method", "")
    person_response = siren_client.request(find_method, find_uri).json()

    person_items: Sequence[Mapping[str, str]] = person_response.get("entities")

    assert person_items
    assert isinstance(person_items, list)
    assert all(item.get("rel") == "items" for item in person_items)

    first_item, *_ = person_items
    first_item_uri = get_siren_link(first_item, "self").get("href", "")
    first_item_response = siren_client.get(first_item_uri).json()
    first_item_response.update({"rel": "items"})

    assert first_item == first_item_response


@pytest.fixture()
def existing_item() -> Any:
    return {"id_": "item04"}


@pytest.fixture()
def non_existing_item() -> Any:
    return {"id_": "item05"}


def test_add_item_to_unlocked_person(
    siren_client: TestClient,
    find_uri_template: Mapping[str, str],
    unlocked_person: Person,
    existing_item: Any,
) -> None:
    find_uri_href = find_uri_template.get("href", "")
    find_uri = unlocked_person.parse_uri(find_uri_href)

    find_method = find_uri_template.get("method", "")
    before = siren_client.request(find_method, find_uri).json()

    before_items = before.get("entities", {})
    add_item_action = get_siren_action(before, "add_item")

    assert add_item_action

    add_item_href = add_item_action.get("href", "")
    add_item_method = add_item_action.get("method", "")

    after = siren_client.request(
        add_item_method, add_item_href, json=existing_item
    ).json()
    after_items = after.get("entities", {})
    assert after_items

    lenght_before = len(before_items)
    lenght_after = len(after_items)
    assert lenght_before + 1 == lenght_after

    assert after_items[-1].get("properties").get("id_") == existing_item.get("id_")


def test_add_item_to_unlocked_person_nonexisting_item(
    siren_client: TestClient,
    find_uri_template: Mapping[str, str],
    unlocked_person: Person,
    non_existing_item: Any,
) -> None:
    find_uri_href = find_uri_template.get("href", "")
    find_uri = unlocked_person.parse_uri(find_uri_href)

    find_method = find_uri_template.get("method", "")

    before = siren_client.request(find_method, find_uri).json()

    add_item_action = get_siren_action(before, "add_item")

    assert add_item_action

    add_item_href = add_item_action.get("href", "")
    add_item_method = add_item_action.get("method", "")

    response = siren_client.request(
        add_item_method, add_item_href, json=non_existing_item
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "No item found with id item05"}


def test_add_item_to_locked_person(
    siren_client: TestClient,
    find_uri_template: Mapping[str, str],
    locked_person: Person,
) -> None:
    find_uri_href = find_uri_template.get("href", "")
    find_uri = locked_person.parse_uri(find_uri_href)

    find_method = find_uri_template.get("method", "")

    before = siren_client.request(find_method, find_uri).json()

    add_item_action = get_siren_link(before, "add_item").get("href")

    assert not add_item_action
