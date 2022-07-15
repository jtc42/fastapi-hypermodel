# Extending FastAPI-HyperModel

The `HyperModel` class works by adding a root validator that iterates through each field on the instance being validated, and checks if it is an instance of `AbstractHyperField`.

If an instance of `AbstractHyperField` is found, its `__build_hypermedia__` method is called, and the returned value will be substituted into the validated `HyperModel` instance.

## Creating a new link class

In most respects, a custom link class should be treated as a [custom Pydantic data type](https://pydantic-docs.helpmanual.io/usage/types/#custom-data-types). It can inherit from any Pydantic-compatible type, include any custom validation required, but *must* also inherit from `AbstractHyperField` and include a `__build_hypermedia__` method.

This method must accept two arguments, an *optional* `fastapi.FastAPI` instance (optional only because prior to `HyperModel.init_app` being called, it will evaluate to `None`), and a dict containing the name-to-value mapping of all fields on the parent `HyperModel` instance.

As an example, we'll re-implement the basic `URLFor` class from scratch.

### Create a basic custom Pydantic class

First we'll create a subclass of `UrlType` which accepts an endpoint string, and a dictionary of URL parameter to field mappings (see [Basic Usage](basics.md)).

```python
from fastapi_hypermodel.hypermodel import UrlType

class UrlFor(UrlType):
    def __init__(self, endpoint: str, param_values: Optional[Dict[str, str]] = None):
        self.endpoint: str = endpoint
        self.param_values: Dict[str, str] = param_values or {}
        super().__init__()
```

Next, we'll add out basic Pydantic validation functionality:

```python
from fastapi_hypermodel.hypermodel import UrlType
from starlette.datastructures import URLPath

class UrlFor(UrlType):
    def __init__(self, endpoint: str, param_values: Optional[Dict[str, str]] = None):
        self.endpoint: str = endpoint
        self.param_values: Dict[str, str] = param_values or {}
        super().__init__()

    @no_type_check
    def __new__(cls, *_):
        return str.__new__(cls)

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value: Any) -> "UrlFor":
        """
        Validate UrlFor object against itself.
        The UrlFor field type will only accept UrlFor instances.
        """
        # Return original object if it's already a UrlFor instance
        if value.__class__ == URLPath:
            return value
        # Otherwise raise an exception
        raise ValueError(
            f"UrlFor field should resolve to a starlette.datastructures.URLPath instance. Instead got {value.__class__}"
        )
```

At this point, our custom type will behave as a normal Pydantic type, but won't do any hypermedia substitutions.
For this, we must add our "magic" `__build_hypermedia__` method.

```python
from fastapi_hypermodel.hypermodel import UrlType, resolve_param_values
from starlette.datastructures import URLPath

class UrlFor(UrlType, AbstractHyperField):
    def __init__(self, endpoint: str, param_values: Optional[Dict[str, str]] = None):
        self.endpoint: str = endpoint
        self.param_values: Dict[str, str] = param_values or {}
        super().__init__()

    @no_type_check
    def __new__(cls, *_):
        return str.__new__(cls)

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value: Any) -> "UrlFor":
        """
        Validate UrlFor object against itself.
        The UrlFor field type will only accept UrlFor instances.
        """
        # Return original object if it's already a UrlFor instance
        if value.__class__ == URLPath:
            return value
        # Otherwise raise an exception
        raise ValueError(
            f"UrlFor field should resolve to a starlette.datastructures.URLPath instance. Instead got {value.__class__}"
        )

    def __build_hypermedia__(
        self, app: Optional[FastAPI], values: Dict[str, Any]
    ) -> Optional[str]:
        if app is None:
            return None
        resolved_params = resolve_param_values(self.param_values, values)
        return app.url_path_for(self.endpoint, **resolved_params)
```

Here we see that, as expected, our method accepts a `FastAPI` instance, and our dict of parent field values. We pass these field values, along with the URL parameter to field mappings, to a `resolve_param_values` function. This function takes our URL parameter to field mappings, and substitutes in the *actual* values from the parent. 

We can then pass this new dictionary of URL parameters to the FastAPI `url_path_for` function to generate a valid URL for this specific endpoint with this specific set of values.

## Creating a new link set class

