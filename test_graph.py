from collections import deque
from decimal import Decimal

import pytest

import graph

network = graph.create("abcdefgh")


def test_open_channel() -> None:
    # Test opening a normal channel between two nodes.
    graph.open_channel(
        network,
        "a",
        "b",
        Decimal("2.5"),
        Decimal("2.5"),
    )
    assert network["a"]["b"] == Decimal("2.5") and network["b"]["a"] == Decimal("2.5")

    # Test opening a channel where both nodes are given a negative balance.
    with pytest.raises(ValueError):
        graph.open_channel(
            network,
            "a",
            "c",
            Decimal("-2.5"),
            Decimal("-2.5"),
        )

    # Test opening a channel with a negative balance on just one side.
    with pytest.raises(ValueError):
        graph.open_channel(
            network,
            "a",
            "d",
            Decimal("-2.5"),
            Decimal("3.0"),
        )

    # Test opening a channel to a node that does not exist.
    with pytest.raises(ValueError):
        graph.open_channel(
            network,
            "a",
            "z",
            Decimal("2.5"),
            Decimal("2.5"),
        )

    # Test opening a channel from a node that does not exist.
    with pytest.raises(ValueError):
        graph.open_channel(
            network,
            "z",
            "a",
            Decimal("2.5"),
            Decimal("2.5"),
        )

    # Test opening a channel that has already been opened.
    with pytest.raises(Exception):
        graph.open_channel(
            network,
            "a",
            "b",
            Decimal("2.5"),
            Decimal("2.5"),
        )

    # Test opening a channel from a node to itself.
    with pytest.raises(ValueError):
        graph.open_channel(
            network,
            "a",
            "a",
            Decimal("2.5"),
            Decimal("2.5"),
        )

    graph.reset(network)


def test_close_channel() -> None:
    # Try closing a channel between two nodes in `graph`.
    with pytest.raises(Exception):
        graph.close_channel(network, "a", "b")

    # Test closing a channel from a node that does not exist.
    with pytest.raises(ValueError):
        graph.close_channel(network, "z", "a")

    # Test closing a channel to a node that does not exist.
    with pytest.raises(ValueError):
        graph.close_channel(network, "a", "z")

    # Test closing a channel that has already been closed.
    with pytest.raises(Exception):
        graph.close_channel(network, "a", "b")


def test_transfer() -> None:
    # Try making a normal transfer.
    graph.reset(network)
    graph.open_channel(network, "a", "b", Decimal("1"), Decimal("1"))
    graph.transfer(network, "a", "b", Decimal("0.5"))
    assert network["a"]["b"] == Decimal("0.5") and network["b"]["a"] == Decimal("1.5")


def test_dijkstra() -> None:
    graph.reset(network)
    # Intialize some default values.
    network["a"]["b"] = Decimal(1)
    network["b"]["a"] = Decimal(1)
    network["b"]["c"] = Decimal(1)
    network["c"]["b"] = Decimal(1)
    network["c"]["d"] = Decimal(1)
    network["d"]["c"] = Decimal(1)
    # Check the shortest path from a to d.
    assert graph.dijkstra(network, "a", "d") == (
        deque(["a", "b", "c", "d"]),
        Decimal(3),
    )


def test_send() -> None:
    graph.reset(network)
    network["a"]["b"] = Decimal(1)
    network["b"]["a"] = Decimal(1)
    with pytest.raises(Exception):
        graph.send(network, "a", "b", Decimal(1.5))
