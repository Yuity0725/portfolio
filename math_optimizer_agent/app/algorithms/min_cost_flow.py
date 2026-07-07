from __future__ import annotations

import networkx as nx

from app.graph_model import GraphModel

_SRC = "__src__"
_SNK = "__snk__"


def decompose_flow(
    edge_flows: list[tuple[str, str, float]], source: str, target: str
) -> list[tuple[list[str], float]]:
    """edge_flows を source→target のパスごとに分解する。

    Returns: list of (path, flow). path はノード列。
    """
    flow_left: dict[tuple[str, str], float] = {
        (s, d): float(f) for s, d, f in edge_flows if f > 0
    }
    decomp: list[tuple[list[str], float]] = []

    while True:
        path = _find_path(source, target, flow_left)
        if path is None:
            break
        bottleneck = min(flow_left[(path[i], path[i + 1])] for i in range(len(path) - 1))
        for i in range(len(path) - 1):
            key = (path[i], path[i + 1])
            flow_left[key] -= bottleneck
            if flow_left[key] < 1e-9:
                del flow_left[key]
        decomp.append((path, bottleneck))

    return decomp


def _find_path(
    source: str, target: str, flow_left: dict[tuple[str, str], float]
) -> list[str] | None:
    succ: dict[str, list[str]] = {}
    for (s, d), f in flow_left.items():
        if f > 0:
            succ.setdefault(s, []).append(d)

    stack: list[tuple[str, list[str], set[str]]] = [(source, [source], {source})]
    while stack:
        node, path, visited = stack.pop()
        if node == target:
            return path
        for d in succ.get(node, []):
            if d not in visited:
                stack.append((d, path + [d], visited | {d}))
    return None


def min_cost_flow(
    graph: GraphModel, source: str, target: str, demand: float
) -> tuple[float, float, list[tuple[str, str, float]]]:
    """目標流量 demand を最小総コストで流す。

    Returns (achieved_flow, total_cost, edge_flows)。
    - 容量制約上 demand に届かない場合は achieved_flow を最大流量に切り詰める。
    - edge_flows は元グラフ上のエッジ (src, dst, flow) リスト（flow > 0 のみ）。
    """
    g = graph.to_node_split_networkx()
    s, t = f"{source}_in", f"{target}_out"

    max_flow_val, _ = nx.maximum_flow(g, s, t)
    achieved = int(min(float(demand), float(max_flow_val)))
    if achieved <= 0:
        return 0.0, 0.0, []

    h = g.copy()
    h.add_node(_SRC, demand=-achieved)
    h.add_node(_SNK, demand=achieved)
    h.add_edge(_SRC, s, capacity=achieved, weight=0)
    h.add_edge(t, _SNK, capacity=achieved, weight=0)

    flow_cost, flow_dict = nx.network_simplex(h)

    edge_flows: list[tuple[str, str, float]] = []
    for e in graph.edges:
        f = flow_dict.get(f"{e.src}_out", {}).get(f"{e.dst}_in", 0)
        if f > 0:
            edge_flows.append((e.src, e.dst, float(f)))

    return float(achieved), float(flow_cost), edge_flows
