# !usr/bin/env python3

from decimal import Decimal
from pprint import pprint

NODES = "abcdefgh"

graph = {node: dict.fromkeys({*NODES} - {node}, Decimal()) for node in NODES}
closed_channels = set()  # type: ignore
opened_channels = set()  # type: ignore


def reset_graph() -> None:
    """Utility function for resetting graph values and channel data."""
    graph.update({node: dict.fromkeys({*NODES} - {node}, Decimal()) for node in NODES})
    closed_channels.clear()
    opened_channels.clear()


def open_channel(u: str, v: str, x: Decimal, y: Decimal) -> None:
    """Opens a channel between nodes `u` and `v`,
    where `u -> v = x` and `v -> u = y`.
    """
    if u == v:
        raise ValueError("Node cannot open channel with itself.")
    if x < 0 or y < 0:
        raise ValueError("Channel amount cannot be negative.")
    if (u, v) in opened_channels:
        raise Exception("Channel has already been opened.")
    # Channels are opened between two nodes.
    channel = (u, v), (v, u)
    # Add channel to opened channels.
    opened_channels.update(channel)
    # Remove channel from closed channels (if it exists).
    for pair in channel:
        closed_channels.discard(pair)
    # Update channel balances.
    graph[u][v] = x
    graph[v][u] = y


def close_channel(u: str, v: str) -> None:
    """Closes a channel between nodes `u` and `v`.
    Balances are reset to 0.
    """
    if (u, v) in closed_channels:
        raise Exception("Cannot close a channel that has already been closed.")
    if (u, v) not in opened_channels:
        raise Exception("Cannot close a channel that hasn't been opened.")
    # Remove channel from opened channels.
    channel = (u, v), (v, u)
    for pair in channel:
        opened_channels.remove(pair)
    # Add channel to closed channels.
    closed_channels.update(channel)
    # Reset channel balances to 0.
    graph[u][v] = Decimal()
    graph[v][u] = Decimal()


def transfer(u: str, v: str, amount: Decimal) -> None:
    """Transfers an amount `amount` from `u` to `v`."""
    if amount < 0:
        raise ValueError("Transfer amount cannot be negative.")
    if (u, v) not in opened_channels:
        raise Exception(f"Channel between nodes {u} and {v} does not exist.")
    graph[u][v] -= amount
    graph[v][u] += amount


def main() -> None:
    ...


if __name__ == "__main__":
    main()
