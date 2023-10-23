# !usr/bin/env python3

import random
import statistics
import string
import time
from functools import partial
from itertools import filterfalse
from operator import countOf
from pprint import pprint
from typing import Iterable

from graph import DEFAULT_TRANSACTION_VALUE, Graph
from utils import TxData, TxStatus

NUMBER_OF_TRANSACTIONS = 100_000
CHANNELS_PER_NODE = 4


def remaining_nodes(graph: Graph, node: str) -> list[str]:
    return list(graph.keys() - graph[node].keys() - {node})


def max_channels_created(graph: Graph, node: str) -> bool:
    return len(graph[node]) == CHANNELS_PER_NODE


def unpopulated_nodes(graph: Graph, nodes: Iterable[str]) -> Iterable[str]:
    return filterfalse(partial(max_channels_created, graph), nodes)


def generate_channels(graph: Graph) -> None:
    nodes = unpopulated_nodes(graph, map(str, graph.nodes))
    for node in nodes:
        neighbours = unpopulated_nodes(graph, remaining_nodes(graph, node))
        for neighbour in neighbours:
            graph.open_channel(node, neighbour)
            if max_channels_created(graph, node):
                break


def main() -> None:
    graph = Graph(string.ascii_lowercase)
    # Populate graph with channels.
    generate_channels(graph)
    # Track our attempted transactions.
    attempts = 0
    txs: list[TxData] = []
    t0 = time.perf_counter()
    while attempts < NUMBER_OF_TRANSACTIONS:
        # Randomly select two nodes from the network.
        sender, receiver = map(graph.get_node, random.sample(graph.nodes, 2))
        if sender.balance < DEFAULT_TRANSACTION_VALUE:
            continue
        txs.append(sender.send(receiver))
        attempts += 1
    t1 = time.perf_counter()
    successes = countOf((tx.status for tx in txs), TxStatus.SUCCESS)
    failures = attempts - successes
    avg_hops = statistics.mean(tx.hops for tx in txs if tx.status == TxStatus.SUCCESS)
    print(
        "=" * 80,
        f"Attempted Transactions: {attempts:_}",
        f"Successes: {successes}",
        f"Failures: {failures}",
        f"Success Rate: {successes/attempts:.2%}",
        f"Attempted Transactions Per Second: {attempts/(t1-t0):.4f}",
        f"Average Hops Per Successful Transaction: {avg_hops:.1f}",
        "=" * 80,
        sep="\n",
    )
    max_hops_tx = max(
        (tx for tx in txs if tx.status != TxStatus.UNREACHABLE),
        key=lambda x: x.hops,
    )
    print(f"Max Hops For Transaction: {max_hops_tx.hops}")
    print(max_hops_tx)
    print("=" * 80)
    pprint(graph)
    print("=" * 80)


if __name__ == "__main__":
    main()
