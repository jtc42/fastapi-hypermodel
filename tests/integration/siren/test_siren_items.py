import uuid
from typing import Any, List

import pytest
from fastapi.testclient import TestClient

from examples.siren import Item
from fastapi_hypermodel import SirenActionType, get_siren_action, get_siren_link


@pytest.fixture()
def item_uri() -> str:
    return "/items"


@pytest.fixture()
def find_uri_template(siren_client: TestClient, item_uri: str) -> SirenActionType:
    reponse = siren_client.get(item_uri).json()
    find_uri = get_siren_action(reponse, "find")
    assert find_uri
    return find_uri


@pytest.fixture()
def update_uri_template(siren_client: TestClient, item_uri: str) -> SirenActionType:
    reponse = siren_client.get(item_uri).json()
    update_uri = get_siren_action(reponse, "update")
    assert update_uri
    return update_uri


def test_items_content_type(siren_client: TestClient, item_uri: str) -> None:
    response = siren_client.get(item_uri)

    content_type = response.headers.get("content-type")
    assert content_type == "application/siren+json"

    response_json = response.json()
    assert response_json

    assert not response_json.get("properties")

    links: List[Any] = response_json["links"]
    assert links
    assert isinstance(links, list)
    assert len(links) == 1
    first, *_ = links
    assert first["href"]
    assert not isinstance(first["href"], list)
    assert first["href"]

    actions: List[Any] = response_json["actions"]
    assert actions
    assert isinstance(actions, list)
    assert len(actions) == 2
    first, second, *_ = actions
    assert first["name"]
    assert not isinstance(first["name"], list)
    assert first["href"]
    assert len(first) == 5

    assert len(second) == 6
    fields = second.get("fields")
    assert fields
    assert all(field.get("name") for field in fields)
    types = [field.get("type") for field in fields]
    assert all(types)
    assert any(type_ == "text" for type_ in types)
    assert any(type_ == "number" for type_ in types)

    entities: List[Any] = response_json["entities"]
    assert entities
    assert isinstance(entities, list)
    assert len(entities) == 4

    first, *_ = entities
    properties = first["properties"]
    assert len(properties) == 4
    assert properties.get("name")
    assert properties.get("id_")
    assert not isinstance(properties.get("description"), list)
    assert properties.get("price")

    links = first["links"]
    assert isinstance(links, list)
    assert len(links) == 1

    first_link, *_ = links
    assert first_link.get("rel")
    assert len(first_link.get("rel")) == 1
    assert isinstance(first_link.get("rel"), list)
    assert first_link.get("href")

    actions = first["actions"]
    assert isinstance(actions, list)
    assert len(actions) == 1

    first_action, *_ = actions
    assert first_action.get("name")
    assert first_action.get("href")
    assert first_action.get("type")

    fields = first_action.get("fields")
    assert fields
    assert all(field.get("name") for field in fields)
    assert all(field.get("type") for field in fields)
    assert any(field.get("value") for field in fields)


def test_get_items(siren_client: TestClient, item_uri: str) -> None:
    response = siren_client.get(item_uri).json()

    self_link = get_siren_link(response, "self")
    assert self_link
    assert self_link.href == item_uri

    links = response.get("actions", [])
    find_uri = next(link for link in links if "find" in link.get("name"))
    assert find_uri.get("templated")
    assert item_uri in find_uri.get("href")

    items = response.get("entities", [])
    assert items
    assert len(items) == 4


def test_get_item(
    siren_client: TestClient,
    find_uri_template: SirenActionType,
    item_uri: str,
    item: Item,
) -> None:
    find_uri = item.parse_uri(find_uri_template.href)
    item_response = siren_client.request(find_uri_template.method, find_uri).json()

    item_href = get_siren_link(item_response, "self")
    assert item_href
    assert item.properties

    item_id = item.properties.get("id_", "")
    assert item_uri in item_href.href
    assert item_id in item_href.href
    assert item_response.get("properties").get("id_") == item_id


def test_update_item_from_uri_template(
    siren_client: TestClient,
    find_uri_template: SirenActionType,
    update_uri_template: SirenActionType,
    item: Item,
) -> None:
    find_uri = item.parse_uri(find_uri_template.href)

    assert find_uri_template.method

    before = siren_client.request(find_uri_template.method, find_uri).json()

    new_data = {"name": f"updated_{uuid.uuid4().hex}"}

    update_uri = item.parse_uri(update_uri_template.href)

    assert update_uri_template.method
    response = siren_client.request(
        update_uri_template.method, update_uri, json=new_data
    ).json()

    name = response.get("properties", {}).get("name")
    assert name == new_data.get("name")
    assert name != before.get("name")

    before_uri = get_siren_link(before, "self")
    after_uri = get_siren_link(response, "self")

    assert before_uri
    assert after_uri
    assert before_uri == after_uri


def test_update_item_from_update_uri(
    siren_client: TestClient, find_uri_template: SirenActionType, item: Item
) -> None:
    find_uri = item.parse_uri(find_uri_template.href)
    before = siren_client.request(find_uri_template.method, find_uri).json()

    new_data = {"name": f"updated_{uuid.uuid4().hex}"}

    update_action = get_siren_action(before, "update")

    assert update_action

    response = siren_client.request(
        update_action.method, update_action.href, json=new_data
    ).json()

    name = response.get("properties", {}).get("name")
    assert name == new_data.get("name")
    assert name != before.get("properties").get("name")

    before_uri = get_siren_link(before, "self")
    after_uri = get_siren_link(response, "self")

    assert before_uri
    assert after_uri
    assert before_uri == after_uri
