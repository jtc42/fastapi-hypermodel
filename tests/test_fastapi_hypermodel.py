import pytest

from .app import items, people


@pytest.mark.parametrize("item_id", items.keys())
def test_items(client, item_id):
    url = f"/items/{item_id}"
    response = client.get(url)
    assert "href" in response.json()
    assert response.json().get("href") == url


@pytest.mark.parametrize("person_id", people.keys())
def test_people(client, person_id):
    url = f"/people/{person_id}"
    response = client.get(url)
    assert "href" in response.json()
    assert response.json().get("href") == url
