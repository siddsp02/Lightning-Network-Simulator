import textwrap
from itertools import pairwise, starmap
from math import inf
from operator import itemgetter
from pprint import pformat
from typing import Any, Callable, Iterable, Self, Sequence

import networkx as nx

from utils import add_key_incr, is_valid_amount, valid_amounts


def max_balance[T](dct: dict[T, int]) -> T:
    id_, _ = max(dct.items(), key=itemgetter(1))
    return id_


class Graph[K](nx.DiGraph):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._make_edges_symmetrical()

    def __repr__(self) -> str:
        data = nx.to_dict_of_dicts(self)
        fmt = textwrap.indent(pformat(data), " " * 4)
        clsname = type(self).__name__
        return f"{clsname}(\n{fmt},\n)"

    __str__ = __repr__
    shortest_path = nx.shortest_path

    def add_edge(self, u, v, **attr) -> None:
        "Adds an edge to the graph, ensuring edges are mirrored properly."
        super().add_edge(u, v, channels={}, **attr)
        super().add_edge(v, u, channels={}, **attr)

    def _make_edges_symmetrical(self) -> None:
        for u, v in list(self.edges):
            self.add_edge(u, v)

    @classmethod
    def generate_random(cls, n: int, p: float, seed: int | None = None) -> Self:
        return nx.erdos_renyi_graph(n, p, seed, directed=True, create_using=cls)

    def open_bichannels(
        self, channels: Iterable[tuple[tuple[K, int], tuple[K, int]]]
    ) -> None:
        """Opens multiple channels initialized with balances on both sides.
        Calling two edges that connect the same nodes doesn't update the same
        channel, but opens a new one instead."""
        for (u, u_balance), (v, v_balance) in channels:
            if not valid_amounts([u_balance, v_balance]):
                raise ValueError
            if (u, v) not in self.edges:
                self.add_edge(u, v)
            add_key_incr(self[u][v]["channels"], u_balance)
            add_key_incr(self[v][u]["channels"], v_balance)

    def open_channels(self, channels: Iterable[tuple[K, K, int]]) -> None:
        """Opens multiple channels with balances only on one side. Note that calling
        two edges that have the same connecting nodes doesn't update the same channel,
        but opens a new one instead. If a channel (u, v, amount) is opened, and then
        another channel (v, u, amount) is opened, 2 channels will be created."""
        self.open_bichannels(
            channels=[((u, amount), (v, 0)) for u, v, amount in channels]
        )

    def close_channel(self, channel: tuple[K, K], id_: int) -> None:
        "Closes a channel and removes it from the graph. `id_` is the channel id."
        u, v = channel
        del self[u][v]["channels"][id_]
        del self[v][u]["channels"][id_]

    def edge_cost(self, edge: tuple[K, K]) -> float:
        u, v = edge
        return 1 if (u, v) in self.edges else inf

    def transfer(
        self,
        edge: tuple[K, K],
        amount: int,
        picker: Callable[[dict[int, Any]], int] = max_balance,
    ) -> None:
        "Transfer an amount across an edge (u, v)."
        # TODO: Add checks for the amount being sent to ensure that
        # a node cannot send more than its allowed "balance".
        if edge not in self.edges:
            raise LookupError
        u, v = edge
        u_channels = self[u][v]["channels"]
        v_channels = self[v][u]["channels"]
        channel_id = picker(u_channels)
        if not is_valid_amount(amount):
            raise ValueError
        balance = u_channels[channel_id]
        if balance < amount:
            raise ValueError
        u_channels[channel_id] -= amount
        v_channels[channel_id] += amount

    def send(self, source: K, target: K, amount: int) -> None:
        path = self.shortest_path(source, target)
        for edge in pairwise(path):
            try:
                self.transfer(edge, amount)
            except ValueError:
                raise  # TODO: Handle failure and rolling back of transaction.

    def max_sendable(self, source: K, target: K) -> float:
        path = self.shortest_path(source, target)
        max_amount = min(max_balance(self[u][v]["channels"]) for u, v in pairwise(path))
        return max_amount

    def _path_cost(self, path: Iterable[K]) -> float:
        return sum(starmap(self.edge_cost, pairwise(path)))

    def reset(self) -> None:
        self.remove_edges_from(list(self.edges))


def main() -> None:
    g = Graph()
    g.open_channels([(1, 0, 32), (1, 3, 25), (3, 1, 12)])
    print(g)
    g.send(1, 0, amount=20)
    print(g)


if __name__ == "__main__":
    main()
