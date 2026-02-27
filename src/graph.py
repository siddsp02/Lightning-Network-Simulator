from __future__ import annotations

import textwrap
from collections import deque
from dataclasses import dataclass, field
from itertools import pairwise
from pprint import pformat
from typing import Iterable, Iterator, MutableMapping, Self, overload

try:
    from src.algorithms import bfs, dijkstra
    from src.utils import TxData, TxStatus
except ImportError:
    from algorithms import bfs, dijkstra
    from utils import TxData, TxStatus

BITCOIN_PRICE = 30_000
SATOSHIS_PER_BITCOIN = 100_000_000

# Consider as "infinity" or our maximum edge cost.
# Any edge with a cost greater than or equal to
# this value is unreachable in a graph.
INFINITY = 0xFFFFFFFFFFFFFFFF

MIN_TRANSACTION_VALUE = 5
MAX_TRANSACTION_VALUE = 250
DEFAULT_TRANSACTION_VALUE = MIN_TRANSACTION_VALUE
DEFAULT_CHANNEL_CAPACITY = MAX_TRANSACTION_VALUE * 2
DEFAULT_CHANNEL_BALANCE = MAX_TRANSACTION_VALUE


class Graph[K, V: int](MutableMapping):
    """Data type for representing a graph on the network. The underlying
    data structure for storing nodes and channel balances is a hashtable
    mapping node ids to channel balances with their peers.
    """

    def __init__(self, nodes: Iterable[K]) -> None:
        self.graph = {node: {} for node in nodes}

    def __repr__(self) -> str:
        fmt = pformat(self.graph)
        return "{}(\n{},\n)".format(type(self).__name__, textwrap.indent(fmt, " " * 4))

    @overload
    def __getitem__(self, k: K) -> dict[K, V]: ...

    @overload
    def __getitem__(self, k: tuple[K, K]) -> V: ...

    def __getitem__(self, k):
        if isinstance(k, tuple):
            u, v = k
            return self.graph[u][v]
        else:
            return self.graph[k]

    @overload
    def __setitem__(self, k: K, v: dict[K, V]) -> None: ...

    @overload
    def __setitem__(self, k: tuple[K, K], v: V) -> None: ...

    def __setitem__(self, k, v):
        if isinstance(k, tuple):
            x, y = k
            self.graph[x][y] = v
        else:
            self.graph[k] = v

    def __delitem__(self, k: K | tuple[K, K]) -> None:
        if isinstance(k, tuple):
            u, v = k
            del self.graph[u][v]
            del self.graph[v][u]
        else:
            del self.graph[k]
            for node in self.nodes:
                if k in self.graph[node]:
                    del self.graph[node][k]

    def __iter__(self) -> Iterator[K]:
        return iter(self.graph)

    def __len__(self) -> int:
        return len(self.graph)

    @classmethod
    def from_dict(cls, graph: dict[K, dict[K, V]]) -> Self:
        """Returns a graph instance as a wrapper over a dict.

        Note that this class contains a reference to the dict
        and does not copy its values.
        """
        ret = cls(graph.keys())
        ret.graph = graph
        return ret

    @property
    def nodes(self) -> list[K]:
        return sorted(self)

    def reset(self) -> None:
        "Utility function for resetting graph values and channel data."
        self.update((node, {}) for node in self.nodes)

    def open_channel(
        self, u: K, v: K, x: V = DEFAULT_CHANNEL_BALANCE, y: V = DEFAULT_CHANNEL_BALANCE
    ) -> None:
        "Opens a channel between nodes `u` and `v`, where `u -> v = x` and `v -> u = y`."
        if self.get((u, v)) is not None:
            raise Exception("Channel/edge already exists.")
        if u not in self or v not in self:
            raise ValueError("Node passed as parameter does not exist.")
        if u == v:
            raise ValueError("Node cannot open channel with itself.")
        if x < 0 or y < 0:
            raise ValueError("Channel amount cannot be negative.")

        self[u][v] = x
        self[v][u] = y

    def close_channel(self, u: K, v: K) -> None:
        "Closes a channel between nodes `u` and `v`. Channel is deleted from graph."
        if u not in self or v not in self:
            raise ValueError("Node passed as parameter does not exist.")
        if self[u].get(v) is None:
            raise Exception("Cannot close a channel that hasn't been opened.")

        del self[u][v]
        del self[v][u]

    def transfer(self, u: K, v: K, amount: V = DEFAULT_TRANSACTION_VALUE) -> None:
        "Transfers an amount `amount` from `u` to `v` through a single channel `(u, v)`."
        if self.get((u, v)) is None:
            raise Exception("Edge does not exist.")
        if amount < 0:
            raise ValueError("Transfer amount cannot be negative.")
        if amount > self[u][v]:
            raise ValueError("Insufficient funds.")

        self[u][v] -= amount  # type: ignore
        self[v][u] += amount  # type: ignore

    def edge_cost(self, u: K, v: K) -> V:
        "Returns the cost/weight of an edge (u, v) on a graph."
        return 1 if self.get((u, v)) is not None else INFINITY  # type: ignore

    bfs = bfs

    def dijkstra(self, src: K, dst: K) -> tuple[deque[K], int]:
        return dijkstra(self, src, dst, weight_func=Graph.edge_cost)  # type: ignore

    def send(self, src: K, dst: K, amount: V = DEFAULT_TRANSACTION_VALUE) -> TxData:
        """Sends an amount `amount` from `src` to `dst` based
        on the shortest path between the two if one exists.
        """
        path, cost = self.bfs(src, dst)
        if cost >= INFINITY:
            return TxData(path, src, dst, 0, 0, TxStatus.UNREACHABLE)
        if any(self[u][v] < amount for (u, v) in pairwise(path)):
            return TxData(path, src, dst, 0, len(path) - 1, TxStatus.INSUFFICIENT_FUNDS)
        for u, v in pairwise(path):
            self.transfer(u, v, amount)
        return TxData(path, src, dst, amount, len(path) - 1, TxStatus.SUCCESS)

    def get_balance(self, node: K) -> int:
        "Returns the outgoing balance of a node on a graph."
        return sum(self[node].values())

    # def get_node(self, node: K) -> Node:
    #     "Returns a node instance that belongs to the graph."
    #     if node not in self:
    #         raise KeyError("Node does not exist in graph.")
    #     return Node(node, self)

    def max_sendable(self, src: K, dst: K) -> V:
        """Returns the maximum amount that can be sent from the source
        to the destination node (assuming the shortest path)."""
        path, _ = self.bfs(src, dst)
        return min(self[u][v] for u, v in pairwise(path))


# @dataclass
# class Node[K, V]:
#     """Wrapper class that allows easy access to a graph from a node.
#     Supports retrieving balances and channel information, and performing
#     graph operations that involve a node.
#     """

#     name: K
#     graph: Graph = field(repr=False)

#     def __post_init__(self) -> None:
#         if self.name not in self.graph:
#             raise ValueError("Node does not exist on graph.")

#     def __str__(self) -> str:
#         return str(self.name)

#     @property
#     def balance(self) -> int:
#         return self.graph.get_balance(self.name)

#     @property
#     def channels(self) -> dict[K, V]:
#         return self.graph[self.name]

#     def send(self, node: Self | K, amount: V) -> TxData[K]:
#         return self.graph.send(self.name, str(node), amount)

#     def open_channel(self, node: Self | K, outbound: V, inbound: V) -> None:
#         self.graph.open_channel(self.name, str(node), outbound, inbound)

#     def close_channel(self, node: Self | K) -> None:
#         self.graph.close_channel(self.name, str(node))


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
    del graph["Alice", "Bob"]
    print(graph)


if __name__ == "__main__":
    main()
