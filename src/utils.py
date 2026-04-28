import textwrap
from collections import deque
from enum import Enum, auto
from itertools import starmap
from typing import Any, NamedTuple


class TxStatus(Enum):
    SUCCESS = auto()
    INSUFFICIENT_FUNDS = auto()
    UNREACHABLE = auto()


class TxData[T](NamedTuple):
    path: deque[T]
    sender: T
    receiver: T
    amount: int
    hops: int
    status: TxStatus

    def __str__(self) -> str:
        pairs = self._asdict().items()
        return "{}(\n{}\n)".format(
            type(self).__name__,
            textwrap.indent(",\n".join(starmap("{}={!r}".format, pairs)), " " * 4),
        )
