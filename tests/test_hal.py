import uuid
from typing import Any, Generator, List, Mapping, Sequence

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import Field, ValidationError
from pytest_lazy_fixtures import lf

from fastapi_hypermodel import (
    HALFor,
    HALForType,
    HalHyperModel,
    HALResponse,
    LinkSet,
    UrlType,
)


class MockClass(HalHyperModel):
    id_: str

    links: LinkSet = Field(
        default=LinkSet({
            "self": HALFor("mock_read_with_path_hal", {"id_": "<id_>"}),
        }),
        alias="_links",
    )


class MockClassWithEmbedded(HalHyperModel):
    id_: str

    test: MockClass


class MockClassWithMultipleEmbedded(HalHyperModel):
    id_: str

    test: MockClass
    test2: MockClass


class MockClassWithEmbeddedAliased(HalHyperModel):
    id_: str

    test: MockClass = Field(alias="sc:test")


class MockClassWithEmbeddedList(HalHyperModel):
    id_: str

    test: Sequence[MockClass]


class MockClassWithEmbeddedListAliased(HalHyperModel):
    id_: str

    test: Sequence[MockClass] = Field(alias="sc:test")


class MockClassWithCuries(HalHyperModel):
    id_: str

    links: LinkSet = Field(
        default=LinkSet({
            "self": HALFor("mock_read_with_path_hal", {"id_": "<id_>"}),
            "sc:item": HALFor("mock_read_with_path_hal", {"id_": "<id_>"}),
        }),
        alias="_links",
    )


class MockClassWithMissingCuries(HalHyperModel):
    id_: str

    links: LinkSet = Field(
        default=LinkSet({
            "self": HALFor("mock_read_with_path_hal", {"id_": "<id_>"}),
            "missing:item": HALFor("mock_read_with_path_hal", {"id_": "<id_>"}),
        }),
        alias="_links",
    )


@pytest.fixture()
def hal_app(app: FastAPI) -> FastAPI:
    @app.get("/mock_read_with_path/{id_}", response_class=HALResponse)
    def mock_read_with_path_hal() -> Any:  # pragma: no cover
        return {}

    HalHyperModel.init_app(app)

    return app


@pytest.fixture()
def hal_for_properties() -> Any:
    return {
        "href": {
            "default": "",
            "format": "uri",
            "maxLength": 65536,
            "minLength": 1,
            "title": "Href",
            "type": "string",
        },
        "templated": {
            "anyOf": [{"type": "boolean"}, {"type": "null"}],
            "default": None,
            "title": "Templated",
        },
        "title": {
            "anyOf": [{"type": "string"}, {"type": "null"}],
            "default": None,
            "title": "Title",
        },
        "name": {
            "anyOf": [{"type": "string"}, {"type": "null"}],
            "default": None,
            "title": "Name",
        },
        "type": {
            "anyOf": [{"type": "string"}, {"type": "null"}],
            "default": None,
            "title": "Type",
        },
        "hreflang": {
            "anyOf": [{"type": "string"}, {"type": "null"}],
            "default": None,
            "title": "Hreflang",
        },
        "profile": {
            "anyOf": [{"type": "string"}, {"type": "null"}],
            "default": None,
            "title": "Profile",
        },
        "deprecation": {
            "anyOf": [{"type": "string"}, {"type": "null"}],
            "default": None,
            "title": "Deprecation",
        },
    }


@pytest.fixture()
def hal_for_schema(hal_for_properties: Mapping[str, Any]) -> Any:
    return {"type": "object", "properties": hal_for_properties, "title": "HALFor"}


@pytest.fixture()
def invalid_links_empty() -> Any:
    return {"_links": {}}


@pytest.fixture()
def invalid_links() -> Any:
    return {"_links": {"test_link": {"name": "test_name"}}}


@pytest.fixture()
def invalid_links_list() -> Any:
    return {"_links": {"test_link": [{"name": "test_name"}]}}


