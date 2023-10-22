# !usr/bin/env python3

import random
import string
import time

from graph import DEFAULT_TRANSACTION_VALUE, Graph

NUMBER_OF_TRANSACTIONS = 20_000


def remaining_nodes(graph: Graph, node: str) -> list[str]:
    return list(graph.keys() - graph[node].keys() - {node})


def main() -> None:
    graph = Graph(string.ascii_lowercase)

    for node in graph.nodes:
        lst = remaining_nodes(graph, node)
        neighbours = random.sample(lst, min(len(lst), 3))
        for neighbour in neighbours:
            graph.open_channel(node, neighbour)

    # Keep track of the number of successful transactions,
    # failed transactions, and the number of transactions
    # attempted.
    i, successes, failures = 0, 0, 0
    t0 = time.perf_counter()
    while i < NUMBER_OF_TRANSACTIONS:
        # Randomly select two nodes from the network to transact.
        sender, receiver = random.sample(graph.nodes, 2)
        # If the node itself does not have the proper funds to send
        # a transaction, we skip this loop iteration since this is
        # not a failure on the network to route a payment.
        if graph.get_balance(sender) < DEFAULT_TRANSACTION_VALUE:
            continue
        try:
            graph.send(sender, receiver)  # type: ignore
        except Exception:
            failures += 1
        else:
            successes += 1
        i += 1
    t1 = time.perf_counter()
    print(f"Attempted Transactions: {i}")
    print(f"Successes: {successes:^-50}")
    print(f"Failures: {failures}")
    print(f"Success Rate: {successes/i:.2%}")
    print(f"Attempted Transactions Per Second: {i/(t1-t0):.4f}")


if __name__ == "__main__":
    main()
