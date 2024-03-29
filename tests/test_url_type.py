from typing import Any, Mapping

import pytest

from fastapi_hypermodel import HyperModel, UrlType


class MockClassWithURL(HyperModel):
    test_field: UrlType = UrlType()


@pytest.mark.usefixtures("app")
def test_openapi_schema(url_type_schema: Mapping[str, Any]) -> None:
    mock = MockClassWithURL()
    schema = mock.model_json_schema()
    url_type_schema = schema["properties"]["test_field"]

    assert all(url_type_schema.get(k) == v for k, v in url_type_schema.items())