@pytest.fixture()
def invalid_links_not_mapping() -> Any:
    return {"_links": [{"name": "test_name"}]}


@pytest.fixture()
def invalid_links_self_is_templated() -> Any:
    return {"_links": {"self": {"href": "test", "templated": True}}}


@pytest.fixture()
def invalid_links_self_empty_href() -> Any:
    return {"_links": {"self": {"href": ""}}}


@pytest.fixture()
def invalid_links_empty_name() -> Any:
    return {"_links": {"self": {"href": "test"}, "": {"href": "test"}}}


@pytest.fixture()
def invalid_embedded_links(invalid_links: Any) -> Any:
    return {"_embedded": {"test": invalid_links}}


@pytest.fixture()
def invalid_embedded_links_list(invalid_links_list: Any) -> Any:
    return {"_embedded": {"test": invalid_links_list}}


@pytest.fixture()
def invalid_embedded_links_empty(invalid_links_empty: Any) -> Any:
    return {"_embedded": {"test": invalid_links_empty}}


@pytest.fixture()
def invalid_embedded_empty() -> Any:
    return {"_embedded": {}}


@pytest.fixture()
def invalid_embedded_not_mapping() -> Any:
    return {"_embedded": [1, 2, 3]}


@pytest.fixture()
def curies() -> List[HALForType]:
    return [
        HALForType(
            href=UrlType("https://schema.org/{rel}"),
            name="sc",
            templated=True,
        )
    ]


@pytest.fixture()
def _set_curies(curies: Sequence[HALForType]) -> Generator[None, None, None]:
    HalHyperModel.register_curies(curies)
    yield
    HalHyperModel.register_curies([])


@pytest.fixture()
def invalid_curies_not_templated() -> Any:
    return {
        "_links": {
            "self": HALForType(href=UrlType("test")),
            "curies": [
                HALForType(
                    href=UrlType("https://schema.org/{rel}"), name="sc", templated=False
                )
            ],
        },
    }


@pytest.fixture()
def invalid_curies_no_name() -> Any:
    return {
        "_links": {
            "self": HALForType(href=UrlType("test")),
            "curies": [
                HALForType(href=UrlType("https://schema.org/{rel}"), templated=True)
            ],
        },
    }


@pytest.fixture()
def invalid_curies_no_href() -> Any:
    return {
        "_links": {
            "self": HALForType(href=UrlType("test")),
            "curies": [HALForType(href=UrlType(""), name="sc", templated=True)],
        },
    }


@pytest.fixture()
def invalid_curies_no_rel_in_href() -> Any:
    return {
        "_links": {
            "self": HALForType(href=UrlType("test")),
            "curies": [
                HALForType(
                    href=UrlType("https://schema.org/"), name="sc", templated=True
                )
            ],
        },
    }


@pytest.fixture()
def invalid_curies_used_but_not_defined() -> Any:
    return {
        "_links": {
            "self": HALForType(href=UrlType("test")),
            "sc:items": HALForType(href=UrlType("test")),
        },
    }


@pytest.fixture()
def invalid_curies_missing_and_used_in_links() -> Any:
    return {
        "_links": {
            "self": HALForType(href=UrlType("test")),
            "curies": [
                HALForType(
                    href=UrlType("https://schema.org/{rel}"), name="sc", templated=True
                )
            ],
            "missing:items": HALForType(href=UrlType("test")),
        },
    }


@pytest.fixture()
def invalid_curies_missing_and_used_in_embedded() -> Any:
    return {
        "_links": {
            "self": HALForType(href=UrlType("test")),
            "curies": [
                HALForType(
                    href=UrlType("https://schema.org/{rel}"), name="sc", templated=True
                )
            ],
        },
        "_embedded": {"missing:items": None},
    }


