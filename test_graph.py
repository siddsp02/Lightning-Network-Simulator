from collections import deque
from decimal import Decimal
from itertools import pairwise

import pytest

from graph import Graph

graph = Graph("abcdefgh")


def test_open_channel() -> None:
    # Test opening a normal channel between two nodes.
    graph.open_channel(
        "a",
        "b",
        Decimal("2.5"),
        Decimal("2.5"),
    )
    assert graph["a"]["b"] == Decimal("2.5") and graph["b"]["a"] == Decimal("2.5")

    # Test opening a channel where both nodes are given a negative balance.
    with pytest.raises(ValueError):
        graph.open_channel(
            "a",
            "c",
            Decimal("-2.5"),
            Decimal("-2.5"),
        )

    # Test opening a channel with a negative balance on just one side.
    with pytest.raises(ValueError):
        graph.open_channel(
            "a",
            "d",
            Decimal("-2.5"),
            Decimal("3.0"),
        )

    # Test opening a channel to a node that does not exist.
    with pytest.raises(ValueError):
        graph.open_channel(
            "a",
            "z",
            Decimal("2.5"),
            Decimal("2.5"),
        )

    # Test opening a channel from a node that does not exist.
    with pytest.raises(ValueError):
        graph.open_channel(
            "z",
            "a",
            Decimal("2.5"),
            Decimal("2.5"),
        )

    # Test opening a channel that has already been opened.
    with pytest.raises(Exception):
        graph.open_channel(
            "a",
            "b",
            Decimal("2.5"),
            Decimal("2.5"),
        )

    # Test opening a channel from a node to itself.
    with pytest.raises(ValueError):
        graph.open_channel(
            "a",
            "a",
            Decimal("2.5"),
            Decimal("2.5"),
        )

    graph.reset()


def test_close_channel() -> None:
    # Try closing a channel between two nodes in `graph`.
    with pytest.raises(Exception):
        graph.close_channel("a", "b")

    # Test closing a channel from a node that does not exist.
    with pytest.raises(ValueError):
        graph.close_channel("z", "a")

    # Test closing a channel to a node that does not exist.
    with pytest.raises(ValueError):
        graph.close_channel("a", "z")

    # Test closing a channel that has already been closed.
    with pytest.raises(Exception):
        graph.close_channel("a", "b")


def test_transfer() -> None:
    # Try making a normal transfer.
    graph.reset()
    graph.open_channel("a", "b", Decimal("1"), Decimal("1"))
    graph.transfer("a", "b", Decimal("0.5"))
    assert graph["a"]["b"] == Decimal("0.5") and graph["b"]["a"] == Decimal("1.5")


def test_dijkstra() -> None:
    graph.reset()
    # Intialize some default values.
    for u, v in pairwise("abcd"):
        graph[u][v] = Decimal(1)
        graph[v][u] = Decimal(1)
    # Check the shortest path from a to d.
    assert graph.dijkstra("a", "d") == (
        deque(["a", "b", "c", "d"]),
        Decimal(3),
    )


def test_send() -> None:
    graph.reset()
    graph["a"]["b"] = Decimal(1)
    graph["b"]["a"] = Decimal(1)
    with pytest.raises(Exception):
        graph.send("a", "b", Decimal(1.5))
