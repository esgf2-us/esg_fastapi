"""Ensure that the settings module works as intended."""

from types import ModuleType

import pytest
from pytest_mock import MockerFixture
from typing_extensions import assert_type

from esg_fastapi.utils import type_of


def test_settings_is_usable() -> None:
    """Ensure that the settings module can be imported and provides at least one setting."""
    from esg_fastapi import settings

    assert settings.globus_search_index is not None


@pytest.mark.parametrize("enabled", [True, False])
def test_type_of_indicates_correctly(mocker: MockerFixture, enabled: bool) -> None:
    """Ensure that a class inheriting from type_of(T) type checks as a T but otherwise doesn't change its inheritance."""
    mocker.patch("typing.TYPE_CHECKING", enabled)

    class TestObj(type_of(ModuleType)): ...

    if enabled:
        assert_type(TestObj, ModuleType)
    else:
        assert_type(TestObj, object)
