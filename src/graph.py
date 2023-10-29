from __future__ import annotations

import textwrap
from collections import deque
from dataclasses import dataclass, field
from itertools import pairwise
from pprint import pformat
from typing import Iterable, Iterator, MutableMapping, Self, cast

from src.utils import TxData, TxStatus

BITCOIN_PRICE = 30_000
SATOSHIS_PER_BITCOIN = 100_000_000

# Consider as "infinity" or our maximum edge cost.
# Any edge with a cost greater than or equal to
# this value is unreachable in a graph.
INFINITY = UINT64_MAX = 0xFFFFFFFFFFFFFFFF

MIN_TRANSACTION_VALUE = 5
MAX_TRANSACTION_VALUE = 250
DEFAULT_TRANSACTION_VALUE = MIN_TRANSACTION_VALUE
DEFAULT_CHANNEL_CAPACITY = MAX_TRANSACTION_VALUE * 2
DEFAULT_CHANNEL_BALANCE = MAX_TRANSACTION_VALUE


class Graph(MutableMapping[str, dict[str, int]]):
    """Data type for representing a graph on the network. The underlying
    data structure for storing nodes and channel balances is a hashtable
    mapping node "ids" to channel balances with its peers.
    """

    def __init__(self, nodes: Iterable[str]) -> None:
        self.graph = {node: {} for node in nodes}  # type: ignore

    def __repr__(self) -> str:
        fmt = pformat(self.graph)
        return "{}(\n{},\n)".format(type(self).__name__, textwrap.indent(fmt, " " * 4))

    def __getitem__(self, k: str) -> dict[str, int]:
        return self.graph[k]

    def __setitem__(self, k: str, v: dict[str, int]) -> None:
        self.graph[k] = v

    def __delitem__(self, k: str) -> None:
        del self.graph[k]

    def __iter__(self) -> Iterator[str]:
        return iter(self.graph)

    def __len__(self) -> int:
        return len(self.graph)

    @classmethod
    def from_dict(cls, graph: dict[str, dict[str, int]]) -> Self:
        """Returns a graph instance as a wrapper over a dict.

        Note that this class contains a reference to the dict
        and does not copy its values.
        """
        ret = cls(graph.keys())
        ret.graph = graph
        return ret

    @property
    def nodes(self) -> list[str]:
        return sorted(self)

    def reset(self) -> None:
        """Utility function for resetting graph values and channel data."""
        self.update((node, {}) for node in self.nodes)

    def open_channel(
        self, u: str, v: str, x=DEFAULT_CHANNEL_BALANCE, y=DEFAULT_CHANNEL_BALANCE
    ) -> None:
        """Opens a channel between nodes `u` and `v`, where `u -> v = x` and `v -> u = y`."""
        if u not in self or v not in self:
            raise ValueError("Node passed as parameter does not exist.")
        if u == v:
            raise ValueError("Node cannot open channel with itself.")
        if x < 0 or y < 0:
            raise ValueError("Channel amount cannot be negative.")
        if self[u].get(v) is not None:
            raise Exception("Channel has already been opened.")

        self[u][v] = x
        self[v][u] = y

    def close_channel(self, u: str, v: str) -> None:
        """Closes a channel between nodes `u` and `v`. Channel is deleted from graph."""
        if u not in self or v not in self:
            raise ValueError("Node passed as parameter does not exist.")
        if self[u].get(v) is None:
            raise Exception("Cannot close a channel that hasn't been opened.")

        del self[u][v]
        del self[v][u]

    def transfer(self, u: str, v: str, amount=DEFAULT_TRANSACTION_VALUE) -> None:
        """Transfers an amount `amount` from `u` to `v` through a single channel `(u, v)`."""
        if u not in self or v not in self:
            raise ValueError("Node passed as parameter does not exist.")
        if amount < 0:
            raise ValueError("Transfer amount cannot be negative.")
        if self[u].get(v) is None:
            raise Exception(f"Channel between nodes {u} and {v} has not been opened.")
        if amount > self[u][v]:
            raise ValueError("Insufficient funds.")

        self[u][v] -= amount
        self[v][u] += amount

    def edgecost(self, u: str, v: str) -> int:
        """Returns the cost/weight of an edge (u, v) on a graph."""
        try:
            self[u][v]
        except KeyError:
            return INFINITY
        return 1

    def dijkstra(self, src: str, dst: str) -> tuple[deque[str], int]:
        """Dijkstra's shortest path algorithm for finding the shortest
        path between any two given vertices or nodes on a graph.

        References:
            - https://github.com/siddsp02/Dijkstras-Algorithm/blob/main/dijkstra.py
            - https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm
        """
        dist = dict.fromkeys(self, INFINITY)
        prev = dict.fromkeys(self)
        dist[src] = 0
        unmarked = set(self)
        while unmarked:
            u = min(unmarked, key=dist.__getitem__)
            unmarked.remove(u)
            if u == dst:
                break
            neighbours = self[u].keys()
            for v in neighbours & unmarked:
                alt = dist[u] + self.edgecost(u, v)
                if alt < dist[v]:
                    dist[v] = alt
                    prev[v] = u
        path = deque[str]()
        pred = dst
        while pred is not None:
            path.appendleft(pred)
            pred = cast(str, prev.get(pred))
        return path, dist[dst]

    def send(self, src: str, dst: str, amount=DEFAULT_TRANSACTION_VALUE) -> TxData:
        """Sends an amount `amount` from `src` to `dst` based
        on the shortest path between the two if one exists.
        """
        path, cost = self.dijkstra(src, dst)
        if cost >= INFINITY:
            return TxData(path, src, dst, 0, 0, TxStatus.UNREACHABLE)
        if any(self[u][v] < amount for (u, v) in pairwise(path)):
            return TxData(path, src, dst, 0, len(path) - 1, TxStatus.INSUFFICIENT_FUNDS)
        for u, v in pairwise(path):
            self.transfer(u, v, amount)
        return TxData(path, src, dst, amount, len(path) - 1, TxStatus.SUCCESS)

    def get_balance(self, node: str) -> int:
        """Returns the outgoing balance of a node on a graph."""
        return sum(self[node].values())

    def get_node(self, node: str) -> Node:
        """Returns a node instance that belongs to the graph."""
        if node not in self:
            raise KeyError("Node does not exist in graph.")
        return Node(node, self)

    def max_sendable(self, src: str, dst: str) -> int:
        """Returns the maximum amount that can be sent from the source
        to the destination node (assuming the shortest path)."""
        path, _ = self.dijkstra(src, dst)
        return min(self[u][v] for u, v in pairwise(path))


