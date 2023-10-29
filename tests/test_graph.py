import random
from collections import deque
from itertools import combinations, pairwise

import pytest

from src.graph import DEFAULT_CHANNEL_BALANCE, Graph
from src.utils import TxStatus

NODES = "abcdefgh"
VALID_GRAPH_EDGES = list(combinations(NODES, 2))
NEGATIVE_VALUES = [random.sample(range(-100, 0), k=10) for _ in range(2)]

graph = Graph(NODES)


@pytest.mark.parametrize("a, b", VALID_GRAPH_EDGES)
def test_open_channel_valid_edges(a, b) -> None:
    graph.open_channel(a, b)
    assert (
        graph[a][b] == DEFAULT_CHANNEL_BALANCE
        and graph[b][a] == DEFAULT_CHANNEL_BALANCE
    )
    graph.reset()


def test_open_channel() -> None:
    graph.reset()
    # Test opening a channel where both nodes are given a negative balance.
    with pytest.raises(ValueError):
        graph.open_channel("a", "c", -3, -3)

    # Test opening a channel with a negative balance on just one side.
    with pytest.raises(ValueError):
        graph.open_channel("a", "d", -3, 3)

    # Test opening a channel to a node that does not exist.
    with pytest.raises(ValueError):
        graph.open_channel("a", "z")

    # Test opening a channel from a node that does not exist.
    with pytest.raises(ValueError):
        graph.open_channel("z", "a")

    graph.open_channel("a", "b")
    # Test opening a channel that has already been opened.
    with pytest.raises(Exception):
        graph.open_channel("a", "b")

    # Test opening a channel from a node to itself.
    with pytest.raises(ValueError):
        graph.open_channel("a", "a")

    graph.reset()


@pytest.mark.parametrize("a, b", [("a", "b")])
def test_close_channel_never_opened(a: str, b: str) -> None:
    graph.reset()
    with pytest.raises(Exception):
        graph.close_channel(a, b)


@pytest.mark.parametrize("a, b", [("a", "z"), ("z", "a"), ("q", "r"), ("r", "q")])
def test_close_channel_invalid_nodes(a: str, b: str) -> None:
    with pytest.raises(Exception):
        graph.close_channel(a, b)


@pytest.mark.parametrize("a, b", VALID_GRAPH_EDGES)
def test_close_opened_channel(a, b) -> None:
    graph.open_channel(a, b)
    try:
        graph.close_channel(a, b)
    except Exception as e:
        assert False, f"Exception {e} was raised."


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
    graph.reset()


def test_send() -> None:
    graph.reset()
    graph["a"]["b"] = 1
    graph["b"]["a"] = 1
    # More test cases will be added soon.
    assert graph.send("a", "b", 2).status == TxStatus.INSUFFICIENT_FUNDS
    assert graph.send("a", "b", 1).status == TxStatus.SUCCESS
    with pytest.raises(ValueError):
        graph.send("a", "b", -3)
