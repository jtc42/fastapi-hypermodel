from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from pydantic import Field
from pydantic.main import BaseModel

from examples.hal.data import items, people
from fastapi_hypermodel import HALFor, HyperModel, LinkSet


class ItemSummary(HyperModel):
    name: str
    id_: str

    links: LinkSet = Field(
        default=LinkSet({
            "self": HALFor("read_item", {"id_": "<id_>"}),
            "update": HALFor("update_item", {"id_": "<id_>"}),
        }),
        alias="_links",
    )


class Item(ItemSummary):
    description: Optional[str] = None
    price: float


class ItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None


class ItemCreate(ItemUpdate):
    id_: str


class ItemCollection(HyperModel):
    links: LinkSet = Field(
        default=LinkSet({
            "self": HALFor("read_items"),
            "find": HALFor("read_item", template=True),
            "update": HALFor("update_item", template=True),
        }),
        alias="_links",
    )

    embedded: Dict[str, List[Item]] = Field(alias="_embedded")


class Person(HyperModel):
    name: str
    id_: str
    is_locked: bool

    links: LinkSet = Field(
        default=LinkSet({
            "self": HALFor("read_person", {"id_": "<id_>"}),
            "update": HALFor("update_person", {"id_": "<id_>"}),
            "add_item": HALFor(
                "put_person_items",
                {"id_": "<id_>"},
                description="Add an item to this person and the items list",
                condition=lambda values: not values["is_locked"],
            ),
        }),
        alias="_links",
    )

    embedded: Dict[str, List[Item]] = Field(alias="_embedded")


class PersonCollection(HyperModel):
    links: LinkSet = Field(
        default=LinkSet({
            "self": HALFor("read_people"),
            "find": HALFor(
                "read_person", description="Get a particular person", template=True
            ),
            "update": HALFor(
                "update_person",
                description="Update a particular person",
                template=True,
            ),
        }),
        alias="_links",
    )

    embedded: Dict[str, List[Person]] = Field(alias="_embedded")


class PersonUpdate(BaseModel):
    name: Optional[str] = None
    is_locked: Optional[bool] = None


app = FastAPI()
HyperModel.init_app(app)


@app.get("/items", response_model=ItemCollection)
def read_items() -> Any:
    return items


@app.get("/items/{id_}", response_model=Item)
def read_item(id_: str) -> Any:
    return next(item for item in items["_embedded"]["items"] if item.get("id_") == id_)


@app.put("/items/{id_}", response_model=Item)
def update_item(id_: str, item: ItemUpdate) -> Any:
    base_item = next(
        item for item in items["_embedded"]["items"] if item.get("id_") == id_
    )
    base_item.update(item.model_dump(exclude_none=True))
    return base_item


@app.get("/people", response_model=PersonCollection)
def read_people() -> Any:
    return people


@app.get("/people/{id_}", response_model=Person)
def read_person(id_: str) -> Any:
    return next(
        person for person in people["_embedded"]["people"] if person.get("id_") == id_
    )


@app.put("/people/{id_}", response_model=Person)
def update_person(id_: str, person: PersonUpdate) -> Any:
    base_person = next(
        person for person in people["_embedded"]["people"] if person.get("id_") == id_
    )
    base_person.update(person.model_dump(exclude_none=True))
    return base_person


@app.put("/people/{id_}/items", response_model=List[Item])
def put_person_items(id_: str, item: ItemCreate) -> Any:
    complete_item = next(
        (
            item_
            for item_ in items["_embedded"]["items"]
            if item_.get("id_") == item.id_
        ),
        None,
    )
    if not complete_item:
        return []
    base_person = next(
        person for person in people["_embedded"]["people"] if person.get("id_") == id_
    )
    base_person_items = base_person.get("_embedded", {}).get("items", [])
    base_person_items.append(complete_item)
    return base_person_items


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
