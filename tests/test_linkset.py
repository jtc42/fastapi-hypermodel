from typing import Any, Optional
from fastapi import FastAPI
from pydantic import BaseModel, PrivateAttr

from fastapi_hypermodel import (
    HyperModel,
    LinkSet,
    AbstractHyperField,
)

from typing_extensions import Self


class MockHypermediaType(BaseModel):
    href: Optional[str] = None

    def __bool__(self):
        return bool(self.href)


class MockHypermedia(MockHypermediaType, AbstractHyperField[MockHypermediaType]):
    _href: Optional[str] = PrivateAttr()

    def __init__(self: Self, href: Optional[str] = None) -> None:
        super().__init__()
        self._href = href

    def __build_hypermedia__(self: Self, *_: Any) -> MockHypermediaType:
        return MockHypermediaType(href=self._href)


class MockHypermediaEmpty(AbstractHyperField[MockHypermediaType]):
    def __build_hypermedia__(self: Self, *_: Any) -> MockHypermediaType:
        return MockHypermediaType()


class MockClassLinkSet(HyperModel):
    test_field: LinkSet = LinkSet(
        {
            "self": MockHypermedia("test"),
        }
    )


class MockClassLinkSetEmpty(HyperModel):
    test_field: LinkSet = LinkSet()


class MockClassLinkSetWithEmptyHypermedia(HyperModel):
    test_field: LinkSet = LinkSet(
        {
            "self": MockHypermedia("test"),
            "other": MockHypermediaEmpty(),
        }
    )


def test_linkset_in_hypermodel():
    linkset = MockClassLinkSet()
    hypermedia = linkset.model_dump()
    test_field = hypermedia.get("test_field")
    assert test_field

    expected = {"self": {"href": "test"}}
    assert test_field == expected


def test_linkset_in_hypermodel_empty():
    linkset = MockClassLinkSetEmpty()
    hypermedia = linkset.model_dump()
    test_field = hypermedia.get("test_field")
    expected = {}
    assert test_field == expected


def test_linkset_in_hypermodel_with_empty_hypermedia():
    linkset = MockClassLinkSetWithEmptyHypermedia()
    hypermedia = linkset.model_dump()
    test_field = hypermedia.get("test_field")
    assert test_field

    expected = {"self": {"href": "test"}}
    assert test_field == expected


def test_linkset_schema() -> None:
    linkset = MockClassLinkSet()
    schema = linkset.model_json_schema()["$defs"]["LinkSet"]

    schema_type = schema["type"]
    assert schema_type == "object"

    assert "properties" not in schema
    assert "additionalProperties" in schema


def test_linkset_empty(app: FastAPI):
    linkset = LinkSet()
    hypermedia = linkset.__build_hypermedia__(app, {})
    assert hypermedia and hypermedia.mapping == {}


def test_linkset_empty_no_app():
    linkset = LinkSet()
    hypermedia = linkset.__build_hypermedia__(None, {})
    assert hypermedia and hypermedia.mapping == {}
