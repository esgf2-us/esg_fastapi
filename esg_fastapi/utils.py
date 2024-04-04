"""Utilities that don't fit well in other modules."""

from typing import TYPE_CHECKING, TypeGuard

from annotated_types import T


def type_of(baseclass: T) -> T:
    """Inherit from `baseclass` only for type checking purposes.

    This allows informing type checkers that the inheriting class ducktypes
    as the given `baseclass` without actually inheriting from it.

    Notes:
    - `typing.Protocol` is the right answer to this problem, but `sys.modules.__setitem__`
      currently checks for the ModuleType directly rather than a Protocol.
    - `pydantic_settings.BaseSettings` can't inherit from `ModuleType` due to conflicts
      in its use of `__slots__`
    """
    if TYPE_CHECKING:
        return baseclass
    return object


def is_list(value: object) -> TypeGuard[list]:
    """TypeGuard based on whether the value is a list.

    Parameters:
    value (T): The value to be checked.

    Returns:
    TypeGuard[list]: Returns True if the value is a list, otherwise False.
    """
    return isinstance(value, list)


def one_or_list(value: list[T] | T) -> T | list[T]:
    """Unwrap length 1 lists.

    This function takes a value that can be either a single item or a list of items. If the passed value is a list of length 1, the function returns the single item in the list. Otherwise, it returns the original list.

    Args:
        value (list[T] | T): The value to be unwrapped.

    Returns:
        T | list[T]: If the passed list is length 1, the function returns the single item in the list. Otherwise, it returns the original list.

    Example:
        >>> one_or_list([1, 2, 3])
        [1, 2, 3]
        >>> one_or_list(4)
        4
        >>> one_or_list("hello")
        'hello'
        >>> one_or_list([1])
        1
    """
    if is_list(value) and len(value) == 1:
        return value[0]
    return value


def ensure_list(value: T) -> T | list[T]:
    """If value is a list, return as is. Otherwise, wrap it in a list.

    Args:
        value (T): The value to be ensured as a list.

    Returns:
        list: Either the original list passed in, or the passed value wrapped in a list.

    Raises:
        TypeError: If the passed value is not a list and cannot be converted to one.

    Examples:
        >>> ensure_list(123)
        [123]
        >>> ensure_list([123, 456])
        [123, 456]
    """
    if isinstance(value, list):
        return value
    else:
        return [value]
