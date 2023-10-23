from __future__ import annotations

import textwrap
from collections import deque
from dataclasses import dataclass, field
from decimal import Decimal
from itertools import pairwise
from pprint import pformat
from types import MappingProxyType
from typing import Iterable, Iterator, Mapping, MutableMapping, Self

from utils import TxData, TxStatus

MIN_TRANSACTION_VALUE = Decimal("5")
MAX_TRANSACTION_VALUE = Decimal("250")
DEFAULT_TRANSACTION_VALUE = MIN_TRANSACTION_VALUE
DEFAULT_CHANNEL_CAPACITY = MAX_TRANSACTION_VALUE * 2
DEFAULT_CHANNEL_BALANACE = MAX_TRANSACTION_VALUE

inf = Decimal("inf")


class Graph(MutableMapping):
    def __init__(self, nodes: Iterable[str] | str) -> None:
        self.nodes = nodes  # type: ignore
        self.graph = {node: {} for node in self.nodes}  # type: ignore

    def __repr__(self) -> str:
        fmt = pformat(self.graph)
        return "{}(\n{},\n)".format(type(self).__name__, textwrap.indent(fmt, " " * 4))

    def __getitem__(self, k: str) -> dict[str, Decimal]:
        return self.graph[k]

    def __setitem__(self, k: str, v: dict[str, Decimal]) -> None:
        self.graph[k] = v

    def __delitem__(self, k: str) -> None:
        del self.graph[k]

    def __iter__(self) -> Iterator[str]:
        return iter(self.graph)

    def __len__(self) -> int:
        return len(self.graph)

    @property
    def nodes(self) -> list[str]:
        return sorted(self.nodeset)

    @nodes.setter
    def nodes(self, nodes: Iterable[str]) -> None:
        self.nodeset = set(nodes)

    def reset(self) -> None:
        """Utility function for resetting graph values and channel data."""
        self.update((node, {}) for node in self.nodes)

    def open_channel(
        self, u: str, v: str, x=DEFAULT_CHANNEL_BALANACE, y=DEFAULT_CHANNEL_BALANACE
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

    def close_channel(self, u: str, v: str) -> None:
        """Closes a channel between nodes `u` and `v`. Channel is deleted from graph."""
        if u not in self or v not in self:
            raise ValueError("Node passed as parameter does not exist.")
        if self[u].get(v) is None:
            raise Exception("Cannot close a channel that hasn't been opened.")

        del self[u][v]
        del self[v][u]

    def transfer(self, u: str, v: str, amount: Decimal) -> None:
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

    def edgecost(self, u: str, v: str) -> Decimal:
        """Returns the cost/weight of an edge (u, v) on a graph."""
        try:
            self[u][v]
        except KeyError:
            return inf
        return Decimal(1)

    def dijkstra(self, src: str, dst: str) -> tuple[deque[str], Decimal]:
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
        path = deque()  # type: ignore
        pred = dst
        while pred is not None:
            path.appendleft(pred)
            pred = prev.get(pred)  # type: ignore
        return path, dist[dst]

    def send(self, src: str, dst: str, amount=DEFAULT_TRANSACTION_VALUE) -> TxData:
        """Sends an amount `amount` from `src` to `dst` based
        on the shortest path between the two if one exists.
        """
        path, cost = self.dijkstra(src, dst)
        if cost == inf:
            return TxData(path, src, dst, 0, TxStatus.UNREACHABLE)
        if any(self[u][v] < amount for (u, v) in pairwise(path)):
            return TxData(path, src, dst, len(path) - 1, TxStatus.INSUFFICIENT_FUNDS)
            # raise Exception("Path is unreachable due to insufficient funds.")
        for u, v in pairwise(path):
            self.transfer(u, v, amount)
        return TxData(path, src, dst, len(path) - 1, TxStatus.SUCCESS)

    def get_balance(self, node: str) -> Decimal:
        """Returns the outgoing balance of a node on a graph."""
        return sum(self[node].values())  # type: ignore

    def get_node(self, node: str) -> Node:
        """Returns a node instance that belongs to the graph."""
        if node not in self.nodeset:
            raise KeyError("Node does not exist in graph.")
        return Node(node, self)


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
    def balance(self) -> Decimal:
        return self.graph.get_balance(self.name)

    @property
    def channels(self) -> Mapping[str, Decimal]:
        return MappingProxyType(self.graph[self.name])

    def send(self, node: Self | str, amount=DEFAULT_TRANSACTION_VALUE) -> TxData:
        return self.graph.send(self.name, str(node))

    def open_channel(
        self,
        node: Self | str,
        outbound=DEFAULT_CHANNEL_BALANACE,
        inbound=DEFAULT_CHANNEL_BALANACE,
    ) -> None:
        self.graph.open_channel(self.name, str(node), outbound, inbound)

    def close_channel(self, node: Self | str) -> None:
        self.graph.close_channel(self.name, str(node))
