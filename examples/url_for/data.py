items = {
    "item01": {"id_": "item01", "name": "Foo", "price": 50.2},
    "item02": {
        "id_": "item02",
        "name": "Bar",
        "description": "The Bar fighters",
        "price": 62,
    },
    "item03": {
        "id_": "item03",
        "name": "Baz",
        "description": "There goes my baz",
        "price": 50.2,
    },
    "item04": {
        "id_": "item04",
        "name": "Doe",
        "description": "There goes my Doe",
        "price": 5,
    },
}

people = {
    "person01": {
        "id_": "person01",
        "name": "Alice",
        "is_locked": False,
        "items": [items["item01"], items["item02"]],
    },
    "person02": {
        "id_": "person02",
        "name": "Bob",
        "is_locked": True,
        "items": [items["item03"]],
    },
}
