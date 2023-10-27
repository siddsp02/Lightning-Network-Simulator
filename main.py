# !usr/bin/env python3

import random
import statistics
import time
from collections import Counter
from functools import partial
from itertools import batched, combinations, filterfalse, product
from operator import ne
from pprint import pprint
from typing import Iterable

from src.graph import DEFAULT_TRANSACTION_VALUE, Graph
from src.utils import TxData, TxStatus

NUMBER_OF_TRANSACTIONS = 100_000
CHANNELS_PER_NODE = 4


def remaining_nodes(graph: Graph, node: str) -> list[str]:
    return list(graph.keys() - graph[node].keys() - {node})


def max_channels_created(graph: Graph, node: str) -> bool:
    return len(graph[node]) == CHANNELS_PER_NODE


def unpopulated_nodes(graph: Graph, nodes: Iterable[str]) -> Iterable[str]:
    return filterfalse(partial(max_channels_created, graph), nodes)


# def generate_channels(graph: Graph) -> None:
#     processed = set()  # type: ignore
#     n = len(graph)
#     combs = math.comb(n, 2)
#     while not all(max_channels_created(graph, node) for node in graph):
#         i = random.randint(0, combs - 1)
#         u, v = nth_combination(graph, 2, i)
#         if u in processed:
#             continue
#         if max_channels_created(graph, u):
#             processed.add(u)
#         try:
#             graph.open_channel(u, v)
#         except Exception:
#             ...


# The following code is supposed to generate channels on a graph
# with at least N nodes per channel, but it is still a WIP.
# There needs to be a more efficient way to generate channels,
# which will be added later on.


def generate_channels(graph: Graph) -> None:
    nodes = unpopulated_nodes(graph, map(str, graph.nodes))
    for node in nodes:
        neighbours = unpopulated_nodes(graph, remaining_nodes(graph, node))
        for neighbour in neighbours:
            graph.open_channel(node, neighbour)
            if max_channels_created(graph, node):
                break


def generate_channels_hub_and_spoke(graph: Graph, n=1) -> None:
    peers = graph.nodes
    random.shuffle(peers)
    hubs, nodes = peers[:n], peers[n:]
    groups = batched(nodes, (len(nodes) + 1) // n)
    for hub, group in zip(hubs, groups, strict=True):
        for node in group:
            graph.open_channel(hub, node)
    # Make sure all lightning hubs are connected to each other.
    for u, v in combinations(hubs, 2):
        graph.open_channel(u, v)


def generate_txs(
    graph: Graph, n=NUMBER_OF_TRANSACTIONS, txval=DEFAULT_TRANSACTION_VALUE
) -> list[TxData]:
    txs = []  # type: ignore
    while len(txs) < n:
        sender, receiver = random.sample(graph.nodes, 2)
        if graph.get_balance(sender) < txval:
            continue
        txs.append(graph.send(sender, receiver, txval))
    return txs


def main() -> None:
    # Make a graph with m**n nodes
    graph = Graph(map("".join, product("abcd", repeat=3)))

    # Populate graph with channels
    print("Generating channels...")
    generate_channels(graph)
    print("Finished generating channels.")

    # Generate transactions on the network.
    print("Generating transactions...")
    t0 = time.perf_counter()
    txs = generate_txs(graph)
    t1 = time.perf_counter()
    print("Finished generating transactions.\n")

    # Calculate network statistics.
    counter = Counter(tx.status for tx in txs)
    successes = counter[TxStatus.SUCCESS]
    attempts = len(txs)
    failures = attempts - successes
    lst = [tx.hops for tx in txs if tx.status == TxStatus.SUCCESS]
    avg_hops = statistics.mean(lst)
    med_hops = statistics.median(lst)
    max_hops_tx = max(
        filter(partial(ne, TxStatus.UNREACHABLE), txs), key=lambda x: x.hops
    )

    # Print network statistics.
    pprint(counter)
    print()
    print(
        "=" * 80,
        f"Attempted Transactions: {attempts:_}",
        f"Successes: {successes}",
        f"Failures: {failures}",
        f"Success Rate: {successes/attempts:.2%}",
        f"Attempted Transactions Per Second: {attempts//(t1-t0)}",
        f"Average Hops Per Successful Transaction: {avg_hops:.1f}",
        f"Median Hops Per Successful Transaction: {med_hops:.1f}",
        "=" * 80,
        sep="\n",
    )
    print(f"Max Hops For Transaction: {max_hops_tx.hops}")
    print(max_hops_tx)
    if len(graph) <= 30:
        print("=" * 80)
        pprint(graph)
        print("=" * 80)


if __name__ == "__main__":
    # To be modified later. Having a seed allows reproducible results.
    random.seed(10)

    import cProfile
    import pstats

    # main()
    with cProfile.Profile() as pr:
        main()
        pr.print_stats(pstats.SortKey.TIME)
