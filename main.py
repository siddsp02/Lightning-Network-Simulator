# !usr/bin/env python3

from collections import deque
from decimal import Decimal
from itertools import pairwise
from math import isinf
from pprint import pprint
from typing import Sequence

NODES = "abcdefgh"

Graph = dict[str, dict[str, Decimal]]

inf = Decimal("inf")
graph: Graph = {node: {} for node in NODES}


def create(nodes: Sequence[str] | str) -> Graph:
    return {node: {} for node in nodes}


def reset(graph: Graph) -> None:
    """Utility function for resetting graph values and channel data."""
    graph |= {node: {} for node in NODES}


def open_channel(graph: Graph, u: str, v: str, x=Decimal(1), y=Decimal(1)) -> None:
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


def close_channel(graph: Graph, u: str, v: str) -> None:
    """Closes a channel between nodes `u` and `v`. Channel is deleted from graph."""
    if u not in graph or v not in graph:
        raise ValueError("Node passed as parameter does not exist.")
    if graph[u].get(v) is None:
        raise Exception("Cannot close a channel that hasn't been opened.")

    del graph[u][v]
    del graph[v][u]


def transfer(graph: Graph, u: str, v: str, amount: Decimal) -> None:
    """Transfers an amount `amount` from `u` to `v` through a single channel (u, v)."""
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


def edgecost(graph: Graph, u: str, v: str) -> Decimal:
    """Returns the cost/weight of an edge (u, v) on a graph."""
    try:
        graph[u][v]
    except KeyError:
        return inf
    return Decimal(1)


def dijkstra(graph: Graph, src: str, dst: str) -> tuple[deque[str], Decimal]:
    """Dijkstra's shortest path algorithm for finding the shortest
    path between any two given vertices or nodes on a graph.
    """
    dist = dict.fromkeys(graph, inf)
    prev = dict.fromkeys(graph)
    dist[src] = Decimal()
    unmarked = set(graph)
    while unmarked:
        u = min(unmarked, key=dist.get)  # type: ignore
        unmarked.remove(u)
        if u == dst:
            break
        neighbours = graph[u].keys()
        for v in neighbours & unmarked:
            alt = dist[u] + edgecost(graph, u, v)
            if alt < dist[v]:
                dist[v] = alt
                prev[v] = u
    path = deque()  # type: ignore
    pred = dst
    while pred is not None:
        path.appendleft(pred)
        pred = prev.get(pred)  # type: ignore
    return path, dist[dst]


def send(graph: Graph, src: str, dst: str, amount=Decimal(1)) -> None:
    """Sends an amount `amount` from `src` to `dst` based
    on the shortest path between the two if one exists.
    """
    path, cost = dijkstra(graph, src, dst)
    if isinf(cost):
        raise ValueError("Node is unreachable.")
    if any(graph[u][v] < amount for (u, v) in pairwise(path)):
        raise Exception("Path is unreachable due to insufficient funds.")
    for u, v in pairwise(path):
        transfer(graph, u, v, amount)


def main() -> None:
    open_channel(graph, "a", "b", Decimal("1"), Decimal("1"))
    transfer(graph, "a", "b", Decimal("-0.5"))
    pprint(graph)
    close_channel(graph, "a", "b")


if __name__ == "__main__":
    main()
