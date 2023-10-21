# !usr/bin/env python3

from decimal import Decimal
from pprint import pprint

import graph

network = graph.create(graph.NODES)


def main() -> None:
    graph.open_channel(network, "a", "b")
    graph.transfer(network, "a", "b", Decimal("-0.5"))
    pprint(network)
    graph.close_channel(network, "a", "b")


if __name__ == "__main__":
    main()
