from __future__ import annotations

import math
import random
from typing import Literal

import networkx as nx

from app.graph_model import GraphModel

Method = Literal["exact", "2opt", "sa", "auto"]


def _pairwise_distances(graph: GraphModel, nodes: list[str]) -> dict[tuple[str, str], float]:
    """All-pairs shortest path in the undirected closure of the graph.

    Inspection mode: ignore DAG direction and use t_move as the road cost
    (processing time at intermediate nodes is not part of the tour cost).
    """
    g = nx.Graph()
    g.add_nodes_from(n.id for n in graph.nodes)
    for e in graph.edges:
        if g.has_edge(e.src, e.dst):
            if e.t_move < g[e.src][e.dst]["weight"]:
                g[e.src][e.dst]["weight"] = e.t_move
        else:
            g.add_edge(e.src, e.dst, weight=e.t_move)

    dist: dict[tuple[str, str], float] = {}
    for u in nodes:
        lengths = nx.single_source_dijkstra_path_length(g, u, weight="weight")
        for v in nodes:
            if v == u:
                dist[(u, v)] = 0.0
            elif v in lengths:
                dist[(u, v)] = float(lengths[v])
            else:
                dist[(u, v)] = math.inf
    return dist


def _tour_cost(tour: list[str], dist: dict[tuple[str, str], float]) -> float:
    return sum(dist[(tour[i], tour[i + 1])] for i in range(len(tour) - 1))


def _bitmask_dp(nodes: list[str], start: str, dist) -> tuple[list[str], float]:
    others = [n for n in nodes if n != start]
    n = len(others)
    INF = math.inf
    dp = [[INF] * n for _ in range(1 << n)]
    parent = [[-1] * n for _ in range(1 << n)]
    for j in range(n):
        dp[1 << j][j] = dist[(start, others[j])]
    for mask in range(1 << n):
        for j in range(n):
            if not (mask >> j) & 1 or dp[mask][j] == INF:
                continue
            for k in range(n):
                if (mask >> k) & 1:
                    continue
                nmask = mask | (1 << k)
                cand = dp[mask][j] + dist[(others[j], others[k])]
                if cand < dp[nmask][k]:
                    dp[nmask][k] = cand
                    parent[nmask][k] = j
    full = (1 << n) - 1
    best_j, best_cost = min(
        ((j, dp[full][j] + dist[(others[j], start)]) for j in range(n)),
        key=lambda x: x[1],
    )
    # Reconstruct
    tour_idx: list[int] = []
    mask, j = full, best_j
    while j != -1:
        tour_idx.append(j)
        pj = parent[mask][j]
        mask ^= 1 << j
        j = pj
    tour_idx.reverse()
    return [start, *(others[i] for i in tour_idx), start], best_cost


def _nearest_neighbor(nodes: list[str], start: str, dist) -> list[str]:
    remaining = {n for n in nodes if n != start}
    tour = [start]
    cur = start
    while remaining:
        nxt = min(remaining, key=lambda n: dist[(cur, n)])
        tour.append(nxt)
        remaining.remove(nxt)
        cur = nxt
    tour.append(start)
    return tour


def _two_opt(tour: list[str], dist) -> list[str]:
    improved = True
    n = len(tour)
    while improved:
        improved = False
        for i in range(1, n - 2):
            for k in range(i + 1, n - 1):
                a, b, c, d = tour[i - 1], tour[i], tour[k], tour[k + 1]
                delta = (dist[(a, c)] + dist[(b, d)]) - (dist[(a, b)] + dist[(c, d)])
                if delta < -1e-9:
                    tour[i:k + 1] = reversed(tour[i:k + 1])
                    improved = True
    return tour


def _simulated_annealing(
    tour: list[str], dist, iters: int = 5000, seed: int = 42
) -> list[str]:
    rng = random.Random(seed)
    n = len(tour)
    cur = list(tour)
    cur_cost = _tour_cost(cur, dist)
    best, best_cost = list(cur), cur_cost
    T = max(cur_cost * 0.1, 1.0)
    cooling = 0.995
    for _ in range(iters):
        i, k = sorted(rng.sample(range(1, n - 1), 2))
        new = cur[:i] + cur[i:k + 1][::-1] + cur[k + 1:]
        new_cost = _tour_cost(new, dist)
        if new_cost < cur_cost or rng.random() < math.exp(-(new_cost - cur_cost) / max(T, 1e-9)):
            cur, cur_cost = new, new_cost
            if cur_cost < best_cost:
                best, best_cost = list(cur), cur_cost
        T *= cooling
    return best


def tour(
    graph: GraphModel,
    node_set: list[str],
    start_node: str,
    method: Method = "auto",
) -> tuple[list[str], float]:
    """Minimum-cost tour visiting all nodes in node_set (closed at start_node).

    Inspection mode: DAG direction is relaxed; tour cost uses t_move only.
    """
    if start_node not in node_set:
        node_set = [start_node, *node_set]
    dist = _pairwise_distances(graph, node_set)

    n = len(node_set)
    if method == "auto":
        method = "exact" if n <= 12 else "2opt" if n <= 100 else "sa"

    if method == "exact":
        t, c = _bitmask_dp(node_set, start_node, dist)
    elif method == "2opt":
        t = _two_opt(_nearest_neighbor(node_set, start_node, dist), dist)
        c = _tour_cost(t, dist)
    else:   # sa
        seed = _nearest_neighbor(node_set, start_node, dist)
        t = _simulated_annealing(_two_opt(seed, dist), dist)
        c = _tour_cost(t, dist)

    return t, float(c)
