# FastAPI-HyperModel

FastAPI-HyperModel is a FastAPI + Pydantic extension for simplifying hypermedia-driven API development. 

This module adds a new Pydantic model base-class, supporting dynamic `href` generation based on object data.

<table>
<tbody>
<tr>
<th>Model</th>
<th>Response</th>
</tr>
<tr>
<td>

```python
class ItemSummary(HyperModel):
    name: str
    id: str
    href = UrlFor(
        "read_item", {"item_id": "<id>"}
    )
```

</td>
<td>

```json
{
  "name": "Foo",
  "id": "item01",
  "href": "/items/item01"
}
```

</td>
</tr>
<tr></tr>
<tr>
<td>

```python
class ItemSummary(HyperModel):
    name: str
    id: str
    link = HALFor(
        "read_item", {"item_id": "<id>"}, 
        description="Read an item"
    )
```

</td>
<td>

```json
{
  "name": "Foo",
  "id": "item01",
  "link": {
      "href": "/items/item01",
      "method": "GET",
      "description": "Read an item"
  }
}
```

</td>
</tr>
</tbody>
</table>

## Installation

`pip install fastapi-hypermodel`

## Attributions

Some functionality is based on [Flask-Marshmallow](https://github.com/marshmallow-code/flask-marshmallow/blob/dev/src/flask_marshmallow/fields.py) `URLFor` class.

