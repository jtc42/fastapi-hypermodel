#  Basic Usage

## Choose Hypermedia Formats

Fastapi-hypermodel has support for following [Hypermedia Maturity Model
Levels](https://8thlight.com/insights/the-hypermedia-maturity-model):

- Level 0: URLFor - Plain Text
- Level 1: [Hypertext Application Language (HAL)](https://datatracker.ietf.org/doc/html/draft-kelly-json-hal)
- Level 2: [Siren](https://github.com/kevinswiber/siren)

There is a fully working example for each format in the
[examples](https://github.com/jtc42/fastapi-hypermodel/tree/main/examples)
directory.

## Initialization

=== "URLFor"

    ```python linenums="1"
    from fastapi import FastAPI

    from fastapi_hypermodel import HyperModel, UrlFor
    ```

=== "HAL"

    ```python linenums="1"
    from fastapi import FastAPI

    from fastapi_hypermodel import (
        FrozenDict,
        HALFor,
        HALHyperModel,
        HALLinks,
        HALResponse,
    )
    ```

=== "Siren"

    ```python linenums="1"
    from fastapi import FastAPI

    from fastapi_hypermodel import (
        SirenActionFor,
        SirenHyperModel,
        SirenLinkFor,
        SirenResponse,
    )
    ```

## Create Basic Models

Two showcase the hypermedia feature, an `Item` model will be used. Each item
will have an `id_`, a `name`, an optional `description` and a `price`. Moreover
a `ItemCollection` will also be defined to return multiple items. Two hypermedia
references will be used, one called `self` (`href` in the case of `URLFor`) and
an `update`.

All formats support "links", that is, plain references of HTTP URIs fetchable
via GET. Moreover, Level 2 formats (SIREN) support "actions", which also specify
the HTTP method and the fields needed.

Even though not part of the standard, fastapi-hypermodel provides support for
"templated URIs". Allowing the client to form the URI with information from the
selected resource. This is useful when returning collections.

!!! info

    The reason to define two classes `ItemSummary` and `Item` is to enable using
    a lightweight version (`ItemSummary`) for nested objects 


=== "URLFor"

    ```python linenums="1"
    class ItemSummary(HyperModel):
        id_: str
        name: str

        href: UrlFor = UrlFor("read_item", {"id_": "<id_>"})
        update: UrlFor = UrlFor("update_item", {"id_": "<id_>"})

    class Item(ItemSummary):
        description: Optional[str] = None
        price: float

    class ItemCollection(HyperModel):
        items: Sequence[Item]

        href: UrlFor = UrlFor("read_items")
        find: UrlFor = UrlFor("read_item", templated=True)
        update: UrlFor = UrlFor("update_item", templated=True)
    ```

=== "HAL"

    ```python linenums="1"
    class ItemSummary(HALHyperModel):
        id_: str
        name: str

        links: HALLinks = FrozenDict({
            "self": HALFor("read_item", {"id_": "<id_>"}),
            "update": HALFor("update_item", {"id_": "<id_>"}),
        })

    class Item(ItemSummary):
        description: Optional[str] = None
        price: float

    class ItemCollection(HALHyperModel):
        items: Sequence[Item] = Field(alias="sc:items")

        links: HALLinks = FrozenDict({
            "self": HALFor("read_items"),
            "find": HALFor("read_item", templated=True),
            "update": HALFor("update_item", templated=True),
        })
    ```

=== "Siren"

    ```python linenums="1"
    class ItemSummary(SirenHyperModel):
        id_: str
        name: str

        links: Sequence[SirenLinkFor] = (
            SirenLinkFor("read_item", {"id_": "<id_>"}, rel=["self"]),
        )

        actions: Sequence[SirenActionFor] = (
            SirenActionFor("update_item", {"id_": "<id_>"}, name="update"),
        )


    class Item(ItemSummary):
        description: Optional[str] = None
        price: float

    class ItemCollection(SirenHyperModel):
        items: Sequence[Item]

        links: Sequence[SirenLinkFor] = (SirenLinkFor("read_items", rel=["self"]),)

        actions: Sequence[SirenActionFor] = (
            SirenActionFor("read_item", templated=True, name="find"),
            SirenActionFor("update_item", templated=True, name="update"),
        )
    ```

## Define your data

Before defining the app and the endpoints, sample data should be defined. In
this case all formats will use the same data.

In the case of HAL, to showcase the "cURIes" feature the data will change and
use `sc:items` instead of `items` as the key. At the moment only HAL supports
"cURIes" as part of the standard.

It is important to note that none of the additional fields added to the response
at runtime are leaked into the data implementation. Therefore, the hypermedia
format and the data model are totally decoupled, granting great flexibility.

=== "URLFor"

    ```python linenums="1"
    from typing import List

    from typing_extensions import NotRequired, TypedDict


    class Item(TypedDict):
        id_: str
        name: str
        price: float
        description: NotRequired[str]


    class Items(TypedDict):
        items: List[Item]


    items: Items = {
        "items": [
            {
                "id_": "item01",
                "name": "Foo",
                "price": 10.2
            },
            {
                "id_": "item02",
                "name": "Bar",
                "description": "The Bar fighters",
                "price": 62,
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
                "price": 5,
            },
        ]
    }
    ```

=== "HAL"

    ```python linenums="1"
    from typing import List

    from typing_extensions import NotRequired, TypedDict

    from fastapi_hypermodel import HALForType, UrlType


    class Item(TypedDict):
        id_: str
        name: str
        price: float
        description: NotRequired[str]


    Items = TypedDict("Items", {"sc:items": List[Item]})

    items: Items = {
        "sc:items": [
            {
                "id_": "item01",
                "name": "Foo",
                "price": 10.2
            },
            {
                "id_": "item02",
                "name": "Bar",
                "description": "The Bar fighters",
                "price": 62,
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
                "price": 5,
            },
        ]
    }

    curies: List[HALForType] = [
        HALForType(
            href=UrlType("https://schema.org/{rel}"),
            name="sc",
            templated=True,
        )
    ]
    ```

=== "Siren"

    ```python linenums="1"
    from typing import List

    from typing_extensions import NotRequired, TypedDict


    class Item(TypedDict):
        id_: str
        name: str
        price: float
        description: NotRequired[str]


    class Items(TypedDict):
        items: List[Item]


    items: Items = {
        "items": [
            {
                "id_": "item01",
                "name": "Foo",
                "price": 10.2
            },
            {
                "id_": "item02",
                "name": "Bar",
                "description": "The Bar fighters",
                "price": 62,
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
                "price": 5,
            },
        ]
    }
    ```


## Create and Attach App

To make the app "hypermedia-aware", it is enough to initiliaze the format's
HyperModel class with the app object. 

!!! warning

    At the moment this is handled by class variables so it is not thread-safe to
    have multiple apps.

=== "URLFor"

    ```python linenums="1"
    app = FastAPI()
    HyperModel.init_app(app)
    ```

=== "HAL"

    ```python linenums="1"
    app = FastAPI()
    HALHyperModel.init_app(app)
    HALHyperModel.register_curies(curies)
    ```

=== "Siren"

    ```python linenums="1"
    app = FastAPI()
    SirenHyperModel.init_app(app)
    ```

## Add API Endpoints

To expose the data via endpoints, they are defined as usual in any FastAPI app.
The `response_model` and `response_class` need to be defined when appropiate.

All formats are compatible with path parameters. In the case of Level 2 formats
(SIREN), it can auto detect path and body parameters as well. Query parameters
are not well supported yet.

=== "URLFor"

    ```python linenums="1"
    @app.get("/items", response_model=ItemCollection)
    def read_items() -> Any:
        return items

    @app.get("/items/{id_}", response_model=Item)
    def read_item(id_: str) -> Any:
        return next(item for item in items["items"] if item["id_"] == id_)
    ```

=== "HAL"

    ```python linenums="1"
    @app.get("/items", response_model=ItemCollection, response_class=HALResponse)
    def read_items() -> Any:
        return items

    @app.get("/items/{id_}", response_model=Item, response_class=HALResponse)
    def read_item(id_: str) -> Any:
        return next(item for item in items["sc:items"] if item["id_"] == id_)
    ```

=== "Siren"

    ```python linenums="1" 
    @app.get("/items", response_model=ItemCollection, response_class=SirenResponse)
    def read_items() -> Any:
        return items

    @app.get("/items/{id_}", response_model=Item, response_class=SirenResponse)
    def read_item(id_: str) -> Any:
        return next(item for item in items["items"] if item["id_"] == id_)
    ```


## Responses

The response generated by each format varies based on their specification. Using
hypermedia usually results in heavier responses because of all the additional
information provided.

!!! warning

    At the moment no optimizations are done under the hood to minimize the size 
    of the response. For instance, one such optimization could be removing 
    cURIes in HAL if they are already defined in a parent.

    Beware of highly nested objects.


### Fetching /items/item01


=== "URLFor"

    ```json linenums="1"
    {
        "id_": "item01",
        "name": "Foo",
        "price": 10.2,

        "href": "/items/item01",
        "update": "/items/item01"
    }
    ```

=== "HAL"

    ```json linenums="1"
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

=== "Siren"

    ```json linenums="1"
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

### Fetching /items


=== "URLFor"

    ```json linenums="1"
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

=== "HAL"

    ```json linenums="1"
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

=== "Siren"

    ```json linenums="1"
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
