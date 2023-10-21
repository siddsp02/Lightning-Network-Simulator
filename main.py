# !usr/bin/env python3

from decimal import Decimal
from pprint import pprint
from typing import MutableMapping

NODES = "abcdefgh"

graph = {node: {} for node in NODES}  # type: ignore


def reset_graph(graph: dict[str, dict[str, Decimal]]) -> None:
    """Utility function for resetting graph values and channel data."""
    graph.update((node, {}) for node in NODES)


def open_channel(
    graph: dict[str, dict[str, Decimal]], u: str, v: str, x: Decimal, y: Decimal
) -> None:
    """Opens a channel between nodes `u` and `v`, where `u -> v = x` and `v -> u = y`."""
    if u not in graph or v not in graph:
        raise ValueError("Node passed as parameter does not exist.")
    if u == v:
        raise ValueError("Node cannot open channel with itself.")
    if x < 0 or y < 0:
        raise ValueError("Channel amount cannot be negative.")
    if graph[u].get(v) is not None:
        raise Exception("Channel has already been opened.")

    graph[u][v] = x
    graph[v][u] = y


def close_channel(graph: dict[str, dict[str, Decimal]], u: str, v: str) -> None:
    """Closes a channel between nodes `u` and `v`. Channel is deleted from graph."""
    if u not in graph or v not in graph:
        raise ValueError("Node passed as parameter does not exist.")
    if graph[u].get(v) is None:
        raise Exception("Cannot close a channel that hasn't been opened.")

    del graph[u][v]
    del graph[v][u]


def transfer(
    graph: dict[str, dict[str, Decimal]], u: str, v: str, amount: Decimal
) -> None:
    """Transfers an amount `amount` from `u` to `v`."""
    if u not in graph or v not in graph:
        raise ValueError("Node passed as parameter does not exist.")
    if amount < 0:
        raise ValueError("Transfer amount cannot be negative.")
    if graph[u].get(v) is None:
        raise Exception(f"Channel between nodes {u} and {v} has not been opened.")
    if amount > graph[u][v]:
        raise ValueError("Insufficient funds.")

    graph[u][v] -= amount
    graph[v][u] += amount


def main() -> None:
    open_channel(graph, "a", "b", Decimal("1"), Decimal("1"))
    transfer(graph, "a", "b", Decimal("-0.5"))
    pprint(graph)
    close_channel(graph, "a", "b")


if __name__ == "__main__":
    main()
