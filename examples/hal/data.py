from typing import List

from fastapi_hypermodel import HALForType, UrlType

items = {
    "_embedded": {
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
}

people = {
    "_embedded": {
        "people": [
            {
                "id_": "person01",
                "name": "Alice",
                "is_locked": False,
                "_embedded": {
                    "sc:items": [
                        items["_embedded"]["sc:items"][0],
                        items["_embedded"]["sc:items"][1],
                    ],
                },
            },
            {
                "id_": "person02",
                "name": "Bob",
                "is_locked": True,
                "_embedded": {
                    "sc:items": [items["_embedded"]["sc:items"][2]],
                },
            },
        ]
    },
}

curies: List[HALForType] = [
    HALForType(
        href=UrlType("https://schema.org/{rel}"),
        name="sc",
        templated=True,
    )
]
