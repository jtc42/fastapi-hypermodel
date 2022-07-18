import pytest
from fastapi_hypermodel.hypermodel import resolve_param_values, InvalidAttribute


def test_resolve_param_values_flat():
    assert resolve_param_values(
        {"person_id": "<id>"}, {"name": "Bob", "id": "person02"}
    ) == {"person_id": "person02"}


def test_resolve_param_values_deep():
    assert (
        resolve_param_values(
            {"person_id": "<identifiers.ids.id>"},
            {"name": "Bob", "identifiers": {"ids": {"id": "person02"}}},
        )
        == {"person_id": "person02"}
    )


def test_resolve_param_values_none():
    with pytest.raises(InvalidAttribute):
        resolve_param_values({"person_id": "<id>"}, {"name": "Bob", "id": None})


def test_resolve_param_values_url_escape():
    assert resolve_param_values(
        {"person_id": "<id>"}, {"name": "Bob", "id": 'person"02"'}
    ) == {"person_id": "person%2202%22"}
