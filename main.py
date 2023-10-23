# !usr/bin/env python3

import random
import string
import time
from operator import countOf
from pprint import pprint
from statistics import mean

from graph import DEFAULT_TRANSACTION_VALUE, Graph
from utils import TxData, TxStatus

NUMBER_OF_TRANSACTIONS = 100_000
CHANNELS_PER_NODE = 4


def remaining_nodes(graph: Graph, node: str) -> list[str]:
    return list(graph.keys() - graph[node].keys() - {node})


def main() -> None:
    graph = Graph(string.ascii_lowercase)

    for node in graph.nodes:
        if len(graph[node]) == CHANNELS_PER_NODE:
            continue
        for neighbour in remaining_nodes(graph, node):
            if len(graph[neighbour]) == CHANNELS_PER_NODE:
                continue
            graph.open_channel(node, neighbour)
            if len(graph[node]) == CHANNELS_PER_NODE:
                break

    # Keep track of the number of successful transactions,
    # failed transactions, and the number of transactions
    # attempted.
    i = 0
    # print(graph)
    t0 = time.perf_counter()
    txs: list[TxData] = []
    while i < NUMBER_OF_TRANSACTIONS:
        # Randomly select two nodes from the network to transact.
        sender, receiver = random.sample(graph.nodes, 2)

        # If the node itself does not have the proper funds to send
        # a transaction, we skip this loop iteration since this is
        # not a failure on the network to route a payment.
        if graph.get_balance(sender) < DEFAULT_TRANSACTION_VALUE:
            continue

        txs.append(graph.send(sender, receiver))
        i += 1
    t1 = time.perf_counter()
    successes = countOf((tx.status for tx in txs), TxStatus.SUCCESS)
    failures = i - successes
    avg_hops = mean(tx.hops for tx in txs if tx.status == TxStatus.SUCCESS)
    print(
        "=" * 80,
        f"Attempted Transactions: {i:_}",
        f"Successes: {successes}",
        f"Failures: {failures}",
        f"Success Rate: {successes/i:.2%}",
        f"Attempted Transactions Per Second: {i/(t1-t0):.4f}",
        f"Hops Per Successful Transaction: {avg_hops}",
        "=" * 80,
        sep="\n",
    )
    max_hops_tx = max(
        (tx for tx in txs if tx.status != TxStatus.UNREACHABLE),
        key=lambda x: x.hops,
    )
    print(f"\nMax Hops {max_hops_tx.hops}\n")
    print(max_hops_tx)
    print("=" * 80)
    pprint(graph)
    print("=" * 80)


if __name__ == "__main__":
    main()
