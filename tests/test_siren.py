from typing import Any, Optional, Sequence

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel
from pydantic.fields import FieldInfo

from fastapi_hypermodel import (
    SirenActionFor,
    SirenActionType,
    SirenFieldType,
    SirenHyperModel,
    SirenLinkFor,
    SirenLinkType,
    SirenResponse,
)
from fastapi_hypermodel.siren import SirenEmbeddedType, get_siren_action, get_siren_link
from fastapi_hypermodel.url_type import UrlType

SAMPLE_ENDPOINT = "/mock_read_with_path_siren/{id_}"


class MockClass(SirenHyperModel):
    id_: str


class MockParams(BaseModel):
    name: str
    lenght: float


class MockClassWithProperties(SirenHyperModel):
    id_: str
    model: MockClass


@pytest.fixture()
def sample_endpoint_uri() -> str:
    return SAMPLE_ENDPOINT


@pytest.fixture()
def siren_app(app: FastAPI, sample_endpoint_uri: str) -> FastAPI:
    @app.get(sample_endpoint_uri, response_class=SirenResponse)
    def mock_read_with_path_siren() -> Any:  # pragma: no cover
        return {}

    @app.get("siren_with_body", response_class=SirenResponse)
    def mock_read_with_path_siren_with_hypermodel(
        mock: MockParams,
    ) -> Any:  # pragma: no cover
        return mock.model_dump()

    SirenHyperModel.init_app(app)

    return app


@pytest.fixture()
def siren_client(siren_app: FastAPI) -> TestClient:
    return TestClient(app=siren_app)


def test_content_type(siren_client: TestClient) -> None:
    response = siren_client.get("mock_read_with_path_siren/test")

    content_type = response.headers.get("content-type")
    assert content_type == "application/siren+json"


# SirenLinkFor


def test_siren_link_for(siren_app: FastAPI) -> None:
    mock = MockClass(id_="test")

    siren_link_for = SirenLinkFor(
        "mock_read_with_path_siren", {"id_": "<id_>"}, rel=["test"]
    )
    assert mock.properties

    siren_link_for_type = siren_link_for(siren_app, mock.properties)

    assert isinstance(siren_link_for_type, SirenLinkType)
    assert siren_link_for_type.href == "/mock_read_with_path_siren/test"
    assert siren_link_for_type.rel == ["test"]


def test_siren_link_for_serialize(siren_app: FastAPI) -> None:
    mock = MockClass(id_="test")

    siren_link_for = SirenLinkFor(
        "mock_read_with_path_siren", {"id_": "<id_>"}, rel=["test"]
    )
    assert mock.properties
    siren_link_for_type = siren_link_for(siren_app, mock.properties)

    assert siren_link_for_type

    siren_link_for_type_dict = siren_link_for_type.model_dump()
    assert siren_link_for_type_dict.get("href") == "/mock_read_with_path_siren/test"
    assert siren_link_for_type_dict.get("rel") == ["test"]
    assert siren_link_for_type_dict.get("title") is None


def test_siren_link_for_serialize_with_optional_fields(siren_app: FastAPI) -> None:
    mock = MockClass(id_="test")

    siren_link_for = SirenLinkFor(
        "mock_read_with_path_siren", {"id_": "<id_>"}, rel=["test"], title="test"
    )
    assert mock.properties
    siren_link_for_type = siren_link_for(siren_app, mock.properties)

    assert siren_link_for_type

    siren_link_for_type_dict = siren_link_for_type.model_dump()
    assert siren_link_for_type_dict.get("href") == "/mock_read_with_path_siren/test"
    assert siren_link_for_type_dict.get("rel") == ["test"]
    assert siren_link_for_type_dict.get("title") == "test"


def test_siren_link_for_condition(siren_app: FastAPI) -> None:
    mock = MockClass(id_="test")

    siren_link_for = SirenLinkFor(
        "mock_read_with_path_siren",
        {"id_": "<id_>"},
        rel=["test"],
        condition=lambda values: "id_" in values,
    )
    assert mock.properties
    siren_link_for_type = siren_link_for(siren_app, mock.properties)

    assert isinstance(siren_link_for_type, SirenLinkType)
    assert siren_link_for_type.href == "/mock_read_with_path_siren/test"
    assert siren_link_for_type.rel == ["test"]


def test_siren_link_for_condition_false(siren_app: FastAPI) -> None:
    mock = MockClass(id_="test")

    siren_link_for = SirenLinkFor(
        "mock_read_with_path_siren",
        {"id_": "<id_>"},
        rel=["test"],
        condition=lambda values: "id_" not in values,
    )
    assert mock.properties
    siren_link_for_type = siren_link_for(siren_app, mock.properties)

    assert siren_link_for_type is None


