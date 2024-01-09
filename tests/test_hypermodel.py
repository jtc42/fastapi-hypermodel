from typing import Any, Optional

import pytest
from fastapi import FastAPI
from pydantic import BaseModel, PrivateAttr
from typing_extensions import Self

from fastapi_hypermodel import AbstractHyperField, HyperModel, InvalidAttribute


class MockHypermediaType(BaseModel):
    href: Optional[str] = None

    def __bool__(self: Self) -> bool:
        return bool(self.href)


class MockHypermedia(MockHypermediaType, AbstractHyperField[MockHypermediaType]):
    _href: Optional[str] = PrivateAttr()

    def __init__(self: Self, href: Optional[str] = None) -> None:
        super().__init__()
        self._href = href

    def __call__(self: Self, *_: Any) -> MockHypermediaType:
        return MockHypermediaType(href=self._href)


class MockClass(HyperModel):
    test_field: MockHypermedia = MockHypermedia("test")


class MockClassWithEmptyField(HyperModel):
    test_field: MockHypermedia = MockHypermedia()


class MockSimpleClass(HyperModel):
    id_: str


def test_app_registration(unregistered_app: FastAPI) -> None:
    assert MockSimpleClass._app != unregistered_app  # noqa: SLF001

    HyperModel.init_app(unregistered_app)

    assert MockSimpleClass._app is unregistered_app  # noqa: SLF001


def test_parse_uri() -> None:
    uri_template = "/model/{id_}"

    mock = MockSimpleClass(id_="test")

    assert mock.parse_uri(uri_template) == f"/model/{mock.id_}"


def test_parse_uri_missing() -> None:
    uri_template = "/model/{age}"

    mock = MockSimpleClass(id_="test")

    with pytest.raises(InvalidAttribute):
        mock.parse_uri(uri_template)


def test_parse_uri_empty_field() -> None:
    uri_template = "/model/{}"

    mock = MockSimpleClass(id_="test")

    with pytest.raises(ValueError, match="Empty Fields Cannot be Processed"):
        mock.parse_uri(uri_template)


def test_build_hypermedia(app: FastAPI) -> None:
    mock = MockHypermedia("test")

    rendered_url = mock(app, {})
    assert rendered_url

    uri = rendered_url.model_dump()
    assert uri == {"href": "test"}


def test_hypermodel_validator() -> None:
    mock = MockClass()

    assert mock.test_field == MockHypermediaType(href="test")
    assert mock.model_dump() == {"test_field": {"href": "test"}}


def test_hypermodel_validator_empty() -> None:
    mock = MockClassWithEmptyField()

    assert mock == MockClassWithEmptyField()