@pytest.fixture()
def invalid_curies_missing_and_used_in_embedded_nested() -> Any:
    return {
        "_links": {
            "self": HALForType(href=UrlType("test")),
            "curies": [
                HALForType(
                    href=UrlType("https://schema.org/{rel}"), name="sc", templated=True
                )
            ],
        },
        "_embedded": {
            "items": {
                "_links": {
                    "self": HALForType(href=UrlType("test")),
                    "missing:items": HALForType(href=UrlType("items")),
                }
            }
        },
    }


@pytest.mark.parametrize(
    "invalid_response",
    [
        lf("invalid_links_empty"),
        lf("invalid_links"),
        lf("invalid_links_list"),
        lf("invalid_links_not_mapping"),
        lf("invalid_links_self_is_templated"),
        lf("invalid_links_self_empty_href"),
        lf("invalid_links_empty_name"),
        lf("invalid_embedded_links"),
        lf("invalid_embedded_links_list"),
        lf("invalid_embedded_links_empty"),
        lf("invalid_embedded_empty"),
        lf("invalid_embedded_not_mapping"),
        lf("invalid_curies_not_templated"),
        lf("invalid_curies_no_name"),
        lf("invalid_curies_no_href"),
        lf("invalid_curies_no_rel_in_href"),
        lf("invalid_curies_used_but_not_defined"),
        lf("invalid_curies_missing_and_used_in_links"),
        lf("invalid_curies_missing_and_used_in_embedded"),
        lf("invalid_curies_missing_and_used_in_embedded_nested"),
    ],
)
def test_hal_response_invalid(hal_app: FastAPI, invalid_response: Any) -> None:
    suffix = uuid.uuid4().hex
    endpoint = f"/test_response_invalid_{suffix}"

    @hal_app.get(endpoint, response_class=HALResponse)
    def _() -> Any:
        return invalid_response

    test_client = TestClient(hal_app)

    with pytest.raises((ValidationError, TypeError)):
        test_client.get(endpoint)


def test_hal_response_empty(hal_app: FastAPI) -> None:
    @hal_app.get("/test_response", response_class=HALResponse)
    def _() -> Any:
        pass

    test_client = TestClient(hal_app)

    response = test_client.get("/test_response")

    content_type = response.headers.get("content-type")
    assert content_type == "application/hal+json"


def test_hal_response_single_link(hal_app: FastAPI) -> None:
    @hal_app.get("/test_response_single_link", response_class=HALResponse)
    def _() -> Any:  # pragma: no cover
        return {"_links": {"self": HALForType(href=UrlType("test"))}}

    test_client = TestClient(hal_app)

    response = test_client.get("/test_response_single_link")

    content_type = response.headers.get("content-type")
    assert content_type == "application/hal+json"


def test_hal_response_link_list(hal_app: FastAPI) -> None:
    @hal_app.get("/test_response_link_list", response_class=HALResponse)
    def _() -> Any:  # pragma: no cover
        return {
            "_links": {
                "self": HALForType(href=UrlType("test")),
                "other": [HALForType(href=UrlType("test"))],
            }
        }

    test_client = TestClient(hal_app)

    response = test_client.get("/test_response_link_list")

    content_type = response.headers.get("content-type")
    assert content_type == "application/hal+json"


def test_hal_response_embedded(hal_app: FastAPI) -> None:
    @hal_app.get("/test_response_single_link_list", response_class=HALResponse)
    def _() -> Any:  # pragma: no cover
        return {"_embedded": {"self": [HALForType(href=UrlType())]}}

    test_client = TestClient(hal_app)

    response = test_client.get("/test_response_single_link_list")

    content_type = response.headers.get("content-type")
    assert content_type == "application/hal+json"


def test_hal_for(hal_app: FastAPI) -> None:
    mock = MockClass(id_="test")

    hal_for = HALFor("mock_read_with_path_hal", {"id_": "<id_>"})
    hal_for_type = hal_for(hal_app, vars(mock))

    assert isinstance(hal_for_type, HALForType)
    assert hal_for_type.href == "/mock_read_with_path/test"


