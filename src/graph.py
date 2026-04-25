from __future__ import annotations

from itertools import pairwise, starmap
from math import inf
import textwrap
from pprint import pformat
from typing import Iterable, Self, Sequence

import networkx as nx

from src.utils import add_key_incr, is_valid_amount, valid_amounts

DEFAULT_CHANNEL_BALANCE = 10


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

    def add_edge(self, u, v, **attr) -> None:
        super().add_edge(u, v, channels={}, **attr)
        super().add_edge(v, u, channels={}, **attr)

    def _make_edges_symmetrical(self) -> None:
        for u, v in self.edges:
            self.add_edge(u, v)

    @classmethod
    def generate_random(cls, n: int, p: float, seed: int | None = None) -> Self:
        return nx.erdos_renyi_graph(n, p, seed=seed, directed=True, create_using=cls)

    def open_bichannels(
        self, channels: Iterable[tuple[tuple[K, int], tuple[K, int]]]
    ) -> None:
        for (u, u_balance), (v, v_balance) in channels:
            if not valid_amounts([u_balance, v_balance]):
                raise ValueError
            if (u, v) not in self.edges:
                self.add_edge(u, v)
            add_key_incr(self[u][v]["channels"], u_balance)
            add_key_incr(self[v][u]["channels"], v_balance)

    def open_channels(self, channels: Iterable[tuple[K, K, int]]) -> None:
        for u, v, amount in channels:
            if not is_valid_amount(amount):
                raise ValueError
            if (u, v) not in self.edges:
                self.add_edge(u, v)
            add_key_incr(self[u][v]["channels"], amount)
            add_key_incr(self[v][u]["channels"], 0)

    def close_channel(self, channel: tuple[K, K], id_: int) -> None:
        u, v = channel
        del self[u][v]["channels"][id_]
        del self[v][u]["channels"][id_]

    def edge_cost(self, edge: tuple[K, K]) -> float:
        u, v = edge
        return 1 if (u, v) in self.edges else inf

    def transfer(self, edge: tuple[K, K]) -> None:
        raise NotImplementedError

    def send(self, src: K, dest: K, amount: int) -> None:
        raise NotImplementedError

    def max_sendable(self, src: K, dest: K) -> float:
        raise NotImplementedError

    def _path_cost(self, path: Sequence[K]) -> float:
        return sum(starmap(self.edge_cost, pairwise(path)))

    def reset(self) -> None:
        self.remove_edges_from(list(self.edges))


def main() -> None:
    g = Graph()
    g.open_channels([(1, 0, 32), (1, 3, 25), (3, 1, 12)])
    print(g)


if __name__ == "__main__":
    main()
