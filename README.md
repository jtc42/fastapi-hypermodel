# FastAPI-HyperModel

FastAPI-HyperModel is a FastAPI + Pydantic extension for simplifying hypermedia-driven API development. This module adds a new Pydantic model base-class, supporting dynamic `href` generation based on object data.

## Installation

`pip install fastapi-hypermodel`

## Basic Usage

### Import `HyperModel` and optionally `HyperRef`

```python
from fastapi import FastAPI

from fastapi_hypermodel import HyperModel, HyperRef
```

`HyperModel` will be your model base-class, and `HyperRef` is just a type alias for `Optional[pydantic.AnyUrl]`

### Create your basic models

We'll create two models, a brief item summary including ID, name, and a link, and a full model containing additional information. We'll use `ItemSummary` in our item list, and `ItemDetail` for full item information.

```python
class ItemSummary(HyperModel):
    id: str
    name: str
    href: HyperRef

class ItemDetail(ItemSummary):
    description: Optional[str] = None
    price: float
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
```

### Configure our model Hrefs

We'll now go back and add a special configuration class to our models. This class defines how our href elements will be generated. We'll change our `ItemSummary` class to:

```python
class ItemSummary(HyperModel):
    id: str
    name: str
    href: HyperRef

    class Href:
        endpoint = "read_item"  # FastAPI endpoint we want to link to
        field = "href"  # Which field should hold our URL
        values = {"item_id": "<id>"}  # Map object attributes to URL variables
```

We need to create a child class named `Href` containing three important attributes:

#### `endpoint`

Name of your FastAPI endpoint function you want to link to. In our example, we want our item summary to link to the corresponding item detail page, which maps to our `read_item` function.

#### `field` (optional)

Determines which field the generated URL should be assigned to. This is an optional property and will default to "href". Note, if the selected field is not defined by your schema, the link will not be generated.

#### `values` (optional depending on endpoint)

Same keyword arguments as FastAPI's url_path_for, except string arguments enclosed in < > will be interpreted as attributes to pull from the object. For example, here we need to pass an `item_id` argument as required by our endpoint function, and we want to populate that with our item object's `id` attribute.

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

## To-do

- [ ] Proper unit tests