@pytest.mark.usefixtures("hal_app")
def test_hal_for_no_app() -> None:
    mock = MockClass(id_="test")

    hal_for = HALFor("mock_read_with_path_hal", {"id_": "<id_>"})
    hypermedia = hal_for(None, vars(mock))

    assert hypermedia.href == ""


def test_build_hypermedia_passing_condition(app: FastAPI) -> None:
    sample_id = "test"
    hal_for = HALFor(
        "mock_read_with_path",
        {"id_": "<id_>"},
        condition=lambda values: values["locked"],
    )
    uri = hal_for(app, {"id_": sample_id, "locked": True})
    assert uri.href == f"/mock_read/{sample_id}"


def test_build_hypermedia_template(hal_app: FastAPI) -> None:
    hal_for = HALFor(
        "mock_read_with_path",
        templated=True,
    )
    uri = hal_for(hal_app, {})
    assert uri.href == "/mock_read/{id_}"


def test_build_hypermedia_not_passing_condition(hal_app: FastAPI) -> None:
    sample_id = "test"
    hal_for = HALFor(
        "mock_read_with_path",
        {"id_": "<id_>"},
        condition=lambda values: values["locked"],
    )
    uri = hal_for(hal_app, {"id_": sample_id, "locked": False})
    assert uri.href == ""


def test_build_hypermedia_with_href(app: FastAPI) -> None:
    sample_id = "test"
    hal_for = HALFor(
        "mock_read_with_path",
        {"id_": "<id_>"},
        condition=lambda values: values["locked"],
    )
    uri = hal_for(app, {"id_": sample_id, "locked": True})
    assert uri.href == f"/mock_read/{sample_id}"


@pytest.mark.usefixtures("hal_app")
def test_openapi_schema(hal_for_schema: Mapping[str, Any]) -> None:
    mock = MockClass(id_="test")
    schema = mock.model_json_schema()
    link_set_definition = schema["$defs"]["LinkSet"]["additionalProperties"]["anyOf"]
    hal_for_definition = next(
        definition
        for definition in link_set_definition
        if definition.get("title") == "HALFor"
    )

    assert all(hal_for_definition.get(k) == v for k, v in hal_for_schema.items())


@pytest.mark.usefixtures("_set_curies")
@pytest.mark.usefixtures("hal_app")
def test_register_curies() -> None:
    mock = MockClass(id_="test").model_dump(by_alias=True)
    curies = mock.get("_links", {}).get("curies", [])
    assert curies

    curie_raw, *_ = curies
    curie = HALForType.model_validate(curie_raw)
    assert curie.href == "https://schema.org/{rel}"


@pytest.mark.usefixtures("hal_app")
def test_with_embedded() -> None:
    mock = MockClass(id_="test")
    mock_with_embedded = MockClassWithEmbedded(id_="test_parent", test=mock).model_dump(
        by_alias=True
    )
    assert mock_with_embedded

    child, *_ = mock_with_embedded.get("_embedded", {}).get("test", [])
    assert child
    assert child.get("id_") == "test"


@pytest.mark.usefixtures("hal_app")
def test_with_multiple_embedded() -> None:
    mock = MockClass(id_="test1")
    mock2 = MockClass(id_="test2")
    mock_with_embedded = MockClassWithMultipleEmbedded(
        id_="test_parent", test=mock, test2=mock2
    ).model_dump(by_alias=True)
    assert mock_with_embedded

    embedded = mock_with_embedded.get("_embedded", {})
    child, *_ = embedded.get("test", [])
    assert child
    assert child.get("id_") == "test1"

    child2, *_ = embedded.get("test2", [])
    assert child2
    assert child2.get("id_") == "test2"


@pytest.mark.usefixtures("hal_app")
def test_with_embedded_and_alias() -> None:
    dump = {"id_": "test_parent", "sc:test": {"id_": "test"}}
    mock_with_embedded = MockClassWithEmbeddedAliased.model_validate(dump).model_dump(
        by_alias=True
    )
    assert mock_with_embedded

    child, *_ = mock_with_embedded.get("_embedded", {}).get("sc:test", [])
    assert child
    assert child.get("id_") == "test"


