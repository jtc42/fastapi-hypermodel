from typing import Any, Optional, Sequence, cast

from fastapi import FastAPI, HTTPException
from pydantic import Field
from pydantic.main import BaseModel

from examples.hal.data import Item as ItemData
from examples.hal.data import Person as PersonData
from examples.hal.data import curies, items, people
from fastapi_hypermodel import (
    FrozenDict,
    HALFor,
    HALHyperModel,
    HALLinks,
    HALResponse,
)


class ItemSummary(HALHyperModel):
    id_: str
    name: str

    links: HALLinks = FrozenDict({
        "self": HALFor("read_item", {"id_": "<id_>"}),
        "update": HALFor("update_item", {"id_": "<id_>"}),
    })


class Item(ItemSummary):
    description: Optional[str] = None
    price: float


class ItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None


class ItemCreate(ItemUpdate):
    id_: str


class ItemCollection(HALHyperModel):
    items: Sequence[Item] = Field(alias="sc:items")

    links: HALLinks = FrozenDict({
        "self": HALFor("read_items"),
        "find": HALFor("read_item", templated=True),
        "update": HALFor("update_item", templated=True),
    })


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


class PersonCollection(HALHyperModel):
    people: Sequence[Person]

    links: HALLinks = FrozenDict({
        "self": HALFor("read_people"),
        "find": HALFor("read_person", templated=True),
        "update": HALFor(
            "update_person",
            templated=True,
        ),
    })


class PersonUpdate(BaseModel):
    name: Optional[str] = None
    is_locked: Optional[bool] = None


app = FastAPI()
HALHyperModel.init_app(app)
HALHyperModel.register_curies(curies)


@app.get(
    "/items",
    response_model=ItemCollection,
    response_model_exclude_unset=True,
    response_class=HALResponse,
)
def read_items() -> Any:
    return items


@app.get(
    "/items/{id_}",
    response_model=Item,
    response_model_exclude_unset=True,
    response_class=HALResponse,
)
def read_item(id_: str) -> Any:
    return next(item for item in items["sc:items"] if item["id_"] == id_)


@app.put(
    "/items/{id_}",
    response_model=Item,
    response_model_exclude_unset=True,
    response_class=HALResponse,
)
def update_item(id_: str, item: ItemUpdate) -> Any:
    base_item = next(item for item in items["sc:items"] if item["id_"] == id_)
    update_item = cast(ItemData, item.model_dump(exclude_none=True))
    base_item.update(update_item)
    return base_item


@app.get(
    "/people",
    response_model=PersonCollection,
    response_model_exclude_unset=True,
    response_class=HALResponse,
)
def read_people() -> Any:
    return people


@app.get(
    "/people/{id_}",
    response_model=Person,
    response_model_exclude_unset=True,
    response_class=HALResponse,
)
def read_person(id_: str) -> Any:
    return next(person for person in people["people"] if person["id_"] == id_)


@app.put(
    "/people/{id_}",
    response_model=Person,
    response_model_exclude_unset=True,
    response_class=HALResponse,
)
def update_person(id_: str, person: PersonUpdate) -> Any:
    base_person = next(person for person in people["people"] if person["id_"] == id_)
    update_person = cast(PersonData, person.model_dump(exclude_none=True))
    base_person.update(update_person)
    return base_person


@app.put(
    "/people/{id_}/items",
    response_model=Person,
    response_model_exclude_unset=True,
    response_class=HALResponse,
)
def put_person_items(id_: str, item: ItemCreate) -> Any:
    complete_item = next(
        (item_ for item_ in items["sc:items"] if item_["id_"] == item.id_),
        None,
    )
    if not complete_item:
        raise HTTPException(status_code=404, detail=f"No item found with id {item.id_}")

    base_person = next(person for person in people["people"] if person["id_"] == id_)

    base_person_items = base_person["sc:items"]
    base_person_items.append(complete_item)
    return base_person
