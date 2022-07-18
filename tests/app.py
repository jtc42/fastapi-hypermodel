from typing import List, Optional

from fastapi import FastAPI
from pydantic.main import BaseModel

from fastapi_hypermodel import HyperModel, UrlFor, LinkSet
from fastapi_hypermodel.hypermodel import HALFor


class ItemSummary(HyperModel):
    name: str
    id: str

    href = UrlFor("read_item", {"item_id": "<id>"})


class ItemDetail(ItemSummary):
    description: Optional[str] = None
    price: float


class ItemUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    price: Optional[float]


class ItemCreate(ItemUpdate):
    id: str


class Person(HyperModel):
    name: str
    id: str
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

    hal_href = HALFor("read_person", {"person_id": "<id>"})
    hal_links = LinkSet(
        {
            "self": HALFor("read_person", {"person_id": "<id>"}),
            "items": HALFor("read_person_items", {"person_id": "<id>"}),
            "addItem": HALFor(
                "put_person_items",
                {"person_id": "<id>"},
                description="Add an item to this person and the items list",
                condition=lambda values: not values["is_locked"],
            ),
        }
    )

    class Config:
        # Alias hal_links to _links as per the HAL standard
        fields = {"hal_links": "_links"}


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
        "is_locked": False,
        "items": [items["item01"], items["item02"]],
    },
    "person02": {
        "id": "person02",
        "name": "Bob",
        "is_locked": True,
        "items": [items["item03"]],
    },
}


def create_app():
    app = FastAPI()
    HyperModel.init_app(app)

    @app.get(
        "/items",
        response_model=List[ItemSummary],
    )
    def read_items():
        return list(items.values())

    @app.get("/items/{item_id}", response_model=ItemDetail)
    def read_item(item_id: str):
        return items[item_id]

    @app.put("/items/{item_id}", response_model=ItemDetail)
    def update_item(item_id: str, item: ItemUpdate):
        items[item_id].update(item.dict(exclude_none=True))
        return items[item_id]

    @app.get(
        "/people",
        response_model=List[Person],
    )
    def read_people():
        return list(people.values())

    @app.get("/people/{person_id}", response_model=Person)
    def read_person(person_id: str):
        return people[person_id]

    @app.get("/people/{person_id}/items", response_model=List[ItemDetail])
    def read_person_items(person_id: str):
        return people[person_id]["items"]

    @app.put("/people/{person_id}/items", response_model=List[ItemDetail])
    def put_person_items(person_id: str, item: ItemCreate):
        items[item.id] = item.dict()
        people[person_id]["items"].append(item.dict())
        return people[person_id]["items"]

    return app
