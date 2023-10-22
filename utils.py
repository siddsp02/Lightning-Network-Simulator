from collections import deque
from dataclasses import dataclass, field
import doctest
from enum import Enum, auto
import random
from decimal import Decimal
from itertools import product
from typing import Iterator


class TransactionStatus(Enum):
    SUCCESS = auto()
    FAILURE = auto()


@dataclass
class TxData:
    path: deque[str]
    sender: str
    receiver: str
    hops: int = field(init=False)
    status: TransactionStatus

    def __post_init__(self) -> None:
        self.hops = len(self.path)


def rand(precision: int = 2) -> Decimal:
    """Returns a random decimal value in the interval [0, 1).

    Default precision is 2.
    """
    val = random.random()
    return Decimal(f"{val:.{precision}f}")


def generate_node_names(chars: str, maxlen: int = 2) -> Iterator[str]:
    """Utility function for generating node names for a large graph.

    This gives out all possible substrings of length 1 to `maxlen`
    from characters of `string`.

    Example:
    >>> list(generate_node_names("ab", maxlen=2))
    ['a', 'b', 'aa', 'ab', 'ba', 'bb']
    """
    for i in range(1, maxlen + 1):
        yield from map("".join, product(chars, repeat=i))


if __name__ == "__main__":
    doctest.testmod()
