"""Utilities that don't fit well in other modules."""

import time
from collections.abc import Sequence
from types import TracebackType
from typing import TYPE_CHECKING, Any, Optional, Self, Type

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


def one_or_list(value: Sequence[T] | T) -> T | Sequence[T]:
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
    if isinstance(value, list) and len(value) == 1:
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


def quote_str(value: str | T) -> str | T:
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
    if isinstance(value, str) and not value.startswith('"') and not value.endswith('"'):
        return f'"{value}"'
    return value


def format_fq_field(field: tuple[str, Any]) -> str:
    """Convert key, value pairs to key:value str expected to be returned by Solr."""
    # TODO: what determines if a field is non-quoted? I suspect things that are represented as
    #       enums in the java code. If we can determine which fields are non-quoted, we should
    #       tag them with annotations and a computed field like we do with non-queriable fields.
    non_quoted_fields = {"type"}
    key, value = field
    value = one_or_list(value)
    return f"{key}:{value if key in non_quoted_fields else quote_str(value)}"
