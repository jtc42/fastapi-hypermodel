from typing import Any, Optional, Sequence, cast

from fastapi import FastAPI, HTTPException
from pydantic.main import BaseModel

from examples.siren.data import Item as ItemData
from examples.siren.data import Person as PersonData
from examples.siren.data import items, people
from fastapi_hypermodel import (
    SirenActionFor,
    SirenHyperModel,
    SirenLinkFor,
    SirenResponse,
)


class ItemSummary(SirenHyperModel):
    id_: str
    name: str

    links: Sequence[SirenLinkFor] = (
        SirenLinkFor("read_item", {"id_": "<id_>"}, rel=["self"]),
    )

    actions: Sequence[SirenActionFor] = (
        SirenActionFor("update_item", {"id_": "<id_>"}, name="update"),
    )


class Item(ItemSummary):
    description: Optional[str] = None
    price: float


class ItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None


class ItemCreate(BaseModel):
    id_: str


class ItemCollection(SirenHyperModel):
    items: Sequence[Item]

    links: Sequence[SirenLinkFor] = (SirenLinkFor("read_items", rel=["self"]),)

    actions: Sequence[SirenActionFor] = (
        SirenActionFor("read_item", templated=True, name="find"),
        SirenActionFor("update_item", templated=True, name="update"),
    )


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
            name="add_item",
            populate_fields=False,
            condition=lambda values: not values["is_locked"],
        ),
    )


class PersonCollection(SirenHyperModel):
    people: Sequence[Person]

    links: Sequence[SirenLinkFor] = (SirenLinkFor("read_people", rel=["self"]),)

    actions: Sequence[SirenActionFor] = (
        SirenActionFor(
            "read_person",
            templated=True,
            name="find",
        ),
        SirenActionFor(
            "update_person",
            templated=True,
            name="update",
        ),
    )


class PersonUpdate(BaseModel):
    name: Optional[str] = None
    is_locked: Optional[bool] = None


app = FastAPI()
SirenHyperModel.init_app(app)


@app.get(
    "/items",
    response_model=ItemCollection,
    response_model_exclude_unset=True,
    response_class=SirenResponse,
)
def read_items() -> Any:
    return items


@app.get(
    "/items/{id_}",
    response_model=Item,
    response_model_exclude_unset=True,
    response_class=SirenResponse,
)
def read_item(id_: str) -> Any:
    return next(item for item in items["items"] if item["id_"] == id_)


@app.put(
    "/items/{id_}",
    response_model=Item,
    response_model_exclude_unset=True,
    response_class=SirenResponse,
)
def update_item(id_: str, item: ItemUpdate) -> Any:
    base_item = next(item for item in items["items"] if item["id_"] == id_)
    update_item = cast(ItemData, item.model_dump(exclude_none=True))
    base_item.update(update_item)
    return base_item


@app.get(
    "/people",
    response_model=PersonCollection,
    response_model_exclude_unset=True,
    response_class=SirenResponse,
)
def read_people() -> Any:
    return people


@app.get(
    "/people/{id_}",
    response_model=Person,
    response_model_exclude_unset=True,
    response_class=SirenResponse,
)
def read_person(id_: str) -> Any:
    return next(person for person in people["people"] if person["id_"] == id_)


@app.put(
    "/people/{id_}",
    response_model=Person,
    response_model_exclude_unset=True,
    response_class=SirenResponse,
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
    response_class=SirenResponse,
)
def put_person_items(id_: str, item: ItemCreate) -> Any:
    complete_item = next(
        (item_ for item_ in items["items"] if item_["id_"] == item.id_),
        None,
    )
    if not complete_item:
        raise HTTPException(status_code=404, detail=f"No item found with id {item.id_}")

    base_person = next(person for person in people["people"] if person["id_"] == id_)

    base_person_items = base_person["items"]
    base_person_items.append(complete_item)
    return base_person
