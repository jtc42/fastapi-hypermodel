from typing import Any, Dict, Optional
from fastapi import FastAPI
from pydantic import BaseModel
import pytest

from typing_extensions import Self

from fastapi_hypermodel import HyperModel, AbstractHyperField, InvalidAttribute


class MockHypermediaType(BaseModel):
    href: Optional[str] = None


class MockHypermedia(MockHypermediaType, AbstractHyperField):
    def __build_hypermedia__(self: Self, *_: Any) -> Optional[Any]:
        return MockHypermediaType(href="test")


class MockClass(HyperModel):
    test_field: MockHypermedia = MockHypermedia()


class MockSimpleClass(HyperModel):
    id_: str


def test_app_registration(unregistered_app: FastAPI) -> None:
    assert MockSimpleClass._hypermodel_bound_app != unregistered_app  # noqa: SLF001

    HyperModel.init_app(unregistered_app)

    assert MockSimpleClass._hypermodel_bound_app is unregistered_app  # noqa: SLF001


def test_parse_uri():
    uri_template = "/model/{id_}"

    mock = MockSimpleClass(id_="test")

    assert mock.parse_uri(uri_template) == f"/model/{mock.id_}"


def test_parse_uri_missing():
    uri_template = "/model/{age}"

    mock = MockSimpleClass(id_="test")

    with pytest.raises(InvalidAttribute):
        mock.parse_uri(uri_template)


def test_parse_uri_empty_field():
    uri_template = "/model/{}"

    mock = MockSimpleClass(id_="test")

    with pytest.raises(ValueError):
        mock.parse_uri(uri_template)


def test_build_hypermedia(app: FastAPI):
    mock = MockHypermedia()

    rendered_url = mock.__build_hypermedia__(app, {})
    assert rendered_url

    uri = rendered_url.model_dump()
    assert uri == {"href": "test"}


def test_hypermodel_validator():
    mock = MockClass()

    assert mock.test_field == MockHypermediaType(href="test")
    assert mock.model_dump() == {"test_field": {"href": "test"}}
