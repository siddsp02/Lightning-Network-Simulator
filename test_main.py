from decimal import Decimal

import pytest

from main import close_channel, graph, open_channel, reset_graph, transfer


def test_open_channel() -> None:
    reset_graph(graph)
    # Test opening a normal channel between two nodes in `graph`.
    open_channel(
        graph,
        "a",
        "b",
        Decimal("2.5"),
        Decimal("2.5"),
    )
    assert graph["a"]["b"] == Decimal("2.5") and graph["b"]["a"] == Decimal("2.5")

    # Test opening a channel where both nodes are given a negative balance.
    with pytest.raises(ValueError):
        open_channel(
            graph,
            "a",
            "c",
            Decimal("-2.5"),
            Decimal("-2.5"),
        )

    # Test opening a channel with a negative balance on just one side.
    with pytest.raises(ValueError):
        open_channel(
            graph,
            "a",
            "d",
            Decimal("-2.5"),
            Decimal("3.0"),
        )

    # Test opening a channel to a node that does not exist.
    with pytest.raises(ValueError):
        open_channel(
            graph,
            "a",
            "z",
            Decimal("2.5"),
            Decimal("2.5"),
        )

    # Test opening a channel from a node that does not exist.
    with pytest.raises(ValueError):
        open_channel(
            graph,
            "z",
            "a",
            Decimal("2.5"),
            Decimal("2.5"),
        )

    # Test opening a channel that has already been opened.
    with pytest.raises(Exception):
        open_channel(
            graph,
            "a",
            "b",
            Decimal("2.5"),
            Decimal("2.5"),
        )

    # Test opening a channel from a node to itself.
    with pytest.raises(ValueError):
        open_channel(
            graph,
            "a",
            "a",
            Decimal("2.5"),
            Decimal("2.5"),
        )

    reset_graph(graph)


def test_close_channel() -> None:
    # Try closing a channel between two nodes in `graph`.
    with pytest.raises(Exception):
        close_channel(graph, "a", "b")

    # Test closing a channel from a node that does not exist.
    with pytest.raises(ValueError):
        close_channel(graph, "z", "a")

    # Test closing a channel to a node that does not exist.
    with pytest.raises(ValueError):
        close_channel(graph, "a", "z")

    # Test closing a channel that has already been closed.
    with pytest.raises(Exception):
        close_channel(graph, "a", "b")


def test_transfer() -> None:
    # Try making a normal transfer.
    reset_graph(graph)
    open_channel(graph, "a", "b", Decimal("1"), Decimal("1"))
    transfer(graph, "a", "b", Decimal("0.5"))
    assert graph["a"]["b"] == Decimal("0.5") and graph["b"]["a"] == Decimal("1.5")


def test_dijkstra() -> None:
    assert False


def test_send() -> None:
    assert False
