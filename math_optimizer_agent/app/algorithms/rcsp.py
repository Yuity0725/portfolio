from __future__ import annotations

import math

import networkx as nx

from app.graph_model import GraphModel


def rcsp_dp(
    graph: GraphModel,
    source: str,
    target: str,
    value_threshold: float,
) -> tuple[list[str], float, float]:
    """Resource-constrained shortest path on a DAG.

    Returns (path, total_time, total_value) minimizing total_time subject to
    Σ v ≥ value_threshold along the path. Values are assumed to be non-negative
    integers (or near-integers). Uses DP over states (node, accumulated_value).
    """
    g = graph.to_networkx()
    if not nx.is_directed_acyclic_graph(g):
        raise ValueError("rcsp_dp requires a DAG")

    order = list(nx.topological_sort(g))
    if source not in order or target not in order:
        raise ValueError("source/target not in graph")

    # dp[node][v_total] = (min_time, prev_node, prev_v_total)
    dp: dict[str, dict[int, tuple[float, str | None, int | None]]] = {n: {} for n in order}
    v0 = int(round(g.nodes[source]["v"]))
    dp[source][v0] = (0.0, None, None)

    for u in order:
        if u not in dp or not dp[u]:
            continue
        for v_acc, (t_acc, _, _) in list(dp[u].items()):
            for w in g.successors(u):
                new_t = t_acc + g[u][w]["weight"]   # already includes w's t_proc
                new_v = v_acc + int(round(g.nodes[w]["v"]))
                cur = dp[w].get(new_v)
                if cur is None or new_t < cur[0]:
                    dp[w][new_v] = (new_t, u, v_acc)

    # Pick the best terminal state at target meeting threshold
    best: tuple[float, int] | None = None
    threshold = int(math.ceil(value_threshold))
    for v_acc, (t_acc, _, _) in dp[target].items():
        if v_acc >= threshold:
            if best is None or t_acc < best[0]:
                best = (t_acc, v_acc)
    if best is None:
        raise ValueError(f"No path from {source} to {target} satisfies Σv ≥ {value_threshold}")

    # Reconstruct path
    total_time, v_acc = best
    path: list[str] = [target]
    node, v = target, v_acc
    while True:
        _, prev_node, prev_v = dp[node][v]
        if prev_node is None:
            break
        path.append(prev_node)
        node, v = prev_node, prev_v   # type: ignore[assignment]
    path.reverse()
    return path, float(total_time), float(v_acc)