def test_siren_link_for_no_app() -> None:
    mock = MockClass(id_="test")

    siren_link_for = SirenLinkFor(
        "mock_read_with_path_siren", {"id_": "<id_>"}, rel=["test"]
    )
    assert mock.properties
    siren_link_for_type = siren_link_for(None, mock.properties)

    assert siren_link_for_type is None


def test_siren_link_for_templated(siren_app: FastAPI) -> None:
    mock = MockClass(id_="test")

    siren_link_for = SirenLinkFor(
        "mock_read_with_path_siren", {"id_": "<id_>"}, rel=["test"], templated=True
    )

    assert mock.properties
    siren_link_for_type = siren_link_for(siren_app, mock.properties)

    assert isinstance(siren_link_for_type, SirenLinkType)
    assert siren_link_for_type.href == "/mock_read_with_path_siren/{id_}"
    assert siren_link_for_type.rel == ["test"]


def test_siren_link_for_missing_rel(siren_app: FastAPI) -> None:
    mock = MockClass(id_="test")

    siren_link_for = SirenLinkFor("mock_read_with_path_siren", {"id_": "<id_>"})

    assert mock.properties

    with pytest.raises(ValueError, match="Field rel and href are mandatory"):
        siren_link_for(siren_app, mock.properties)


# SirenFieldType


def test_siren_field_type() -> None:
    siren_field_type = SirenFieldType(name="test_field")

    assert siren_field_type.name == "test_field"


def test_siren_field_type_parse_type_text() -> None:
    python_type = Optional[str]
    html_type = SirenFieldType.parse_type(python_type)

    assert html_type == "text"


def test_siren_field_type_parse_type_number() -> None:
    python_type = Optional[float]
    html_type = SirenFieldType.parse_type(python_type)

    assert html_type == "number"


def test_siren_field_type_parse_type_dict() -> None:
    python_type = Optional[Any]
    html_type = SirenFieldType.parse_type(python_type)

    assert html_type == "text"


def test_siren_field_type_from_field_info() -> None:
    field_info = FieldInfo()
    field_type = SirenFieldType.from_field_info("test", field_info)

    assert isinstance(field_type, SirenFieldType)
    assert field_type.name == "test"
    assert field_type.type_ == "text"
    assert field_type.value is None


def test_siren_field_type_from_field_info_with_type() -> None:
    field_info = FieldInfo(annotation=Optional[float])
    field_type = SirenFieldType.from_field_info("test", field_info)

    assert isinstance(field_type, SirenFieldType)
    assert field_type.name == "test"
    assert field_type.type_ == "number"
    assert field_type.value is None


def test_siren_field_type_from_field_info_with_default() -> None:
    field_info = FieldInfo(default="hello")
    field_type = SirenFieldType.from_field_info("test", field_info)

    assert isinstance(field_type, SirenFieldType)
    assert field_type.name == "test"
    assert field_type.type_ == "text"
    assert field_type.value == "hello"


def test_siren_field_type_from_field_info_with_type_and_default() -> None:
    field_info = FieldInfo(annotation=Optional[float], default=10)
    field_type = SirenFieldType.from_field_info("test", field_info)

    assert isinstance(field_type, SirenFieldType)
    assert field_type.name == "test"
    assert field_type.type_ == "number"
    assert field_type.value == 10


# SirenActionFor


def test_siren_action_for(siren_app: FastAPI) -> None:
    mock = MockClass(id_="test")

    siren_action_for = SirenActionFor(
        "mock_read_with_path_siren", {"id_": "<id_>"}, name="test"
    )
    assert mock.properties
    siren_action_for_type = siren_action_for(siren_app, mock.properties)

    assert isinstance(siren_action_for_type, SirenActionType)
    assert siren_action_for_type.href == "/mock_read_with_path_siren/test"
    assert siren_action_for_type.name == "test"
    assert not siren_action_for_type.fields


def test_siren_action_for_serialize(siren_app: FastAPI) -> None:
    mock = MockClass(id_="test")

    siren_action_for = SirenActionFor(
        "mock_read_with_path_siren", {"id_": "<id_>"}, name="test"
    )
    assert mock.properties
    siren_action_for_type = siren_action_for(siren_app, mock.properties)

    assert siren_action_for_type

    siren_action_for_type_dict = siren_action_for_type.model_dump()
    assert siren_action_for_type_dict.get("href") == "/mock_read_with_path_siren/test"
    assert siren_action_for_type_dict.get("name") == "test"
    assert siren_action_for_type_dict.get("title") is None
    assert not siren_action_for_type.fields


