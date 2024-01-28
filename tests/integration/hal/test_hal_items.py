import uuid

import pytest
from fastapi.testclient import TestClient

from examples.hal import Item
from fastapi_hypermodel import UrlType, get_hal_link_href


@pytest.fixture()
def item_uri() -> str:
    return "/items"


@pytest.fixture()
def find_uri_template(hal_client: TestClient, item_uri: str) -> UrlType:
    find_uri = get_hal_link_href(hal_client.get(item_uri).json(), "find")
    assert find_uri
    return find_uri.href


@pytest.fixture()
def update_uri_template(hal_client: TestClient, item_uri: str) -> UrlType:
    update_uri = get_hal_link_href(hal_client.get(item_uri).json(), "update")
    assert update_uri
    return update_uri.href


def test_items_content_type(hal_client: TestClient, item_uri: str) -> None:
    response = hal_client.get(item_uri)
    content_type = response.headers.get("content-type")
    assert content_type == "application/hal+json"


def test_get_items(hal_client: TestClient, item_uri: str) -> None:
    response = hal_client.get(item_uri).json()

    self_link = get_hal_link_href(response, "self")
    assert self_link
    assert self_link.href == item_uri

    find_uri = response.get("_links", {}).get("find", {})
    assert find_uri.get("templated")
    assert item_uri in find_uri.get("href")

    items = response.get("_embedded", {}).get("sc:items", [])
    assert items
    assert len(items) == 4


def test_get_item(
    hal_client: TestClient,
    find_uri_template: str,
    item_uri: str,
    item: Item,
) -> None:
    find_uri = item.parse_uri(find_uri_template)
    item_response = hal_client.get(find_uri).json()

    item_hal_link = get_hal_link_href(item_response, "self")

    assert item_hal_link
    assert item_uri in item_hal_link.href
    assert item.id_ in item_hal_link.href
    assert item_response.get("id_") == item.id_


def test_update_item_from_uri_template(
    hal_client: TestClient,
    find_uri_template: str,
    update_uri_template: str,
    item: Item,
) -> None:
    find_uri = item.parse_uri(find_uri_template)
    before = hal_client.get(find_uri).json()

    new_data = {"name": f"updated_{uuid.uuid4().hex}"}
    update_uri = item.parse_uri(update_uri_template)
    response = hal_client.put(update_uri, json=new_data).json()

    assert response.get("name") == new_data.get("name")
    assert response.get("name") != before.get("name")

    before_uri = get_hal_link_href(before, "self")
    after_uri = get_hal_link_href(response, "self")

    assert before_uri == after_uri


def test_update_item_from_update_uri(
    hal_client: TestClient, find_uri_template: str, item: Item
) -> None:
    find_uri = item.parse_uri(find_uri_template)
    before = hal_client.get(find_uri).json()

    new_data = {"name": f"updated_{uuid.uuid4().hex}"}

    update_link = get_hal_link_href(before, "update")
    assert update_link

    response = hal_client.put(update_link.href, json=new_data).json()

    assert response.get("name") == new_data.get("name")
    assert response.get("name") != before.get("name")

    before_uri = get_hal_link_href(before, "self")
    after_uri = get_hal_link_href(response, "self")

    assert before_uri == after_uri
