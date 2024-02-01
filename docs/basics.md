#  Basic Usage

## Choose Hypermedia Formats

Fastapi-hypermodel has support for following [Hypermedia Maturity Model
Levels](https://8thlight.com/insights/the-hypermedia-maturity-model):

- Level 0: URLFor - Plain Text
- Level 1: [Hypertext Application Language (HAL)](https://datatracker.ietf.org/doc/html/draft-kelly-json-hal)
- Level 2: [Siren](https://github.com/kevinswiber/siren)

There is a fully working example for each format in the [examples](../examples)
directory.

## Initialization

=== "URLFor"

    ```python
    from fastapi import FastAPI

    from fastapi_hypermodel import HyperModel, UrlFor
    ```

=== "HAL"

    ```python
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

    ```python
    from fastapi import FastAPI

    from fastapi_hypermodel import (
        SirenActionFor,
        SirenHyperModel,
        SirenLinkFor,
        SirenResponse,
    )
    ```

## Create your basic models

We'll create two models, a brief item summary including ID, name, and a link,
and a full model containing additional information. We'll use `ItemSummary` in
our item list, and `ItemDetail` for full item information.


=== "URLFor"

    ```python
    class ItemSummary(HyperModel):
        name: str
        id_: str

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

    ```python
    class ItemSummary(HALHyperModel):
        name: str
        id_: str

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

    ```python
    class ItemSummary(SirenHyperModel):
        name: str
        id_: str

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

=== "URLFor"

    ```python
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
            {"id_": "item01", "name": "Foo", "price": 50.2},
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

    ```python
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
            {"id_": "item01", "name": "Foo", "price": 10.2},
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

    ```python
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
            {"id_": "item01", "name": "Foo", "price": 10.2},
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


## Create and attach your app

We'll now create our FastAPI app, and bind it to our `HyperModel` base class.

=== "URLFor"

    ```python
    app = FastAPI()
    HyperModel.init_app(app)
    ```

=== "HAL"

    ```python
    app = FastAPI()
    HALHyperModel.init_app(app)
    HALHyperModel.register_curies(curies)
    ```

=== "Siren"

    ```python
    app = FastAPI()
    SirenHyperModel.init_app(app)
    ```

## Add some API views

We'll create an API view for a list of items, as well as details about an
individual item. Note that we pass the item ID with our `{item_id}` URL
variable.

=== "URLFor"

    ```python
    @app.get("/items", response_model=ItemCollection)
    def read_items() -> Any:
        return items

    @app.get("/items/{id_}", response_model=Item)
    def read_item(id_: str) -> Any:
        return next(item for item in items["items"] if item["id_"] == id_)
    ```

=== "HAL"

    ```python
    @app.get("/items", response_model=ItemCollection, response_class=HALResponse)
    def read_items() -> Any:
        return items

    @app.get("/items/{id_}", response_model=Item, response_class=HALResponse)
    def read_item(id_: str) -> Any:
        return next(item for item in items["sc:items"] if item["id_"] == id_)
    ```

=== "Siren"

    ```python
    @app.get("/items", response_model=ItemCollection, response_class=SirenResponse)
    def read_items() -> Any:
        return items

    @app.get("/items/{id_}", response_model=Item, response_class=SirenResponse)
    def read_item(id_: str) -> Any:
        return next(item for item in items["items"] if item["id_"] == id_)
    ```

## Create a model `href`

We'll now go back and add an `href` field with a special `UrlFor` value. This
`UrlFor` class defines how our href elements will be generated. We'll change our
`ItemSummary` class to:

```python
class ItemSummary(HyperModel):
    name: str
    id: str
    href = UrlFor("read_item", {"item_id": "<id>"})
```

The `UrlFor` class takes two arguments:

### `endpoint`

Name of your FastAPI endpoint function you want to link to. In our example, we
want our item summary to link to the corresponding item detail page, which maps
to our `read_item` function.

Alternatively, rather than providing the endpoint name, you can provide a
reference to the endpoint function itself, for example `UrlFor(read_item,
{"item_id": "<id>"})`. This can help with larger projects where function names
may be refactored.

### `values` (optional depending on endpoint)

Same keyword arguments as FastAPI's url_path_for, except string arguments
enclosed in < > will be interpreted as attributes to pull from the object. For
example, here we need to pass an `item_id` argument as required by our endpoint
function, and we want to populate that with our item object's `id` attribute.

## Create a link set

In some cases we want to create a map of relational links. In these cases we can
create a `LinkSet` field describing each link and it's relationship to the
object. The `LinkSet` class is really just a spicy dictionary that tells the
parent `HyperModel` to "render" each link in the link set, and includes some
extra OpenAPI schema stuff.

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

## Putting it all together

For this example, we can make a dictionary containing some fake data, and add
extra models, even nesting models if we want. A complete example based on this
documentation can be found
[here](https://github.com/jtc42/fastapi-hypermodel/blob/main/examples/simple_app.py).

If we run the example application and go to our `/items` URL, we should get a
response like:

```json
[
  {
    "name": "Foo",
    "id": "item01",
    "href": "/items/item01"
  },
  {
    "name": "Bar",
    "id": "item02",
    "href": "/items/item02"
  },
  {
    "name": "Baz",
    "id": "item03",
    "href": "/items/item03"
  }
]
```




=== "URLFor"

    ```python

    ```

=== "HAL"

    ```python

    ```

=== "Siren"

    ```python

    ```