"""Ensure that the settings module works as intended."""


def test_settings_is_usable() -> None:
    """Ensure that the settings module can be imported and provides at least one setting."""
    from esg_fastapi import settings

    assert settings.globus_search_index is not None
