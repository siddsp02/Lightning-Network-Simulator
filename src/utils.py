import doctest
import math
import random
import textwrap
from collections import deque
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum, auto
from itertools import chain, product, starmap
from typing import Iterable, Iterator, NamedTuple, Set, TypeVar

T = TypeVar("T")


class TxStatus(Enum):
    SUCCESS = auto()
    INSUFFICIENT_FUNDS = auto()
    UNREACHABLE = auto()


class TxData(NamedTuple):
    path: deque[str]
    sender: str
    receiver: str
    amount: int
    hops: int
    status: TxStatus

    def __str__(self) -> str:
        pairs = self._asdict().items()
        return "{}(\n{}\n)".format(
            type(self).__name__,
            textwrap.indent(",\n".join(starmap("{}={!r}".format, pairs)), " " * 4),
        )


@dataclass
class SubstringSet(Set[str]):
    chars: str
    maxlen: int = 1

    def __post_init__(self) -> None:
        if len(self.chars) != len(set(self.chars)):
            raise ValueError("Characters must be unique")

    def __len__(self) -> int:
        x = len(self.chars)
        return sum(x**i for i in range(1, self.maxlen + 1))

    def __iter__(self) -> Iterator[str]:
        return generate_node_names(self.chars, self.maxlen)

    def __contains__(self, value: str) -> bool:  # type: ignore
        return len(value) <= self.maxlen and all(char in self.chars for char in value)


def rand(precision: int = 2) -> Decimal:
    """Returns a random decimal value in the interval [0, 1).

    Default precision is 2.
    """
    val = random.random()
    return Decimal(f"{val:.{precision}f}")


def rand_between(lower: Decimal, upper: Decimal, precision: int = 2) -> Decimal:
    """Returns a random Decimal value between an upper and lower bound."""
    result = random.uniform(float(lower), float(upper))
    return round(Decimal(result), precision)


def generate_node_names(chars: str, maxlen: int = 2) -> Iterator[str]:
    """Utility function for generating node names for a large graph.
    Make sure that the string is all unique characters for this
    function to work properly.

    This gives out all possible substrings of length 1 to `maxlen`
    from characters of `chars`.

    Examples:
    >>> list(generate_node_names("ab", maxlen=2))
    ['a', 'b', 'aa', 'ab', 'ba', 'bb']
    >>> list(generate_node_names("ab", maxlen=3))
    ['a', 'b', 'aa', 'ab', 'ba', 'bb', 'aaa', 'aab', 'aba', 'abb', 'baa', 'bab', 'bba', 'bbb']
    """
    return chain.from_iterable(
        map("".join, product(chars, repeat=i)) for i in range(1, maxlen + 1)
    )


# The following code was taken from the link below (see end).
# https://docs.python.org/3/library/itertools.html


def nth_combination(iterable: Iterable[T], r: int, index: int) -> tuple[T, ...]:
    """Equivalent to list(combinations(iterable, r))[index]"""
    pool = tuple(iterable)
    n = len(pool)
    c = math.comb(n, r)
    if index < 0:
        index += c
    if index < 0 or index >= c:
        raise IndexError()
    result = []
    while r:
        c, n, r = c * r // n, n - 1, r - 1
        while index >= c:
            index -= c
            c, n = c * (n - r) // n, n - 1
        result.append(pool[-1 - n])
    return tuple(result)


if __name__ == "__main__":
    doctest.testmod()
