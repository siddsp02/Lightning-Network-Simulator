import heapq
from collections import deque
from math import inf
from typing import Callable, MutableMapping

type GraphLike[K, V] = MutableMapping[K, MutableMapping[K, V]]


def reconstruct_path[K](prev: dict[K, K], dest: K) -> deque[K]:
    """Reconstruct a path traversed from the destination node back
    to the original starting node.
    """
    path = deque[K]()
    pred: K | None = dest
    while pred is not None:
        path.appendleft(pred)
        pred = prev.get(pred)
    return path


def edge_weight[K, V](g: GraphLike[K, V], u: K, v: K) -> V:
    return g[u][v]


def dijkstra[K, V: float](
    graph: GraphLike[K, V],
    src: K,
    dst: K,
    /,
    *,
    weight_func: Callable[[GraphLike[K, V], K, K], V] = edge_weight,
) -> tuple[deque[K], V]:
    """Dijkstra's shortest path algorithm for finding the shortest
    path between any two given vertices or nodes on a graph.

    References:
        - https://github.com/siddsp02/Dijkstras-Algorithm/blob/main/dijkstra.py
        - https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm
    """
    queue = [(0, src)]
    dist = dict.fromkeys(graph, inf)
    prev = {}
    dist[src] = 0
    while queue:
        priority, u = heapq.heappop(queue)
        if priority > dist[u]:
            continue
        if u == dst:
            break
        for v in graph[u]:
            alt = dist[u] + weight_func(graph, u, v)
            if alt < dist[v]:
                dist[v] = alt
                prev[v] = u
                heapq.heappush(queue, (alt, v))  # type: ignore
    path = reconstruct_path(prev, dst)
    return path, dist[dst]  # type: ignore


def bfs[K, V](graph: GraphLike[K, V], src: K, dst: K) -> tuple[deque[K], int]:
    """Breadth-first search algorithm. Finds the shortest path
    in an unweighted graph.
    """
    queue = deque([src])
    visited = {src}
    prev = {}
    while queue:
        u = queue.pop()
        if u == dst:
            break
        for v in graph[u]:
            if v not in visited:
                visited.add(v)
                queue.appendleft(v)
                prev[v] = u
    path = reconstruct_path(prev, dst)
    return path, len(path) - 1
