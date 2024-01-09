items = {
    "items": [
        {"id_": "item01", "name": "Foo", "price": 50.2},
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

people = {
    "people": [
        {
            "id_": "person01",
            "name": "Alice",
            "is_locked": False,
            "items": items["items"][:2],
        },
        {
            "id_": "person02",
            "name": "Bob",
            "is_locked": True,
            "items": items["items"][2:],
        },
    ]
}
