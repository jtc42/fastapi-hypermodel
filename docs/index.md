# FastAPI-HyperModel

<p align="center">
    <em>Simple hypermedia for FastAPI</em>
</p>
<p align="center">
<a href="https://pypi.org/project/fastapi-utils" target="_blank">
    <img src="https://badge.fury.io/py/fastapi-hypermodel.svg" alt="Package version">
</a>
    <img src="https://img.shields.io/pypi/pyversions/fastapi-hypermodel.svg">
    <img src="https://img.shields.io/github/license/jtc42/fastapi-hypermodel.svg">
</p>

---

**Documentation**: <a href="https://jtc42.github.io/fastapi-hypermodel/"
target="_blank">https://jtc42.github.io/fastapi-hypermodel/</a>

**Source Code**: <a href="https://github.com/jtc42/fastapi-hypermodel"
target="_blank">https://github.com/jtc42/fastapi-hypermodel</a>

---

FastAPI-HyperModel is a FastAPI + Pydantic extension for simplifying
hypermedia-driven API development. 

Hypermedia consist of enriching API responses by providing links to other URIs
within the services to fetch related resources or perform certain actions. There
are several levels according to the [Hypermedia Maturity Model
Levels](https://8thlight.com/insights/the-hypermedia-maturity-model). Using
Hypermedia makes APIs reach Level 3 of the Richardson Maturity Model (RMM),
which involves leveraging Hypertext As The Engine Of Application State
(HATEOAS), that is, Hypermedia.


## Single Item Example

=== "No Hypermedia"

    ```json
    {
        "id_": "item01",
        "name": "Foo",
        "price": 10.2,
    }
    ```

=== "Level 0 (URLFor)"

    ```json
    {
        "id_": "item01",
        "name": "Foo",
        "price": 10.2,

        "href": "/items/item01",
        "update": "/items/item01"
    }
    ```

=== "Level 1 (HAL)"

    ```json
    {
        "id_": "item01",
        "name": "Foo",
        "price": 10.2,

        "_links": {
            "self": {"href": "/items/item01"},
            "update": {"href": "/items/item01"},
            "curies": [
                {
                    "href": "https://schema.org/{rel}",
                    "templated": true,
                    "name": "sc"
                }
            ],
        },
    }
    ```

=== "Level 2 (Siren)"

    ```json
    {
        "properties": {
            "id_": "item01",
            "name": "Foo",
            "price": 10.2
        },
        "links": [
            {
                "rel": ["self"],
                "href": "/items/item01"
            }
        ],
        "actions": [
            {
                "name": "update",
                "method": "PUT",
                "href": "/items/item01",
                "type": "application/x-www-form-urlencoded",
                "fields": [
                    {
                        "name": "name",
                        "type": "text",
                        "value": "Foo"
                    },
                    {
                        "name": "description",
                        "type": "text",
                        "value": "None"
                    },
                    {
                        "name": "price",
                        "type": "number",
                        "value": "10.2"
                    }
                ]
            }
        ]
    }
    ```

## Collection of Items Example


=== "No Hypermedia"

    ```json
    {
        "items": [
            {
                "id_": "item01",
                "name": "Foo",
                "description": null,
                "price": 50.2,
            },
            {
                "id_": "item02",
                "name": "Bar",
                "description": "The Bar fighters",
                "price": 62.0,
            },
            {
                "id_": "item03",
                "name": "Baz",
                "description": "There goes my baz",
                "price": 50.2,
            },
            {
                "id_": "item04",
                "name": "Doe",
                "description": "There goes my Doe",
                "price": 5.0,
            }
        ],
    }
    ```

=== "Level 0 (URLFor)"

    ```json
    {
        "items": [
            {
                "id_": "item01",
                "name": "Foo",
                "description": null,
                "price": 50.2,

                "href": "/items/item01",
                "update": "/items/item01"
            },
            {
                "id_": "item02",
                "name": "Bar",
                "description": "The Bar fighters",
                "price": 62.0,

                "href": "/items/item02",
                "update": "/items/item02"
            },
            {
                "id_": "item03",
                "name": "Baz",
                "description": "There goes my baz",
                "price": 50.2,

                "href": "/items/item03",
                "update": "/items/item03"
            },
            {
                "id_": "item04",
                "name": "Doe",
                "description": "There goes my Doe",
                "price": 5.0,

                "href": "/items/item04",
                "update": "/items/item04"
            }
        ],

        "href": "/items",
        "find": "/items/{id_}",
        "update": "/items/{id_}"
    }
    ```

=== "Level 1 (HAL)"

    ```json
    {
        "_embedded": {
            "sc:items": [
                {
                    "id_": "item01",
                    "name": "Foo",
                    "description": null,
                    "price": 10.2,

                    "_links": {
                        "self": {
                            "href": "/items/item01"
                        },
                        "update": {
                            "href": "/items/item01"
                        },
                        "curies": [
                            {
                                "href": "https://schema.org/{rel}",
                                "templated": true,
                                "name": "sc"
                            }
                        ]
                    }
                },
                {
                    "id_": "item02",
                    "name": "Bar",
                    "description": "The Bar fighters",
                    "price": 62.0,

                    "_links": {
                        "self": {
                            "href": "/items/item02"
                        },
                        "update": {
                            "href": "/items/item02"
                        },
                        "curies": [
                            {
                                "href": "https://schema.org/{rel}",
                                "templated": true,
                                "name": "sc"
                            }
                        ]
                    }
                },
                {
                    "id_": "item03",
                    "name": "Baz",
                    "description": "There goes my baz",
                    "price": 50.2,

                    "_links": {
                        "self": {
                            "href": "/items/item03"
                        },
                        "update": {
                            "href": "/items/item03"
                        },
                        "curies": [
                            {
                                "href": "https://schema.org/{rel}",
                                "templated": true,
                                "name": "sc"
                            }
                        ]
                    }
                },
                {
                    "id_": "item04",
                    "name": "Doe",
                    "description": "There goes my Doe",
                    "price": 5.0,
                    
                    "_links": {
                        "self": {
                            "href": "/items/item04"
                        },
                        "update": {
                            "href": "/items/item04"
                        },
                        "curies": [
                            {
                                "href": "https://schema.org/{rel}",
                                "templated": true,
                                "name": "sc"
                            }
                        ]
                    }
                }
            ]
        },

        "_links": {
            "self": {
                "href": "/items"
            },
            "find": {
                "href": "/items/{id_}",
                "templated": true
            },
            "update": {
                "href": "/items/{id_}",
                "templated": true
            },
            "curies": [
                {
                    "href": "https://schema.org/{rel}",
                    "templated": true,
                    "name": "sc"
                }
            ]
        }
    }
    ```

=== "Level 2 (Siren)"

    ```json
    {
        "entities": [
            {
                "properties": {
                    "id_": "item01",
                    "name": "Foo",
                    "description": null,
                    "price": 10.2
                },
                "links": [
                    {
                        "rel": ["self"],
                        "href": "/items/item01"
                    }
                ],
                "actions": [
                    {
                        "name": "update",
                        "method": "PUT",
                        "href": "/items/item01",
                        "type": "application/x-www-form-urlencoded",
                        "fields": [
                            {
                                "name": "name",
                                "type": "text",
                                "value": "Foo"
                            },
                            {
                                "name": "description",
                                "type": "text",
                                "value": "None"
                            },
                            {
                                "name": "price",
                                "type": "number",
                                "value": "10.2"
                            }
                        ]
                    }
                ],
                "rel": ["items"]
            },
            {
                "properties": {
                    "id_": "item02",
                    "name": "Bar",
                    "description": "The Bar fighters",
                    "price": 62.0
                },
                "links": [
                    {
                        "rel": ["self"],
                        "href": "/items/item02"
                    }
                ],
                "actions": [
                    {
                        "name": "update",
                        "method": "PUT",
                        "href": "/items/item02",
                        "type": "application/x-www-form-urlencoded",
                        "fields": [
                            {
                                "name": "name",
                                "type": "text",
                                "value": "Bar"
                            },
                            {
                                "name": "description",
                                "type": "text",
                                "value": "The Bar fighters"
                            },
                            {
                                "name": "price",
                                "type": "number",
                                "value": "62.0"
                            }
                        ]
                    }
                ],
                "rel": ["items"]
            },
            {
                "properties": {
                    "id_": "item03",
                    "name": "Baz",
                    "description": "There goes my baz",
                    "price": 50.2
                },
                "links": [
                    {
                        "rel": ["self"],
                        "href": "/items/item03"
                    }
                ],
                "actions": [
                    {
                        "name": "update",
                        "method": "PUT",
                        "href": "/items/item03",
                        "type": "application/x-www-form-urlencoded",
                        "fields": [
                            {
                                "name": "name",
                                "type": "text",
                                "value": "Baz"
                            },
                            {
                                "name": "description",
                                "type": "text",
                                "value": "There goes my baz"
                            },
                            {
                                "name": "price",
                                "type": "number",
                                "value": "50.2"
                            }
                        ]
                    }
                ],
                "rel": ["items"]
            },
            {
                "properties": {
                    "id_": "item04",
                    "name": "Doe",
                    "description": "There goes my Doe",
                    "price": 5.0
                },
                "links": [
                    {
                        "rel": ["self"],
                        "href": "/items/item04"
                    }
                ],
                "actions": [
                    {
                        "name": "update",
                        "method": "PUT",
                        "href": "/items/item04",
                        "type": "application/x-www-form-urlencoded",
                        "fields": [
                            {
                                "name": "name",
                                "type": "text",
                                "value": "Doe"
                            },
                            {
                                "name": "description",
                                "type": "text",
                                "value": "There goes my Doe"
                            },
                            {
                                "name": "price",
                                "type": "number",
                                "value": "5.0"
                            }
                        ]
                    }
                ],
                "rel": ["items"]
            }
        ],
        "links": [
            {
                "rel": ["self"],
                "href": "/items"
            }
        ],
        "actions": [
            {
                "name": "find",
                "method": "GET",
                "href": "/items/{id_}",
                "templated": true
            },
            {
                "name": "update",
                "method": "PUT",
                "href": "/items/{id_}",
                "type": "application/x-www-form-urlencoded",
                "fields": [
                    {
                        "name": "name",
                        "type": "text",
                        "value": "None"
                    },
                    {
                        "name": "description",
                        "type": "text",
                        "value": "None"
                    },
                    {
                        "name": "price",
                        "type": "number",
                        "value": "None"
                    }
                ],
                "templated": true
            }
        ]
    }
    ```

## Installation

`pip install fastapi-hypermodel`

## Limitations

Currently, query parameters will not resolve correctly. When generating a
resource URL, ensure all parameters passed are path parameters, not query
parameters.

This is an upstream issue, being tracked
[here](https://github.com/encode/starlette/issues/560).

## Attributions

Some functionality is based on
[Flask-Marshmallow](https://github.com/marshmallow-code/flask-marshmallow/blob/dev/src/flask_marshmallow/fields.py)
`URLFor` class.

