from typing import Any, Optional, Sequence, cast

from fastapi import FastAPI
from pydantic import BaseModel

from examples.url_for.data import Item as ItemData
from examples.url_for.data import Person as PersonData
from examples.url_for.data import items, people
from fastapi_hypermodel import HyperModel, UrlFor


class ItemSummary(HyperModel):
    id_: str
    name: str

    href: UrlFor = UrlFor("read_item", {"id_": "<id_>"})
    update: UrlFor = UrlFor("update_item", {"id_": "<id_>"})


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
    items: Sequence[Item]

    href: UrlFor = UrlFor("read_items")
    find: UrlFor = UrlFor("read_item", templated=True)
    update: UrlFor = UrlFor("update_item", templated=True)


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


class PersonUpdate(BaseModel):
    name: Optional[str] = None
    is_locked: Optional[bool] = None


class PeopleCollection(HyperModel):
    people: Sequence[Person]

    href: UrlFor = UrlFor("read_people")
    find: UrlFor = UrlFor("read_person", templated=True)
    update: UrlFor = UrlFor("update_person", templated=True)


app = FastAPI()
HyperModel.init_app(app)


@app.get("/items", response_model=ItemCollection)
def read_items() -> Any:
    return items


@app.get("/items/{id_}", response_model=Item)
def read_item(id_: str) -> Any:
    return next(item for item in items["items"] if item["id_"] == id_)


@app.put("/items/{id_}", response_model=Item)
def update_item(id_: str, item: ItemUpdate) -> Any:
    item_ = next(item_ for item_ in items["items"] if item_["id_"] == id_)
    update_item = cast(ItemData, item.model_dump(exclude_none=True))
    item_.update(update_item)
    return item_


@app.get("/people", response_model=PeopleCollection)
def read_people() -> Any:
    return people


@app.get("/people/{id_}", response_model=Person)
def read_person(id_: str) -> Any:
    return next(person for person in people["people"] if person["id_"] == id_)


@app.put("/people/{id_}", response_model=Person)
def update_person(id_: str, person: PersonUpdate) -> Any:
    base_person = next(person for person in people["people"] if person["id_"] == id_)
    update_person = cast(PersonData, person.model_dump(exclude_none=True))
    base_person.update(update_person)
    return base_person


@app.put("/people/{id_}/items", response_model=Sequence[Item])
def put_person_items(id_: str, item: ItemCreate) -> Any:
    complete_item = next(
        (item_ for item_ in items["items"] if item_["id_"] == item.id_),
        None,
    )

    if not complete_item:
        return []

    base_person = next(person for person in people["people"] if person["id_"] == id_)
    base_person_items = base_person["items"]
    base_person_items.append(complete_item)
    return base_person_items
