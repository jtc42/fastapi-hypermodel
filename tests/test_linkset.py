from typing import Any, Dict, Mapping, Optional
from fastapi import FastAPI
from pydantic import BaseModel
import pytest

from fastapi_hypermodel import (
    HyperModel,
    LinkSet,
    AbstractHyperField,
)

from typing_extensions import Self


test_app = FastAPI()


@pytest.fixture()
def app() -> FastAPI:
    HyperModel.init_app(test_app)
    return test_app


@pytest.fixture()
def href_schema() -> Any:
    return {"type": "string", "format": "uri", "minLength": 1, "maxLength": 2**16}


class MockHypermediaType(BaseModel):
    href: Optional[str] = None


class MockHypermedia(MockHypermediaType, AbstractHyperField):
    def __build_hypermedia__(
        self: Self,
        app: Optional[FastAPI],
        values: Mapping[str, Any],
    ) -> Optional[Any]:
        return MockHypermediaType(href="test")


class MockHypermediaEmpty(AbstractHyperField):
    def __build_hypermedia__(
        self: Self,
        app: Optional[FastAPI],
        values: Mapping[str, Any],
    ) -> Optional[Any]:
        return None


class MockClassLinkSetEmpty(HyperModel):
    test_field: LinkSet = LinkSet()


class MockClassLinkSet(HyperModel):
    test_field: LinkSet = LinkSet(
        {
            "self": MockHypermedia(),
        }
    )


class MockClassLinkSetWithEmptyHypermedia(HyperModel):
    test_field: LinkSet = LinkSet(
        {
            "self": MockHypermedia(),
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


def test_linkset_schema(href_schema: Dict[str, Any]) -> None:
    linkset = MockClassLinkSet()
    schema = linkset.model_json_schema()["$defs"]["LinkSet"]

    schema_type = schema["type"]
    assert schema_type == "object"

    additional_properties = schema["additionalProperties"]
    assert additional_properties == href_schema


def test_linkset_empty(app: FastAPI):
    linkset = LinkSet()
    hypermedia = linkset.__build_hypermedia__(app, {})
    assert hypermedia == {}


def test_linkset_empty_no_app():
    linkset = LinkSet()
    hypermedia = linkset.__build_hypermedia__(None, {})
    assert hypermedia == {}
