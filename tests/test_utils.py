"""Test suite for the utils module.

This module contains various utility functions that do not fit well in other modules. The functions in this module are:

- `type_of(baseclass: T) -> T`: Inherit from `baseclass` only for type checking purposes.
- `is_list(value: T) -> TypeGuard[list]`: TypeGuard based on whether the value is a list.
- `one_or_list(value: list[T] | T) -> T | list[T]`: Unwrap length 1 lists.
- `ensure_list(value: T) -> T | list[T]`: If value is a list, return as is. Otherwise, wrap it in a list.
"""


def test_one_or_list_single_item() -> None:
    """Given a list of len() > 1, return the list unchanged."""
    from esg_fastapi.utils import one_or_list

    assert one_or_list([1, 2, 3]) == [1, 2, 3]


def test_one_or_list_single_item_in_list() -> None:
    """Unwrap a length 1 list[int]."""
    from esg_fastapi.utils import one_or_list

    assert one_or_list([1]) == 1


def test_one_or_list_string() -> None:
    """Unwrap a length 1 list[int]."""
    from esg_fastapi.utils import one_or_list

    assert one_or_list("hello") == "hello"


def test_one_or_list_empty_list() -> None:
    """Empty list is unchanged.

    TODO: is this the correct behavior?
    """
    from esg_fastapi.utils import one_or_list

    assert one_or_list([]) == []


def test_ensure_list_empty_list() -> None:
    """Empty list is unchanged."""
    from esg_fastapi.utils import ensure_list

    assert ensure_list([]) == []


def test_ensure_list_empty_str() -> None:
    """Empty string is wrapped in a list."""
    from esg_fastapi.utils import ensure_list

    assert ensure_list("") == [""]


def test_ensure_list_populated_list() -> None:
    """Populated list is unchanged."""
    from esg_fastapi.utils import ensure_list

    assert ensure_list([1, 2, 3, 4]) == [1, 2, 3, 4]
