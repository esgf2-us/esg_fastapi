"""Utilities that don't fit well in other modules."""

import time
from types import TracebackType
from typing import TYPE_CHECKING, Any, Optional, Self, Type, TypeGuard

from annotated_types import T


class Timer:
    """Context manager for timing the seconds elapsed during a context.

    The `Timer` context manager is used to measure the time taken for a block of code to execute.

    Attributes:
        start_time (int): The start time of the context in nanoseconds.
        end_time (int): The end time of the context in nanoseconds.
        time (int): The time taken by the context in seconds.
    """

    def __enter__(self: Self) -> Self:
        """Open the context and start the timer.

        Returns:
            Timer: Exposes the start, end, and delta in seconds of the context.
        """
        self.start_time = time.monotonic_ns()
        return self

    def __exit__(
        self: Self,
        ex_typ: Optional[Type[BaseException]],
        ex_val: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """Close the context and stop the timer."""
        self.end_time = time.monotonic_ns()
        self.time = int((self.end_time - self.start_time) // 1e9)


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


def quote_str(value: str) -> str:
    r"""Wrap a string in double quotes.

    Args:
        value (str): The value to be wrapped in double quotes.

    Returns:
        str: The wrapped string.

    Examples:
        >>> quote_str("hello")
        '"hello"'
        >>> quote_str("hello'world")
        '"hello'world"'
    """
    if not value.startswith('"') and not value.endswith('"'):
        return f'"{value}"'
    return value


def format_fq_field(field: tuple[str, Any]) -> str:
    """Conver key, value pairs to key:value str expected to be returned by Solr."""
    quoted_fields = {"project", "dataset_id"}
    key, value = field
    return f"{key}:{quote_str(value) if key in quoted_fields else value}"
