import json

import pytest
from pydantic import BaseModel
from semver import Version

from esg_fastapi.api.versions.v1.types import SemVer


@pytest.mark.parametrize("field_value", ["1.2.3", Version.parse("4.5.6")])
def test_SemVer_field_serializes_to_str(field_value: SemVer) -> None:
    """Test that SemVer serializes to a string and accepts both strings and parsed `Version` objects."""

    class TestModel(BaseModel):
        version: SemVer

    model_schema = TestModel.model_json_schema()
    assert model_schema["properties"]["version"]["type"] == "string"

    test_instance = TestModel(version=field_value)
    model_json = test_instance.model_dump_json()
    loaded_model = json.loads(model_json)

    assert isinstance(loaded_model["version"], str)
