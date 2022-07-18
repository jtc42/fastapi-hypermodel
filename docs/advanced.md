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
