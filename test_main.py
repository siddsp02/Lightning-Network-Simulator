from decimal import Decimal

import pytest

from main import (
    close_channel,
    graph,
    open_channel,
    reset_graph,
    transfer,
    opened_channels,
    closed_channels,
)


def test_open_channel() -> None:
    reset_graph(graph, opened_channels, closed_channels)
    # Test opening a normal channel between two nodes in `graph`.
    open_channel(
        graph,
        opened_channels,
        closed_channels,
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
            opened_channels,
            closed_channels,
            "a",
            "c",
            Decimal("-2.5"),
            Decimal("-2.5"),
        )

    # Test opening a channel with a negative balance on just one side.
    with pytest.raises(ValueError):
        open_channel(
            graph,
            opened_channels,
            closed_channels,
            "a",
            "d",
            Decimal("-2.5"),
            Decimal("3.0"),
        )

    # Test opening a channel to a node that does not exist.
    with pytest.raises(ValueError):
        open_channel(
            graph,
            opened_channels,
            closed_channels,
            "a",
            "z",
            Decimal("2.5"),
            Decimal("2.5"),
        )

    # Test opening a channel from a node that does not exist.
    with pytest.raises(ValueError):
        open_channel(
            graph,
            opened_channels,
            closed_channels,
            "z",
            "a",
            Decimal("2.5"),
            Decimal("2.5"),
        )

    # Test opening a channel that has already been opened.
    with pytest.raises(Exception):
        open_channel(
            graph,
            opened_channels,
            closed_channels,
            "a",
            "b",
            Decimal("2.5"),
            Decimal("2.5"),
        )

    # Test opening a channel from a node to itself.
    with pytest.raises(ValueError):
        open_channel(
            graph,
            opened_channels,
            closed_channels,
            "a",
            "a",
            Decimal("2.5"),
            Decimal("2.5"),
        )


def test_close_channel() -> None:
    # Try closing a channel between two nodes in `graph`.
    close_channel(graph, opened_channels, closed_channels, "a", "b")
    assert graph["a"]["b"] == Decimal("0") and graph["b"]["a"] == Decimal("0")

    # Test closing a channel from a node that does not exist.
    with pytest.raises(ValueError):
        close_channel(graph, opened_channels, closed_channels, "z", "a")

    # Test closing a channel to a node that does not exist.
    with pytest.raises(ValueError):
        close_channel(graph, opened_channels, closed_channels, "a", "z")

    # Test closing a channel that has already been closed.
    with pytest.raises(Exception):
        close_channel(graph, opened_channels, closed_channels, "a", "b")


def test_transfer() -> None:
    # Try making a normal transfer.
    graph["a"]["b"] = Decimal("5")
    graph["b"]["a"] = Decimal("5")
    opened_channels.update([("a", "b"), ("b", "a")])
    transfer(graph, opened_channels, "a", "b", Decimal("2.5"))
    assert graph["a"]["b"] == Decimal("2.5") and graph["b"]["a"] == Decimal("7.5")
