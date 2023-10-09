from typing import List, Optional

from fastapi import FastAPI

from fastapi_hypermodel import HyperModel, LinkSet, UrlFor

# Create our FastAPI app
app = FastAPI()
# Attach our HyperModel base class to our app
HyperModel.init_app(app)


# Create a Pydantic model for our Item resources
class ItemSummary(HyperModel):
    name: str
    id: str
    # This is a dynamic link to the Item resource
    href: UrlFor = UrlFor("read_item", {"item_id": "<id>"})


# Extended model for our Item resources, including extra details
class Item(ItemSummary):
    description: Optional[str] = None
    price: float


# Create a Pydantic model for our Person resources
class Person(HyperModel):
    name: str
    id: str
    items: List[ItemSummary]

    # Single link attribute
    href: UrlFor = UrlFor("read_person", {"person_id": "<id>"})

    # Link set attribute
    # For larger APIs, this tends to be more useful as it allows you to easily
    # generate a list of links for all the sub-resources of a resource
    links: LinkSet = LinkSet(
        {
            "self": UrlFor("read_person", {"person_id": "<id>"}),
            "items": UrlFor("read_person_items", {"person_id": "<id>"}),
        }
    )


# Create some test data for our API to return
items = {
    "item01": {"id": "item01", "name": "Foo", "price": 50.2},
    "item02": {
        "id": "item02",
        "name": "Bar",
        "description": "The Bar fighters",
        "price": 62,
    },
    "item03": {
        "id": "item03",
        "name": "Baz",
        "description": "There goes my baz",
        "price": 50.2,
    },
}

people = {
    "person01": {
        "id": "person01",
        "name": "Alice",
        "items": [items["item01"], items["item02"]],
    },
    "person02": {"id": "person02", "name": "Bob", "items": [items["item03"]]},
}

# Create our API routes, using our Pydantic models as respone_model


@app.get("/items", response_model=List[ItemSummary])
def read_items():
    return list(items.values())


@app.get("/items/{item_id}", response_model=Item)
def read_item(item_id: str):
    return items[item_id]


@app.get("/people", response_model=List[Person])
def read_people():
    return list(people.values())


@app.get("/people/{person_id}", response_model=Person)
def read_person(person_id: str):
    return people[person_id]


@app.get("/people/{person_id}/items", response_model=List[ItemSummary])
def read_person_items(person_id: str):
    return people[person_id]["items"]


# Run the app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
