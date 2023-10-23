import doctest
import random
import textwrap
from collections import deque
from decimal import Decimal
from enum import Enum, auto
from itertools import product, starmap
from typing import Iterator, NamedTuple


class TxStatus(Enum):
    SUCCESS = auto()
    INSUFFICIENT_FUNDS = auto()
    UNREACHABLE = auto()


class TxData(NamedTuple):
    path: deque[str]
    sender: str
    receiver: str
    hops: int
    status: TxStatus

    def __str__(self) -> str:
        pairs = self._asdict().items()
        return "{}(\n{}\n)".format(
            type(self).__name__,
            textwrap.indent(",\n".join(starmap("{}={!r}".format, pairs)), " " * 4),
        )


def rand(precision: int = 2) -> Decimal:
    """Returns a random decimal value in the interval [0, 1).

    Default precision is 2.
    """
    val = random.random()
    return Decimal(f"{val:.{precision}f}")


def rand_between(lower: Decimal, upper: Decimal, precision: int = 2) -> Decimal:
    result = random.uniform(float(lower), float(upper))
    return round(Decimal(result), precision)


def generate_node_names(chars: str, maxlen: int = 2) -> Iterator[str]:
    """Utility function for generating node names for a large graph.

    This gives out all possible substrings of length 1 to `maxlen`
    from characters of `chars`.

    Example:
    >>> list(generate_node_names("ab", maxlen=2))
    ['a', 'b', 'aa', 'ab', 'ba', 'bb']
    """
    for i in range(1, maxlen + 1):
        yield from map("".join, product(chars, repeat=i))


if __name__ == "__main__":
    doctest.testmod()
