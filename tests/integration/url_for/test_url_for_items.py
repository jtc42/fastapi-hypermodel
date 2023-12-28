from fastapi.testclient import TestClient

from examples.url_for import Item

import pytest

import uuid


@pytest.fixture()
def item_uri() -> str:
    return "/items"


@pytest.fixture()
def find_uri_template(url_for_client: TestClient, item_uri: str) -> str:
    find_uri = url_for_client.get(item_uri).json().get("find")
    assert find_uri
    return find_uri


@pytest.fixture()
def update_uri_template(url_for_client: TestClient, item_uri: str) -> str:
    update_uri = url_for_client.get(item_uri).json().get("update")
    assert update_uri
    return update_uri


def test_get_items(url_for_client: TestClient, item_uri: str) -> None:
    response = url_for_client.get(item_uri).json()

    self_uri = response.get("href")
    assert self_uri == item_uri

    find_uri = response.get("find")
    assert find_uri

    update_uri = response.get("update")
    assert update_uri


def test_get_item(
    url_for_client: TestClient,
    find_uri_template: str,
    item_uri: str,
    item: Item,
) -> None:
    find_uri = item.parse_uri(find_uri_template)
    item_response = url_for_client.get(find_uri).json()

    item_href = item_response.get("href")

    assert item_uri in item_href and item.id_ in item_href
    assert item_response.get("id_") == item.id_


def test_update_item_from_uri_template(
    url_for_client: TestClient,
    find_uri_template: str,
    update_uri_template: str,
    item: Item,
) -> None:
    find_uri = item.parse_uri(find_uri_template)
    before = url_for_client.get(find_uri).json()

    new_data = {"name": f"updated_{uuid.uuid4().hex}"}
    update_uri = item.parse_uri(update_uri_template)
    response = url_for_client.put(update_uri, json=new_data).json()

    assert response.get("name") == new_data.get("name")
    assert response.get("name") != before.get("name")

    before_uri = before.get("href")
    after_uri = response.get("href")

    assert before_uri == after_uri


def test_update_item_from_update_uri(
    url_for_client: TestClient, find_uri_template: str, item: Item
) -> None:
    find_uri = item.parse_uri(find_uri_template)
    before = url_for_client.get(find_uri).json()

    new_data = {"name": f"updated_{uuid.uuid4().hex}"}

    update_uri = before.get("update")
    response = url_for_client.put(update_uri, json=new_data).json()

    assert response.get("name") == new_data.get("name")
    assert response.get("name") != before.get("name")

    before_uri = before.get("href")
    after_uri = response.get("href")

    assert before_uri == after_uri
