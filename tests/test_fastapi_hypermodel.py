import pytest
from starlette.routing import NoMatchFound

from fastapi_hypermodel.hypermodel import (
    _tpl,
    _get_value_for_key,
    _get_value_for_keys,
    _get_value,
    HyperModel,
    HyperRef,
    MissingEndpoint,
    InvalidAttribute,
)
from .app import items, people


@pytest.mark.parametrize(
    "template", ["<id>", " <id>", "<id> ", "< id>", "<id  >", "< id >"]
)
def test_tpl(template):
    assert _tpl(template) == "id"
    assert _tpl(template) == "id"
    assert _tpl(template) == "id"


def test_get_value_for_key():
    class Object(object):
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
    class Object(object):
        pass

    o = Object()
    o.foo = "bar"

    assert _get_value_for_keys(o, ["foo"], None) == "bar"

    o.foo = Object()
    o.foo.bar = "baz"

    assert _get_value_for_keys(o, ["foo", "bar"], None) == "baz"


def test_get_value():
    class Object(object):
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


def test_bad_endpoint(app):
    class ItemSummary(HyperModel):
        id: str
        href: HyperRef

        class Href:
            endpoint = "bad_endpoint"
            values = {"id": "<id>"}

    assert ItemSummary._hypermodel_bound_app is app

    with pytest.raises(NoMatchFound):
        _ = ItemSummary(id="id0")


def test_no_endpoint(app):
    class ItemSummary(HyperModel):
        id: str
        href: HyperRef

        class Href:
            values = {"id": "<id>"}

    assert ItemSummary._hypermodel_bound_app is app

    with pytest.raises(MissingEndpoint):
        _ = ItemSummary(id="id0")


def test_abd_attribute(app):
    class ItemSummary(HyperModel):
        href: HyperRef

        class Href:
            endpoint = "read_item"
            values = {"item_id": "<id>"}

    assert ItemSummary._hypermodel_bound_app is app

    with pytest.raises(InvalidAttribute):
        _ = ItemSummary()
