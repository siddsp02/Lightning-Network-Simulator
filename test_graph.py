from collections import deque
from itertools import pairwise

import pytest

from graph import DEFAULT_CHANNEL_BALANCE, Graph
from utils import TxStatus

graph = Graph("abcdefgh")


def test_open_channel() -> None:
    # Test opening a normal channel between two nodes.
    graph.open_channel(
        "a",
        "b",
        DEFAULT_CHANNEL_BALANCE,
        DEFAULT_CHANNEL_BALANCE,
    )
    assert (
        graph["a"]["b"] == DEFAULT_CHANNEL_BALANCE
        and graph["b"]["a"] == DEFAULT_CHANNEL_BALANCE
    )

    # Test opening a channel where both nodes are given a negative balance.
    with pytest.raises(ValueError):
        graph.open_channel("a", "c", -3, -3)

    # Test opening a channel with a negative balance on just one side.
    with pytest.raises(ValueError):
        graph.open_channel("a", "d", -3, 3)

    # Test opening a channel to a node that does not exist.
    with pytest.raises(ValueError):
        graph.open_channel("a", "z", DEFAULT_CHANNEL_BALANCE, DEFAULT_CHANNEL_BALANCE)

    # Test opening a channel from a node that does not exist.
    with pytest.raises(ValueError):
        graph.open_channel(
            "z",
            "a",
            DEFAULT_CHANNEL_BALANCE,
            DEFAULT_CHANNEL_BALANCE,
        )

    # Test opening a channel that has already been opened.
    with pytest.raises(Exception):
        graph.open_channel(
            "a",
            "b",
            DEFAULT_CHANNEL_BALANCE,
            DEFAULT_CHANNEL_BALANCE,
        )

    # Test opening a channel from a node to itself.
    with pytest.raises(ValueError):
        graph.open_channel(
            "a",
            "a",
            DEFAULT_CHANNEL_BALANCE,
            DEFAULT_CHANNEL_BALANCE,
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
    graph.open_channel("a", "b", DEFAULT_CHANNEL_BALANCE, DEFAULT_CHANNEL_BALANCE)
    graph.transfer("a", "b", DEFAULT_CHANNEL_BALANCE // 2)
    assert (
        graph["a"]["b"] == DEFAULT_CHANNEL_BALANCE // 2
        and graph["b"]["a"] == (DEFAULT_CHANNEL_BALANCE * 3) // 2
    )


def test_dijkstra() -> None:
    graph.reset()
    # Intialize some default values.
    for u, v in pairwise("abcd"):
        graph[u][v] = 1
        graph[v][u] = 1
    # Check the shortest path from a to d.
    assert graph.dijkstra("a", "d") == (deque(["a", "b", "c", "d"]), 3)


def test_send() -> None:
    graph.reset()
    graph["a"]["b"] = 1
    graph["b"]["a"] = 1
    # More test cases will be added soon.
    assert graph.send("a", "b", 2).status == TxStatus.INSUFFICIENT_FUNDS
