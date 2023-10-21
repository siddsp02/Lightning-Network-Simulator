# !usr/bin/env python3

from decimal import Decimal

NODES = "abcdefgh"

graph = {node: dict.fromkeys({*NODES} - {node}, Decimal()) for node in NODES}


def open_channel(u: str, v: str, x: Decimal, y: Decimal) -> None:
    """Opens a channel between nodes `u` and `v`
    where `u -> v = x` and `v -> u = y`.
    """
    graph[u][v] = x
    graph[v][u] = y


def close_channel(u: str, v: str) -> None:
    """Closes a channel between nodes `u` and `v`.
    Balances are reset to 0.
    """
    graph[u][v] = Decimal()
    graph[v][u] = Decimal()


def transfer(u: str, v: str, amount: Decimal) -> None:
    """Transfers an amount `amount` from `u` to `v`."""
    graph[u][v] -= amount
    graph[v][u] += amount


def main() -> None:
    ...


if __name__ == "__main__":
    main()
