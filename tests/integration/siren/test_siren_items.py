import uuid

import pytest
from fastapi.testclient import TestClient

from examples.siren import Item


@pytest.fixture()
def item_uri() -> str:
    return "/items"


# @pytest.fixture()
# def find_uri_template(siren_client: TestClient, item_uri: str) -> str:
    # find_uri = get_siren_link_href(siren_client.get(item_uri).json(), "find")
    # assert find_uri
    # return find_uri


# @pytest.fixture()
# def update_uri_template(siren_client: TestClient, item_uri: str) -> str:
    # update_uri = get_siren_link_href(siren_client.get(item_uri).json(), "update")
    # assert update_uri
    # return update_uri


def test_items_content_type(siren_client: TestClient, item_uri: str) -> None:
    response = siren_client.get(item_uri)
    content_type = response.headers.get("content-type")
    assert content_type == "application/siren+json"


# def test_get_items(siren_client: TestClient, item_uri: str) -> None:
#     response = siren_client.get(item_uri).json()

#     self_uri = get_siren_link_href(response, "self")
#     assert self_uri == item_uri

#     find_uri = response.get("_links", {}).get("find", {})
#     assert find_uri.get("templated")
#     assert item_uri in find_uri.get("href")

#     items = response.get("_embedded", {}).get("sc:items", [])
#     assert items
#     assert len(items) == 4


# def test_get_item(
#     siren_client: TestClient,
#     find_uri_template: str,
#     item_uri: str,
#     item: Item,
# ) -> None:
#     find_uri = item.parse_uri(find_uri_template)
#     item_response = siren_client.get(find_uri).json()

#     item_href = get_siren_link_href(item_response, "self")

#     assert item_uri in item_href
#     assert item.id_ in item_href
#     assert item_response.get("id_") == item.id_


# def test_update_item_from_uri_template(
#     siren_client: TestClient,
#     find_uri_template: str,
#     update_uri_template: str,
#     item: Item,
# ) -> None:
#     find_uri = item.parse_uri(find_uri_template)
#     before = siren_client.get(find_uri).json()

#     new_data = {"name": f"updated_{uuid.uuid4().hex}"}
#     update_uri = item.parse_uri(update_uri_template)
#     response = siren_client.put(update_uri, json=new_data).json()

#     assert response.get("name") == new_data.get("name")
#     assert response.get("name") != before.get("name")

#     before_uri = get_siren_link_href(before, "self")
#     after_uri = get_siren_link_href(response, "self")

#     assert before_uri == after_uri


# def test_update_item_from_update_uri(
#     siren_client: TestClient, find_uri_template: str, item: Item
# ) -> None:
#     find_uri = item.parse_uri(find_uri_template)
#     before = siren_client.get(find_uri).json()

#     new_data = {"name": f"updated_{uuid.uuid4().hex}"}

#     update_uri = get_siren_link_href(before, "update")
#     response = siren_client.put(update_uri, json=new_data).json()

#     assert response.get("name") == new_data.get("name")
#     assert response.get("name") != before.get("name")

#     before_uri = get_siren_link_href(before, "self")
#     after_uri = get_siren_link_href(response, "self")

#     assert before_uri == after_uri