@dataclass
class Node:
    """Wrapper class that allows easy access to a graph from a node.
    Supports retrieving balances and channel information, and performing
    graph operations that involve a node.
    """

    name: str
    graph: Graph = field(repr=False)

    def __post_init__(self) -> None:
        if self.name not in self.graph:
            raise ValueError("Node does not exist on graph.")

    def __str__(self) -> str:
        return self.name

    @property
    def balance(self) -> int:
        return self.graph.get_balance(self.name)

    @property
    def channels(self) -> dict[str, int]:
        return self.graph[self.name]

    def send(self, node: Self | str, amount=DEFAULT_TRANSACTION_VALUE) -> TxData:
        return self.graph.send(self.name, str(node), amount)

    def open_channel(
        self,
        node: Self | str,
        outbound=DEFAULT_CHANNEL_BALANCE,
        inbound=DEFAULT_CHANNEL_BALANCE,
    ) -> None:
        self.graph.open_channel(self.name, str(node), outbound, inbound)

    def close_channel(self, node: Self | str) -> None:
        self.graph.close_channel(self.name, str(node))


def main() -> None:
    graph = Graph.from_dict(
        {
            "Alice": {"Bob": 4, "Carol": 3},
            "Bob": {"Alice": 1, "Carol": 4, "David": 3},
            "Carol": {"Alice": 3, "Bob": 3, "David": 0, "Ella": 1},
            "David": {"Bob": 1, "Carol": 3, "Frank": 3},
            "Ella": {"Carol": 3, "Frank": 1},
            "Frank": {"David": 3, "Ella": 3},
        }
    )
    graph.send("Alice", "Frank", 1)
    print(graph)


if __name__ == "__main__":
    main()
