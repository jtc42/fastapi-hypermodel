# Advanced Usage

##  Conditional Links

It is possible to add additional field-value-dependent conditions on links. For example, you may want certain links within a set to only appear if the application or session is in a state that allows that interaction.

Let's begin with our `Person` example from earlier.

```python
class Person(HyperModel):
    id: str
    name: str
    items: List[ItemSummary]

    href = UrlFor("read_person", {"person_id": "<id>"})
    links = LinkSet(
        {
            "self": UrlFor("read_person", {"person_id": "<id>"}),
            "items": UrlFor("read_person_items", {"person_id": "<id>"}),
        }
    )
```

We may want a new link that corresponds to adding a new Item to the Person.

```python hl_lines="11"
class Person(HyperModel):
    id: str
    name: str
    items: List[ItemSummary]

    href = UrlFor("read_person", {"person_id": "<id>"})
    links = LinkSet(
        {
            "self": UrlFor("read_person", {"person_id": "<id>"}),
            "items": UrlFor("read_person_items", {"person_id": "<id>"}),
            "addItem": UrlFor("put_person_items", {"person_id": "<id>"},),
        }
    )
```

However, we may want functionality where a Person can be "locked", and no new items added. We add a new field `is_locked` to our model.

```python hl_lines="4"
class Person(HyperModel):
    id: str
    name: str
    is_locked: bool
    items: List[ItemSummary]

    href = UrlFor("read_person", {"person_id": "<id>"})
    links = LinkSet(
        {
            "self": UrlFor("read_person", {"person_id": "<id>"}),
            "items": UrlFor("read_person_items", {"person_id": "<id>"}),
            "addItem": UrlFor("put_person_items", {"person_id": "<id>"},),
        }
    )
```

Now, if the Person is locked, the `addItem` link is no longer relevant. Querying it will result in a denied error, and so we *may* choose to remove it from the link set.
To do this, we will add a field-dependent condition to the link.

```python hl_lines="15"
class Person(HyperModel):
    id: str
    name: str
    is_locked: bool
    items: List[ItemSummary]

    href = UrlFor("read_person", {"person_id": "<id>"})
    links = LinkSet(
        {
            "self": UrlFor("read_person", {"person_id": "<id>"}),
            "items": UrlFor("read_person_items", {"person_id": "<id>"}),
            "addItem": UrlFor(
                "put_person_items",
                {"person_id": "<id>"},
                condition=lambda values: not values["is_locked"],
            ),
        }
    )
```

The `condition` argument takes a callable, which will be passed dict containing the name-to-value mapping of all fields on the parent `HyperModel` instance.
In this example, we use a lambda function that returns `True` or `False` depending on the value `is_locked` of the parent `HyperModel` instance.

!!! note
    Conditional links will *always* show up in the auto-generated OpenAPI/Swagger documentation.
    These conditions *only* apply to the hypermedia fields generated at runtime.



=== "URLFor"

    ```python
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

    ```python
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

    ```python
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
                condition=lambda values: not values["is_locked"],
                name="add_item",
                populate_fields=False,
            ),
        )
    ```

## Response for unlocked Person

=== "URLFor"

    ```json
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

    ```json
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

    ```json
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


## Response for locked Person

=== "URLFor"

    ```json
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

    ```json
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

    ```json
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