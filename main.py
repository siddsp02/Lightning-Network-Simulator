# !usr/bin/env python3

from decimal import Decimal

NODES = "abcdefgh"

graph = {node: dict.fromkeys({*NODES} - {node}, Decimal()) for node in NODES}
closed_channels = set()  # type: ignore
opened_channels = set()  # type: ignore


def open_channel(u: str, v: str, x: Decimal, y: Decimal) -> None:
    """Opens a channel between nodes `u` and `v`,
    where `u -> v = x` and `v -> u = y`.
    """
    if x < 0 or y < 0:
        raise ValueError("Channel amount cannot be negative.")
    if (u, v) in opened_channels:
        raise Exception("Channel has already been opened.")
    graph[u][v] = x
    graph[v][u] = y
    opened_channels.update([(u, v), (v, u)])


def close_channel(u: str, v: str) -> None:
    """Closes a channel between nodes `u` and `v`.
    Balances are reset to 0.
    """
    if (u, v) in closed_channels:
        raise Exception("Cannot close a channel that has already been closed.")
    graph[u][v] = Decimal()
    graph[v][u] = Decimal()
    closed_channels.update([(u, v), (v, u)])


def transfer(u: str, v: str, amount: Decimal) -> None:
    """Transfers an amount `amount` from `u` to `v`."""
    graph[u][v] -= amount
    graph[v][u] += amount


def main() -> None:
    ...


if __name__ == "__main__":
    main()
