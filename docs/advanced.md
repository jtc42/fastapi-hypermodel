# Advanced Usage

In addition to what the standard for the format defines, fastapi-hypermodel has
some additional features, such as conditional links.

##  Conditional Links

It is possible to add additional field-value-dependent conditions on links. For
example, you may want certain links within a set to only appear if the
application or session is in a state that allows that interaction.

A new model `Person` is defined below, a person has an `id`, a `name` and a
collection of `items`. Moreover, a person could be locked, meaning no new items
could be added, this is modeled by the `is_locked` flag. Each `Person` has three
references, `self` (`href` for `URLFor`), `update` and `add_item`.


The `condition` argument takes a callable, which will be passed a dict
containing the name-to-value mapping of all fields on the base `HyperModel`
instance. In this example, a lambda function that returns `True` or `False`
depending on the value `is_locked` of `HyperModel` instance.

!!! note
    Conditional links will *always* show up in the auto-generated OpenAPI/Swagger
    documentation. These conditions *only* apply to the hypermedia fields
    generated at runtime.


=== "URLFor"

    ```python linenums="1" hl_lines="13"
    class Person(HyperModel): 
        id_: str
        name: str
        is_locked: bool

        items: Sequence[Item]

        href: UrlFor = UrlFor("read_person", {"id_": "<id_>"})
        update: UrlFor = UrlFor("update_person", {"id_": "<id_>"})
        add_item: UrlFor = UrlFor(
            "put_person_items",
            {"id_": "<id_>"},
            condition=lambda values: not values["is_locked"],
        )
    ```

=== "HAL"

    ```python linenums="1" hl_lines="14"
    class Person(HALHyperModel):
        id_: str
        name: str
        is_locked: bool

        items: Sequence[Item] = Field(alias="sc:items")

        links: HALLinks = FrozenDict({
            "self": HALFor("read_person", {"id_": "<id_>"}),
            "update": HALFor("update_person", {"id_": "<id_>"}),
            "add_item": HALFor(
                "put_person_items",
                {"id_": "<id_>"},
                condition=lambda values: not values["is_locked"],
            ),
        })
    ```

=== "Siren"

    ```python linenums="1" hl_lines="19"
    class Person(SirenHyperModel):
        id_: str
        name: str
        is_locked: bool

        items: Sequence[Item]

        links: Sequence[SirenLinkFor] = (
            SirenLinkFor("read_person", {"id_": "<id_>"}, rel=["self"]),
        )

        actions: Sequence[SirenActionFor] = (
            SirenActionFor("update_person", {"id_": "<id_>"}, name="update"),
            SirenActionFor(
                "put_person_items",
                {"id_": "<id_>"},
                name="add_item",
                populate_fields=False,
                condition=lambda values: not values["is_locked"],
            ),
        )
    ```


### Response for locked Person

=== "URLFor"

    ```json linenums="1"
    {
        "id_": "person02",
        "name": "Bob",
        "is_locked": true,

        "items": [
            {
                "id_": "item03",
                "name": "Baz",
                "href": "/items/item03",
                "update": "/items/item03",
                "description": "There goes my baz",
                "price": 50.2
            },
            {
                "id_": "item04",
                "name": "Doe",
                "href": "/items/item04",
                "update": "/items/item04",
                "description": "There goes my Doe",
                "price": 5.0
            }
        ],

        "href": "/people/person02",
        "update": "/people/person02"
    }
    ```

=== "HAL"

    ```json linenums="1"
    {
        "id_": "person02",
        "name": "Bob",
        "is_locked": true,

        "_embedded": {
            "sc:items": [
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
                "href": "/people/person02"
            },
            "update": {
                "href": "/people/person02"
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
        "properties": {
            "id_": "person02",
            "name": "Bob",
            "is_locked": true
        },
        "entities": [
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
                "href": "/people/person02"
            }
        ],
        "actions": [
            {
                "name": "update",
                "method": "PUT",
                "href": "/people/person02",
                "type": "application/x-www-form-urlencoded",
                "fields": [
                    {
                        "name": "name",
                        "type": "text",
                        "value": "Bob"
                    },
                    {
                        "name": "is_locked",
                        "type": "text",
                        "value": "True"
                    }
                ]
            }
        ]
    }
    ```

### Response for unlocked Person

=== "URLFor"

    ```json linenums="1" hl_lines="27"
    {
        "id_": "person01",
        "name": "Alice",
        "is_locked": false,

        "items": [
            {
                "id_": "item01",
                "name": "Foo",
                "href": "/items/item01",
                "update": "/items/item01",
                "description": null,
                "price": 50.2
            },
            {
                "id_": "item02",
                "name": "Bar",
                "href": "/items/item02",
                "update": "/items/item02",
                "description": "The Bar fighters",
                "price": 62.0
            }
        ],

        "href": "/people/person01",
        "update": "/people/person01",
        "add_item": "/people/person01/items"
    }
    ```

=== "HAL"

    ```json linenums="1" hl_lines="61-63"
    {
        "id_": "person01",
        "name": "Alice",
        "is_locked": false,

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
                }
            ]
        },
        "_links": {
            "self": {
                "href": "/people/person01"
            },
            "update": {
                "href": "/people/person01"
            },
            "add_item": {
                "href": "/people/person01/items"
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

    ```json linenums="1" hl_lines="114-126"
    {
        "properties": {
            "id_": "person01",
            "name": "Alice",
            "is_locked": false
        },
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
            }
        ],
        "links": [
            {
                "rel": ["self"],
                "href": "/people/person01"
            }
        ],
        "actions": [
            {
                "name": "update",
                "method": "PUT",
                "href": "/people/person01",
                "type": "application/x-www-form-urlencoded",
                "fields": [
                    {
                        "name": "name",
                        "type": "text",
                        "value": "Alice"
                    },
                    {
                        "name": "is_locked",
                        "type": "text",
                        "value": "None"
                    }
                ]
            },
            {
                "name": "add_item",
                "method": "PUT",
                "href": "/people/person01/items",
                "type": "application/x-www-form-urlencoded",
                "fields": [
                    {
                        "name": "id_",
                        "type": "text"
                    }
                ]
            }
        ]
    }
    ```