@pytest.mark.usefixtures("hal_app")
def test_with_embedded_list() -> None:
    mock = MockClass(id_="test")
    mock_with_embedded = MockClassWithEmbeddedList(
        id_="test_parent", test=[mock]
    ).model_dump(by_alias=True)
    assert mock_with_embedded

    child, *_ = mock_with_embedded.get("_embedded", {}).get("test", [])
    assert child
    assert child.get("id_") == "test"


@pytest.mark.usefixtures("hal_app")
def test_with_embedded_list_and_alias() -> None:
    dump = {"id_": "test_parent", "sc:test": [{"id_": "test"}]}
    mock_with_embedded = MockClassWithEmbeddedListAliased.model_validate(
        dump
    ).model_dump(by_alias=True)
    assert mock_with_embedded

    child, *_ = mock_with_embedded.get("_embedded", {}).get("sc:test", [])
    assert child
    assert child.get("id_") == "test"


def test_hal_response_curies_defined_but_not_used(hal_app: FastAPI) -> None:
    @hal_app.get("/test_curies_defined_but_not_used", response_class=HALResponse)
    def _() -> Any:  # pragma: no cover
        return {
            "_links": {
                "self": HALForType(href=UrlType("test")),
                "curies": [
                    HALForType(
                        href=UrlType("https://schema.org/{rel}"),
                        name="sc",
                        templated=True,
                    )
                ],
            },
        }

    test_client = TestClient(hal_app)

    response = test_client.get("/test_curies_defined_but_not_used")

    assert response.status_code == 200


def test_hal_response_curies_defined_and_used_in_links(hal_app: FastAPI) -> None:
    @hal_app.get("/test_curies_defined_and_used_in_links", response_class=HALResponse)
    def _() -> Any:  # pragma: no cover
        return {
            "_links": {
                "self": HALForType(href=UrlType("test")),
                "curies": [
                    HALForType(
                        href=UrlType("https://schema.org/{rel}"),
                        name="sc",
                        templated=True,
                    )
                ],
                "sc:items": HALForType(href=UrlType("test")),
            },
        }

    test_client = TestClient(hal_app)

    response = test_client.get("/test_curies_defined_and_used_in_links")

    assert response.status_code == 200


def test_hal_response_curies_defined_and_used_in_embedded(hal_app: FastAPI) -> None:
    @hal_app.get(
        "/test_curies_defined_and_used_in_embedded", response_class=HALResponse
    )
    def _() -> Any:  # pragma: no cover
        return {
            "_links": {
                "self": HALForType(href=UrlType("test")),
                "curies": [
                    HALForType(
                        href=UrlType("https://schema.org/{rel}"),
                        name="sc",
                        templated=True,
                    )
                ],
            },
            "_embedded": {"sc:items": None},
        }

    test_client = TestClient(hal_app)

    response = test_client.get("/test_curies_defined_and_used_in_embedded")

    assert response.status_code == 200


def test_hal_response_curies_defined_used_in_nested(hal_app: FastAPI) -> None:
    @hal_app.get("/test_curies_defined_used_in_nested", response_class=HALResponse)
    def _() -> Any:  # pragma: no cover
        return {
            "_links": {
                "self": HALForType(href=UrlType("test")),
                "curies": [
                    HALForType(
                        href=UrlType("https://schema.org/{rel}"),
                        name="sc",
                        templated=True,
                    )
                ],
            },
            "_embedded": {
                "items": {
                    "_links": {
                        "self": HALForType(href=UrlType("test")),
                        "sc:items": HALForType(href=UrlType("items")),
                    }
                }
            },
        }

    test_client = TestClient(hal_app)

    response = test_client.get("/test_curies_defined_used_in_nested")

    assert response.status_code == 200
