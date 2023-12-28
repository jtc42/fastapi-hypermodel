from typing import Any, List, Optional

from fastapi import FastAPI
from pydantic import BaseModel

from examples.url_for.data import items, people
from fastapi_hypermodel import HyperModel, UrlFor

app = FastAPI()
HyperModel.init_app(app)


class ItemSummary(HyperModel):
    name: str
    id_: str

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
    items: List[Item]

    href: UrlFor = UrlFor("read_items")
    find: UrlFor = UrlFor("read_item", template=True)
    update: UrlFor = UrlFor("update_item", template=True)


class Person(HyperModel):
    name: str
    id_: str
    is_locked: bool
    items: List[Item]

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
    people: List[Person]

    href: UrlFor = UrlFor("read_people")
    find: UrlFor = UrlFor("read_person", template=True)
    update: UrlFor = UrlFor("update_person", template=True)


@app.get("/items", response_model=ItemCollection)
def read_items() -> Any:
    return {"items": list(items.values())}


@app.get("/items/{id_}", response_model=Item)
def read_item(id_: str) -> Any:
    return items.get(id_)


@app.put("/items/{id_}", response_model=Item)
def update_item(id_: str, item: ItemUpdate) -> Any:
    items.get(id_, {}).update(item.model_dump(exclude_none=True))
    return items.get(id_)


@app.get("/people", response_model=PeopleCollection)
def read_people() -> Any:
    return {"people": list(people.values())}


@app.get("/people/{id_}", response_model=Person)
def read_person(id_: str) -> Any:
    return people.get(id_)


@app.put("/people/{id_}", response_model=Person)
def update_person(id_: str, person: PersonUpdate) -> Any:
    base_person = people.get(id_, {})
    base_person.update(person.model_dump(exclude_none=True))
    return base_person


@app.put("/people/{id_}/items", response_model=List[Item])
def put_person_items(id_: str, item: ItemCreate) -> Any:
    complete_item = items.get(item.id_)

    if not complete_item:
        return []

    base_person = people.get(id_, {})
    base_person_items = base_person.get("items", [])
    base_person_items.append(complete_item)
    return base_person_items


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
