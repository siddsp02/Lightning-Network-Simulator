# !usr/bin/env python3

from decimal import Decimal

from graph import Graph

graph = Graph("abcdefgh")


def main() -> None:
    graph.open_channel("a", "b")
    graph.transfer("a", "b", Decimal("0.5"))
    print(graph)
    print(graph.get_balance("a"))


if __name__ == "__main__":
    main()
