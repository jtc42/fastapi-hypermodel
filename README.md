# FastAPI-HyperModel

<p align="center">
    <em>Simple hypermedia for FastAPI</em>
</p>
<p align="center">
<a href="https://pypi.org/project/fastapi-utils" target="_blank">
    <img src="https://badge.fury.io/py/fastapi-hypermodel.svg" alt="Package version">
</a>
    <img src="https://img.shields.io/pypi/pyversions/fastapi-hypermodel.svg">
    <img src="https://img.shields.io/github/license/jtc42/fastapi-hypermodel.svg">
</p>

---

**Documentation**: <a href="https://jtc42.github.io/fastapi-hypermodel/" target="_blank">https://jtc42.github.io/fastapi-hypermodel/</a>

**Source Code**: <a href="https://github.com/jtc42/fastapi-hypermodel" target="_blank">https://github.com/jtc42/fastapi-hypermodel</a>

---

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

## Limitations

Currently, query parameters will not resolve correctly. When generating a resource URL, ensure all parameters passed are path parameters, not query parameters.

This is an upstream issue, being tracked [here](https://github.com/encode/starlette/issues/560).

## Attributions

Huge thanks to [@christoe](https://github.com/christoe) for building support for Pydantic 2.

Some functionality is based on [Flask-Marshmallow](https://github.com/marshmallow-code/flask-marshmallow/blob/dev/src/flask_marshmallow/fields.py) `URLFor` class.
