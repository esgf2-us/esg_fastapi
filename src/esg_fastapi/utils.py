"""Utilities that don't fit well in other modules."""

import logging
import time
from collections.abc import Sequence
from types import TracebackType
from typing import Any, Optional, Self

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
        ex_typ: Optional[type[BaseException]],
        ex_val: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """Close the context and stop the timer."""
        self.end_time = time.monotonic_ns()
        self.time = int((self.end_time - self.start_time) // 1e9)


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
    return value[0] if isinstance(value, list) and len(value) == 1 else value


def ensure_list(value: T) -> T | list[T]:
    """If value is a list, return as is. Otherwise, wrap it in a list.

    Args:
        value (T): The value to be ensured as a list.

    Returns:
        list: Either the original list passed in, or the passed value wrapped in a list. Comma separated strings will be split on "," and returned.

    Raises:
        TypeError: If the passed value is not a list and cannot be converted to one.

    Examples:
        >>> ensure_list(123)
        [123]
        >>> ensure_list([123, 456])
        [123, 456]
        >>> ensure_list("foo,bar,baz")
        ["foo", "bar", "baz"]
    """
    if isinstance(value, str):
        return value.split(",")
    return value if isinstance(value, list) else [value]


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

    # Every term except (seemingly only) those for the "type" field must be quoted.

    # Lists must be joined with their key names and OR'd together to form a Solr query:
    # "CMIP5,TAMIP,EUCLIPSE,LUCID,GeoMIP,PMIP" -> project:"CMIP5" || project:"TAMIP" || project:"EUCLIPSE" || project:"LUCID" || project:"GeoMIP" || project:"PMIP3"

    return " || ".join(
        [f"{key}:{quote_str(term) if key not in non_quoted_fields else term}" for term in ensure_list(value)]
    )


def print_loggers(verbose: bool = True) -> None:  # pragma: no cover -- not used yet
    """Print out all initialized loggers.

    This is helpful for you to visualize
    exactly how loggers have been set up in your project (and your dependencies). By
    default, all loggers will be printed. If you want to filter out logging
    placeholders, loggers with NullHandlers, and loggers that only propagate to parent,
    set the verbose parameter to False.

    Shamelessly pilfered from https://github.com/kolonialno/troncos/blob/f7e27727f43be57af41a4531afc46a889c6d45f0/troncos/contrib/logging/tools/__init__.py#L4

    This flowchart helps to debug logging issues:
    https://docs.python.org/3/howto/logging.html#logging-flow

    The output from this function will look something like this:

        Loggers:
        [ root                 ] logs.RootLogger LEVEL:0 PROPAGATE:True
          └ HANDLER logs.StreamHandler  LVL  20
            └ FILTER velodrome.observability.logs.TraceIdFilter
            └ FORMATTER velodrome.observability.logs.LogfmtFormatter
        [ uvicorn.access       ] logs.Logger LEVEL:20 PROPAGATE:False
        [ uvicorn.error        ] logs.Logger LEVEL:20 PROPAGATE:True
          └ FILTER velodrome.utils.obs._UvicornErrorFilter
        [ velodrome.access     ] logs.Logger LEVEL:20 PROPAGATE:True
          └ FILTER velodrome.observability.logs.HttpPathFilter
    """

    def internal(
        curr: tuple[str, logging.Logger],
        rest: list[tuple[str, logging.Logger]],
    ) -> None:
        i_name, i_log = curr

        print(
            f"[ {i_name.ljust(20)[:20]} ]"
            f" {str(i_log.__class__)[8:-2]}"
            f" LEVEL: {i_log.level if hasattr(i_log, 'level') else '?'}"
            f" PROPAGATE: {i_log.propagate if hasattr(i_log, 'propagate') else '?'}"
        )

        if hasattr(i_log, "filters"):
            for f in i_log.filters:
                print("  └ FILTER", str(f.__class__)[8:-2])

        if hasattr(i_log, "handlers"):
            for h in i_log.handlers:
                print(
                    "  └ HANDLER",
                    str(h.__class__)[8:-2],
                    " LEVEL:",
                    h.level if hasattr(h, "level") else "?",
                )
                if hasattr(h, "filters"):
                    for f in h.filters:
                        print("    └ FILTER", str(f.__class__)[8:-2])
                if hasattr(h, "formatter"):
                    print("    └ FORMATTER", str(h.formatter.__class__)[8:-2])

        if rest:
            curr = rest[0]
            rest = rest[1:]
            internal(curr, rest)

    all_but_root = []
    for name, logger in logging.Logger.manager.loggerDict.items():
        if not verbose:
            # Ignore placeholders
            if isinstance(logger, logging.PlaceHolder):
                continue

            # If it is a logger that does nothing but propagate to the parent, ignore
            if len(logger.filters) == 0 and len(logger.handlers) == 0 and logger.propagate:
                continue

            # If this logger only has the Null handler
            if (
                len(logger.filters) == 0
                and len(logger.handlers) == 1
                and isinstance(logger.handlers[0], logging.NullHandler)
            ):
                continue

        all_but_root.append((name, logger))

    all_but_root.sort()

    print("Loggers:")
    internal(("root", logging.getLogger()), all_but_root)  # type: ignore[arg-type]
    print("")
