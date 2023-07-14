_uri_schema = {"type": "string", "format": "uri", "minLength": 1, "maxLength": 2**16}

def _is_subset(d1: dict, d2: dict):
    return all(d1.get(k) == d2.get(k) for k in d2)


def test_openapi_schema_href(app):
    openapi = app.openapi()
    href_schema = openapi["components"]["schemas"]["Person"]["properties"]["href"]
    assert _is_subset(href_schema, _uri_schema)


def test_openapi_schema_linkset(app):
    openapi = app.openapi()
    linkset_schema = openapi["components"]["schemas"]["Person"]["properties"]["links"]
    assert linkset_schema["type"] == "object"
    assert _is_subset(linkset_schema["additionalProperties"], _uri_schema)
