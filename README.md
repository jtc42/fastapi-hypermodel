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

FastAPI-HyperModel is a FastAPI + Pydantic extension for simplifying
hypermedia-driven API development. 

Hypermedia consist of enriching API responses by providing links to other URIs
within the services to fetch related resources or perform certain actions. There
are several levels according to the [Hypermedia Maturity Model
Levels](https://8thlight.com/insights/the-hypermedia-maturity-model). Using
Hypermedia makes APIs reach Level 3 of the [Richardson Maturity Model
(RMM)](https://en.wikipedia.org/wiki/Richardson_Maturity_Model), which involves
leveraging [Hypertext As The Engine Of Application State
(HATEOAS)](https://en.wikipedia.org/wiki/HATEOAS), that is, Hypermedia.

Below are some examples of responses using hypermedia. For detailed examples,
check the docs.

<table>
<tbody>
<tr>
<th>Format</th>
<th>Response</th>
</tr>
<tr>
<td>

No Hypermdia

</td>
<td>

```json linenums="1"
{
    "id_": "item01",
    "name": "Foo",
    "price": 10.2,
}
```

</td>
</tr>
<tr>
<td>

Level 0 Hypermedia (URLFor)

</td>
<td>

```json linenums="1"
{
    "id_": "item01",
    "name": "Foo",
    "price": 10.2,

    "href": "/items/item01",
    "update": "/items/item01"
}
```

</td>
</tr>
<tr>
<td>

Level 1 Hypermedia (HAL)

</td>
<td>

```json linenums="1"
{
    "id_": "item01",
    "name": "Foo",
    "price": 10.2,

    "_links": {
        "self": {"href": "/items/item01"},
        "update": {"href": "/items/item01"},
    },
}
```

</td>
</tr>
<tr>
<td>

Level 2 Hypermedia (Siren)

</td>
<td>

```json linenums="1"
{
    "properties": {
        "id_": "item01",
        "name": "Foo",
        "price": 10.2
    },
    "links": [
        {
            "rel": ["self"],
            "href": "/items/item01"
        }
    ],
    "actions": [
        {
            "name": "update",
            "method": "PUT",
            "href": "/items/item01",
            "type": "application/x-www-form-urlencoded",
            "fields": [
                {
                    "name": "name",
                    "type": "text",
                    "value": "Foo"
                },
                {
                    "name": "description",
                    "type": "text",
                    "value": "None"
                },
                {
                    "name": "price",
                    "type": "number",
                    "value": "10.2"
                }
            ]
        }
    ]
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