def test_siren_action_for_serialize_with_optional_fields(siren_app: FastAPI) -> None:
    mock = MockClass(id_="test")

    siren_action_for = SirenActionFor(
        "mock_read_with_path_siren", {"id_": "<id_>"}, name="test", title="test"
    )
    assert mock.properties
    siren_action_for_type = siren_action_for(siren_app, mock.properties)

    assert siren_action_for_type

    siren_action_for_type_dict = siren_action_for_type.model_dump()
    assert siren_action_for_type_dict.get("href") == "/mock_read_with_path_siren/test"
    assert siren_action_for_type_dict.get("name") == "test"
    assert siren_action_for_type_dict.get("title") == "test"
    assert not siren_action_for_type.fields


def test_siren_action_for_no_name(siren_app: FastAPI) -> None:
    mock = MockClass(id_="test")

    siren_action_for = SirenActionFor("mock_read_with_path_siren", {"id_": "<id_>"})
    assert mock.properties

    with pytest.raises(ValueError, match="Field name and href are mandatory"):
        siren_action_for(siren_app, mock.properties)


def test_siren_action_for_no_app() -> None:
    mock = MockClass(id_="test")

    siren_action_for = SirenActionFor(
        "mock_read_with_path_siren", {"id_": "<id_>"}, rel=["test"]
    )
    assert mock.properties
    siren_action_for_type = siren_action_for(None, mock.properties)

    assert siren_action_for_type is None


def test_siren_action_for_condition(siren_app: FastAPI) -> None:
    mock = MockClass(id_="test")

    siren_action_for = SirenActionFor(
        "mock_read_with_path_siren",
        {"id_": "<id_>"},
        name="test",
        condition=lambda values: "id_" in values,
    )
    assert mock.properties
    siren_action_for_type = siren_action_for(siren_app, mock.properties)

    assert isinstance(siren_action_for_type, SirenActionType)
    assert siren_action_for_type.href == "/mock_read_with_path_siren/test"
    assert siren_action_for_type.name == "test"
    assert not siren_action_for_type.fields


def test_siren_action_for_condition_false(siren_app: FastAPI) -> None:
    mock = MockClass(id_="test")

    siren_action_for = SirenActionFor(
        "mock_read_with_path_siren",
        {"id_": "<id_>"},
        name="test",
        condition=lambda values: "id_" not in values,
    )
    assert mock.properties
    siren_action_for_type = siren_action_for(siren_app, mock.properties)

    assert siren_action_for_type is None


def test_siren_aciton_for_templated(siren_app: FastAPI) -> None:
    mock = MockClass(id_="test")

    siren_aciton_for = SirenActionFor(
        "mock_read_with_path_siren", {"id_": "<id_>"}, name="test", templated=True
    )

    assert mock.properties
    siren_action_for_type = siren_aciton_for(siren_app, mock.properties)

    assert isinstance(siren_action_for_type, SirenActionType)
    assert siren_action_for_type.href == "/mock_read_with_path_siren/{id_}"
    assert siren_action_for_type.name == "test"
    assert not siren_action_for_type.fields


def test_siren_action_for_with_fields(siren_app: FastAPI) -> None:
    mock = MockClass(id_="test")

    siren_action_for = SirenActionFor(
        "mock_read_with_path_siren_with_hypermodel", name="test"
    )
    assert mock.properties
    siren_action_for_type = siren_action_for(siren_app, mock.properties)

    assert isinstance(siren_action_for_type, SirenActionType)
    assert siren_action_for_type.href == "siren_with_body"
    assert siren_action_for_type.name == "test"

    fields = siren_action_for_type.fields
    assert fields
    assert len(fields) == 2
    assert all(field.name for field in fields)
    assert all(field.type_ for field in fields)
    assert any(field.name == "name" and field.type_ == "text" for field in fields)
    assert any(field.name == "lenght" and field.type_ == "number" for field in fields)

    assert siren_action_for_type.type_ == "application/x-www-form-urlencoded"


def test_siren_action_for_with_fields_no_populate(siren_app: FastAPI) -> None:
    mock = MockClass(id_="test")

    siren_action_for = SirenActionFor(
        "mock_read_with_path_siren_with_hypermodel", name="test", populate_fields=False
    )
    assert mock.properties
    siren_action_for_type = siren_action_for(siren_app, mock.properties)

    assert isinstance(siren_action_for_type, SirenActionType)
    assert siren_action_for_type.href == "siren_with_body"
    assert siren_action_for_type.name == "test"

    fields = siren_action_for_type.fields
    assert fields
    assert len(fields) == 2
    assert all(field.name for field in fields)
    assert all(field.type_ for field in fields)
    assert any(field.name == "name" and field.type_ == "text" for field in fields)
    assert any(field.name == "lenght" and field.type_ == "number" for field in fields)

    assert siren_action_for_type.type_ == "application/x-www-form-urlencoded"


# SirenHypermodel


