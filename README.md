# FastAPI-HyperModel

FastAPI-HyperModel is a FastAPI + Pydantic extension for simplifying hypermedia-driven API development. This module adds a new Pydantic model base-class, supporting dynamic `href` generation based on object data.

## Installation

`pip install fastapi-hypermodel`

## Basic Usage

### Import `HyperModel` and optionally `HyperRef`

```python
from fastapi import FastAPI

from fastapi_hypermodel import HyperModel, UrlFor
```

`HyperModel` will be your model base-class.

### Create your basic models

We'll create two models, a brief item summary including ID, name, and a link, and a full model containing additional information. We'll use `ItemSummary` in our item list, and `ItemDetail` for full item information.

```python
class ItemSummary(HyperModel):
    id: str
    name: str

class ItemDetail(ItemSummary):
    description: Optional[str] = None
    price: float

class Person(HyperModel):
    name: str
    id: str
    items: List[ItemSummary]
```

### Create and attach your app

We'll now create our FastAPI app, and bind it to our `HyperModel` base class.

```python
from fastapi import FastAPI

app = FastAPI()
HyperModel.init_app(app)
```

### Add some API views

We'll create an API view for a list of items, as well as details about an individual item. Note that we pass the item ID with our `{item_id}` URL variable.

```python
@app.get("/items", response_model=List[ItemSummary])
def read_items():
    return list(items.values())

@app.get("/items/{item_id}", response_model=ItemDetail)
def read_item(item_id: str):
    return items[item_id]

@app.get("/people/{person_id}", response_model=Person)
def read_person(person_id: str):
    return people[person_id]

@app.get("/people/{person_id}/items", response_model=List[ItemDetail])
def read_person_items(person_id: str):
    return people[person_id]["items"]
```

### Create a model `href`

We'll now go back and add an `href` field with a special `UrlFor` value. This `UrlFor` class defines how our href elements will be generated. We'll change our `ItemSummary` class to:

```python
class ItemSummary(HyperModel):
    name: str
    id: str
    href = UrlFor("read_item", {"item_id": "<id>"})
```

The `UrlFor` class takes two arguments:

#### `endpoint`

Name of your FastAPI endpoint function you want to link to. In our example, we want our item summary to link to the corresponding item detail page, which maps to our `read_item` function.

#### `values` (optional depending on endpoint)

Same keyword arguments as FastAPI's url_path_for, except string arguments enclosed in < > will be interpreted as attributes to pull from the object. For example, here we need to pass an `item_id` argument as required by our endpoint function, and we want to populate that with our item object's `id` attribute.

### Create a link set

In some cases we want to create a map of relational links. In these cases we can create a `LinkSet` field describing each link and it's relationship to the object.

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

### Putting it all together

For this example, we can make a dictionary containing some fake data, and add extra models, even nesting models if we want. A complete example based on this documentation can be found [here](examples/simple_app.py).

If we run the example application and go to our `/items` URL, we should get a response like:

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

## Attributions

Some functionality is based on [Flask-Marshmallow](https://github.com/marshmallow-code/flask-marshmallow/blob/dev/src/flask_marshmallow/fields.py) `URLFor` class.
