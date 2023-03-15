import pytest

from fastapi_hypermodel.hypermodel import (
    HyperModel,
    InvalidAttribute,
    UrlFor,
    _get_value,
    _get_value_for_key,
    _get_value_for_keys,
    _tpl,
)

from .app import items, people, read_item


@pytest.mark.parametrize(
    "template", ["<id>", " <id>", "<id> ", "< id>", "<id  >", "< id >"]
)
def test_tpl(template):
    assert _tpl(template) == "id"
    assert _tpl(template) == "id"
    assert _tpl(template) == "id"


def test_get_value_for_key():
    class Object:
        pass

    o = Object()
    o.foo = "bar"
    assert _get_value_for_key(o, "foo", None) == "bar"
    assert _get_value_for_key(o, "missing", "default") == "default"


def test_get_value_for_key_dict():
    o = {"foo": "bar"}
    assert _get_value_for_key(o, "foo", None) == "bar"
    assert _get_value_for_key(o, "missing", "default") == "default"


def test_get_value_for_keys():
    class Object:
        pass

    o = Object()
    o.foo = "bar"

    assert _get_value_for_keys(o, ["foo"], None) == "bar"

    o.foo = Object()
    o.foo.bar = "baz"

    assert _get_value_for_keys(o, ["foo", "bar"], None) == "baz"


def test_get_value():
    class Object:
        pass

    o = Object()
    o.foo = Object()
    o.foo.bar = "baz"

    assert _get_value(o, "foo.bar", None) == "baz"


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


@pytest.mark.parametrize("person_id", people.keys())
def test_people_linkset(client, person_id):
    url = f"/people/{person_id}"
    response = client.get(url)
    assert "href" in response.json()
    links = response.json().get("links")
    assert "self" in links
    assert links["self"] == f"/people/{person_id}"
    assert "items" in links
    assert links["items"] == f"/people/{person_id}/items"


@pytest.mark.parametrize("person_id", ["person01"])
def test_people_linkset_condition_met(client, person_id):
    url = f"/people/{person_id}"
    response = client.get(url)
    links = response.json().get("links")
    assert "addItem" in links
    assert links["addItem"] == f"/people/{person_id}/items"


@pytest.mark.parametrize("person_id", ["person02"])
def test_people_linkset_condition_unmet(client, person_id):
    url = f"/people/{person_id}"
    response = client.get(url)
    links = response.json().get("links")
    assert "AddItem" not in links


@pytest.mark.parametrize("person_id", people.keys())
def test_people_hal(client, person_id):
    url = f"/people/{person_id}"
    response = client.get(url)
    assert "hal_href" in response.json()
    assert response.json().get("hal_href").get("href") == url
    assert response.json().get("hal_href").get("method") == "GET"


@pytest.mark.parametrize("person_id", people.keys())
def test_people_halset(client, person_id):
    url = f"/people/{person_id}"
    response = client.get(url)
    assert "href" in response.json()
    links = response.json().get("_links")

    assert "items" in links
    assert links["items"]["href"] == url + "/items"
    assert links["items"]["method"] == "GET"


@pytest.mark.parametrize("person_id", ["person01"])
def test_people_halset_condition_met(client, person_id):
    url = f"/people/{person_id}"
    response = client.get(url)
    links = response.json().get("_links")

    assert "addItem" in links
    assert links["addItem"]["href"] == url + "/items"
    assert links["addItem"]["method"] == "PUT"
    assert links["addItem"]["description"]


@pytest.mark.parametrize("person_id", ["person02"])
def test_people_halset_condition_unmet(client, person_id):
    url = f"/people/{person_id}"
    response = client.get(url)
    assert "href" in response.json()
    links = response.json().get("_links")

    assert "addItem" not in links


@pytest.mark.parametrize(
    "endpoint",
    [
        pytest.param("read_item", id="Use of a string endpoint"),
        pytest.param(read_item, id="Use of a Callable endpoint"),
    ],
)
def test_bad_attribute(app, endpoint):
    class ItemSummary(HyperModel):
        href = UrlFor(endpoint, {"item_id": "<id>"})

    assert ItemSummary._hypermodel_bound_app is app

    with pytest.raises(InvalidAttribute):
        _ = ItemSummary()


### APP TESTS, SHOULD REMOVE


def test_update_item(client):
    url = "/items/item01"
    response = client.put(url, json={"name": "updated"})
    assert "href" in response.json()
    assert response.json().get("href") == url


@pytest.mark.parametrize("person_id", people.keys())
def test_create_item(client, person_id):
    url = f"/people/{person_id}/items"
    response = client.put(url, json={"id": "item04", "name": "Qux", "price": 20.2})
    assert "item04" in [item.get("id") for item in response.json()]