def test_siren_hypermodel_with_properties() -> None:
    mock = MockClass(id_="test")
    assert mock.properties
    assert mock.properties.get("id_") == "test"


def test_siren_hypermodel_with_entities_embedded_hypermodel() -> None:
    mock = MockClassWithProperties(id_="test", model=MockClass(id_="test_nested"))
    assert mock.entities

    first, *_ = mock.entities
    assert isinstance(first, SirenEmbeddedType)
    assert first.rel == ["model"]
    assert first.properties
    assert first.properties.get("id_") == "test_nested"


def test_siren_hypermodel_with_entities_embedded_link() -> None:
    class MockClassWithEmbeddedLink(SirenHyperModel):
        id_: str
        model: SirenLinkType

    mock = MockClassWithEmbeddedLink(
        id_="test", model=SirenLinkType(href=UrlType("test_nested"), rel=["model"])
    )
    assert mock.entities

    first, *_ = mock.entities
    assert isinstance(first, SirenLinkType)
    assert first.rel == ["model"]
    assert first.href == "test_nested"


@pytest.mark.usefixtures("siren_app")
def test_siren_hypermodel_with_links() -> None:
    class MockClassWithLinks(SirenHyperModel):
        id_: str

        links: Sequence[SirenLinkFor] = (
            SirenLinkFor("mock_read_with_path_siren", {"id_": "<id_>"}, rel=["self"]),
        )

    mock = MockClassWithLinks(id_="test")

    assert mock.links

    first, *_ = mock.links
    assert isinstance(first, SirenLinkType)
    assert first.rel == ["self"]
    assert first.href == "/mock_read_with_path_siren/test"


@pytest.mark.usefixtures("siren_app")
def test_siren_hypermodel_with_links_no_self() -> None:
    class MockClassWithLinks(SirenHyperModel):
        id_: str

        links: Sequence[SirenLinkFor] = (
            SirenLinkFor("mock_read_with_path_siren", {"id_": "<id_>"}, rel=["model"]),
        )

    with pytest.raises(
        ValueError, match="If links are present, a link with rel self must be present"
    ):
        MockClassWithLinks(id_="test")


@pytest.mark.usefixtures("siren_app")
def test_siren_hypermodel_with_actions() -> None:
    class MockClassWithLinks(SirenHyperModel):
        id_: str

        actions: Sequence[SirenActionFor] = (
            SirenActionFor("mock_read_with_path_siren", {"id_": "<id_>"}, name="test"),
        )

    mock = MockClassWithLinks(id_="test")

    assert mock.actions

    first, *_ = mock.actions
    assert isinstance(first, SirenActionType)
    assert first.name == "test"
    assert first.href == "/mock_read_with_path_siren/test"


@pytest.mark.usefixtures("siren_app")
def test_siren_hypermodel_with_actions_outside_actions() -> None:
    class MockClassWithActions(SirenHyperModel):
        id_: str

        test_action: SirenActionFor = SirenActionFor(
            "mock_read_with_path_siren", {"id_": "<id_>"}, name="model"
        )

    with pytest.raises(
        ValueError, match="All actions must be inside the actions property"
    ):
        MockClassWithActions(id_="test")


@pytest.mark.usefixtures("siren_app")
def test_siren_hypermodel_with_actions_empty() -> None:
    class MockClassWithActions(SirenHyperModel):
        id_: str

        actions: Sequence[SirenActionFor] = (
            SirenActionFor(
                "mock_read_with_path_siren",
                {"id_": "<id_>"},
                name="model",
                condition=lambda values: "model" in values,
            ),
        )

    mock = MockClassWithActions(id_="test")
    assert not mock.actions_


def test_siren_parse_uri() -> None:
    uri_template = "/model/{id_}"

    mock = MockClass(id_="test")

    assert mock.properties
    assert mock.parse_uri(uri_template) == f"/model/{mock.properties.get('id_')}"


# Utils


@pytest.fixture()
def siren_response() -> Any:
    return {
        "links": [{"rel": ["self"], "href": "/self"}],
        "actions": [{"name": "add", "href": "/self"}],
    }


def test_get_siren_link_href(siren_response: Any) -> None:
    actual = get_siren_link(siren_response, "self")
    expected = SirenLinkType(href=UrlType("/self"), rel=["self"])

    assert actual == expected


def test_get_siren_link_href_not_found(siren_response: Any) -> None:
    actual = get_siren_link(siren_response, "update")
    assert actual is None


def test_get_siren_action_href(siren_response: Any) -> None:
    actual = get_siren_action(siren_response, "add")
    expected = SirenActionType(href=UrlType("/self"), name="add")

    assert actual == expected


def test_get_siren_action_href_not_found(siren_response: Any) -> None:
    actual = get_siren_action(siren_response, "update")
    assert actual is None
