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

Person = TypedDict(
    "Person", {"id_": str, "name": str, "is_locked": bool, "sc:items": List[Item]}
)


class People(TypedDict):
    people: List[Person]


people: People = {
    "people": [
        {
            "id_": "person01",
            "name": "Alice",
            "is_locked": False,
            "sc:items": items["sc:items"][:2],
        },
        {
            "id_": "person02",
            "name": "Bob",
            "is_locked": True,
            "sc:items": items["sc:items"][2:],
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
