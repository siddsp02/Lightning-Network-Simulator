from __future__ import annotations

import textwrap
from collections import deque
from dataclasses import dataclass, field
from decimal import Decimal
from itertools import pairwise
from pprint import pformat
from types import MappingProxyType
from typing import Generator, Iterable, Iterator, Mapping, MutableMapping, Self

from utils import TxData, TxStatus

MIN_TRANSACTION_VALUE = Decimal("5")
MAX_TRANSACTION_VALUE = Decimal("250")
DEFAULT_TRANSACTION_VALUE = MIN_TRANSACTION_VALUE
DEFAULT_CHANNEL_CAPACITY = MAX_TRANSACTION_VALUE * 2
DEFAULT_CHANNEL_BALANACE = MAX_TRANSACTION_VALUE

inf = Decimal("inf")

# These will be changed to TypeVars later.

K = str
V = Decimal | int


class Graph(MutableMapping[K, MutableMapping[K, V]]):
    """Data type for representing a graph on the network. The underlying
    data structure for storing nodes and channel balances is a hashtable
    mapping node "ids" to channel balances with its peers.
    """

    def __init__(self, nodes: Iterable[K]) -> None:
        self.nodes = nodes  # type: ignore
        self.graph = {node: {} for node in self.nodes}  # type: ignore

    def __repr__(self) -> str:
        fmt = pformat(self.graph)
        return "{}(\n{},\n)".format(type(self).__name__, textwrap.indent(fmt, " " * 4))

    def __getitem__(self, k: K) -> MutableMapping[K, V]:
        return self.graph[k]

    def __setitem__(self, k: K, v: MutableMapping[K, V]) -> None:
        self.graph[k] = v  # type: ignore

    def __delitem__(self, k: K) -> None:
        del self.graph[k]

    def __iter__(self) -> Iterator[K]:
        return iter(self.graph)

    def __len__(self) -> int:
        return len(self.graph)

    @property
    def nodes(self) -> list[K]:
        return sorted(self.nodeset)  # type: ignore

    @nodes.setter
    def nodes(self, nodes: Iterable[K]) -> None:
        self.nodeset = set(nodes)

    def reset(self) -> None:
        """Utility function for resetting graph values and channel data."""
        self.update((node, {}) for node in self.nodes)

    def open_channel(
        self,
        u: K,
        v: K,
        x: V = DEFAULT_CHANNEL_BALANACE,
        y: V = DEFAULT_CHANNEL_BALANACE,
    ) -> None:
        """Opens a channel between nodes `u` and `v`, where `u -> v = x` and `v -> u = y`."""
        if u not in self.nodeset or v not in self.nodeset:
            raise ValueError("Node passed as parameter does not exist.")
        if u == v:
            raise ValueError("Node cannot open channel with itself.")
        if x < 0 or y < 0:
            raise ValueError("Channel amount cannot be negative.")
        if self[u].get(v) is not None:
            raise Exception("Channel has already been opened.")

        self[u][v] = x
        self[v][u] = y

    def close_channel(self, u: K, v: K) -> None:
        """Closes a channel between nodes `u` and `v`. Channel is deleted from graph."""
        if u not in self or v not in self:
            raise ValueError("Node passed as parameter does not exist.")
        if self[u].get(v) is None:
            raise Exception("Cannot close a channel that hasn't been opened.")

        del self[u][v]
        del self[v][u]

    def transfer(self, u: K, v: K, amount: V) -> None:
        """Transfers an amount `amount` from `u` to `v` through a single channel (u, v)."""
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

    def edgecost(self, u: K, v: K) -> V:
        """Returns the cost/weight of an edge (u, v) on a graph."""
        try:
            self[u][v]
        except KeyError:
            return inf
        return Decimal(1)

    def dijkstra(self, src: K, dst: K) -> tuple[deque[K], V]:
        """Dijkstra's shortest path algorithm for finding the shortest
        path between any two given vertices or nodes on a graph.

        References:
            - https://github.com/siddsp02/Dijkstras-Algorithm/blob/main/dijkstra.py
            - https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm
        """
        dist = dict.fromkeys(self, inf)
        prev = dict.fromkeys(self)
        dist[src] = Decimal()
        unmarked = set(self)
        while unmarked:
            u = min(unmarked, key=dist.get)  # type: ignore
            unmarked.remove(u)
            if u == dst:
                break
            neighbours = self[u].keys()
            for v in neighbours & unmarked:
                alt = dist[u] + self.edgecost(u, v)
                if alt < dist[v]:
                    dist[v] = alt
                    prev[v] = u
        path = deque[K]()
        pred = dst
        while pred is not None:
            path.appendleft(pred)
            pred = prev.get(pred)  # type: ignore
        return path, dist[dst]

    def send(self, src: K, dst: K, amount: V = DEFAULT_TRANSACTION_VALUE) -> TxData:
        """Sends an amount `amount` from `src` to `dst` based
        on the shortest path between the two if one exists.
        """
        path, cost = self.dijkstra(src, dst)
        if cost == inf:
            return TxData(path, src, dst, 0, 0, TxStatus.UNREACHABLE)
        if any(self[u][v] < amount for (u, v) in pairwise(path)):
            return TxData(path, src, dst, 0, len(path) - 1, TxStatus.INSUFFICIENT_FUNDS)
        for u, v in pairwise(path):
            self.transfer(u, v, amount)
        return TxData(path, src, dst, amount, len(path) - 1, TxStatus.SUCCESS)

    def get_balance(self, node: K) -> V:
        """Returns the outgoing balance of a node on a graph."""
        return sum(self[node].values())  # type: ignore

    def get_node(self, node: K) -> Node:
        """Returns a node instance that belongs to the graph."""
        if node not in self.nodeset:
            raise KeyError("Node does not exist in graph.")
        return Node(node, self)

    def max_sendable(self, src: K, dst: K) -> V:
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
        if self.name not in self.graph.nodeset:
            raise ValueError("Node does not exist on graph.")

    def __str__(self) -> str:
        return self.name

    @property
    def balance(self) -> Decimal | int:
        return self.graph.get_balance(self.name)

    @property
    def channels(self) -> Mapping[str, Decimal | int]:
        return MappingProxyType(self.graph[self.name])

    def send(self, node: Self | str, amount: V = DEFAULT_TRANSACTION_VALUE) -> TxData:
        return self.graph.send(self.name, str(node), amount)

    def open_channel(
        self,
        node: Self | str,
        outbound=DEFAULT_CHANNEL_BALANACE,
        inbound=DEFAULT_CHANNEL_BALANACE,
    ) -> None:
        self.graph.open_channel(self.name, str(node), outbound, inbound)

    def close_channel(self, node: Self | str) -> None:
        self.graph.close_channel(self.name, str(node))


def main() -> None:
    graph = Graph(["Alice", "Bob", "Carol", "David", "Ella", "Frank"])
    graph.update(
        {
            "Alice": {"Bob": 4, "Carol": 3},
            "Bob": {"Alice": 1, "Carol": 4, "David": 3},
            "Carol": {"Alice": 3, "Bob": 3, "David": 0, "Ella": 1},
            "David": {"Bob": 1, "Carol": 3, "Frank": 3},
            "Ella": {"Carol": 3, "Frank": 1},
            "Frank": {"David": 3, "Ella": 3},
        }
    )
    alice = graph.get_node("Alice")
    print(alice.send("Frank", 1))
    # print(graph.send("Alice", "Frank", 2))
    print(graph)


if __name__ == "__main__":
    main()
