from __future__ import annotations

import math

import networkx as nx

from app.graph_model import GraphModel


def orienteering_dp(
    graph: GraphModel,
    source: str,
    target: str,
    time_budget: float,
    time_bucket: float = 1.0,
) -> tuple[list[str], float, float]:
    """Maximum collectable value on a DAG s.t. total_time ≤ time_budget.

    Returns (path, total_value, total_time).
    Time is discretized in `time_bucket` units to keep the DP table finite.
    """
    g = graph.to_networkx()
    if not nx.is_directed_acyclic_graph(g):
        raise ValueError("orienteering_dp requires a DAG")

    order = list(nx.topological_sort(g))
    budget_b = int(math.floor(time_budget / time_bucket))

    # dp[node][t_bucket] = (max_value, prev_node, prev_t_bucket)
    dp: dict[str, dict[int, tuple[float, str | None, int | None]]] = {n: {} for n in order}
    dp[source][0] = (float(g.nodes[source]["v"]), None, None)

    for u in order:
        if not dp[u]:
            continue
        for t_b, (v_acc, _, _) in list(dp[u].items()):
            for w in g.successors(u):
                new_t_b = t_b + int(math.ceil(g[u][w]["weight"] / time_bucket))
                if new_t_b > budget_b:
                    continue
                new_v = v_acc + float(g.nodes[w]["v"])
                cur = dp[w].get(new_t_b)
                if cur is None or new_v > cur[0]:
                    dp[w][new_t_b] = (new_v, u, t_b)

    if not dp[target]:
        raise ValueError(f"No path from {source} to {target} within time_budget={time_budget}")

    # Pick best feasible terminal state at target (max value, tie-break smallest time)
    best_t_b, (best_v, _, _) = max(dp[target].items(), key=lambda kv: (kv[1][0], -kv[0]))

    # Reconstruct path
    path: list[str] = [target]
    node, t_b = target, best_t_b
    while True:
        _, prev_node, prev_t_b = dp[node][t_b]
        if prev_node is None:
            break
        path.append(prev_node)
        node, t_b = prev_node, prev_t_b   # type: ignore[assignment]
    path.reverse()
    return path, float(best_v), float(best_t_b * time_bucket)
