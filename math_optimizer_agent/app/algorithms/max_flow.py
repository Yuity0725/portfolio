from __future__ import annotations

import networkx as nx

from app.graph_model import GraphModel


def _parse_split(name: str) -> tuple[str, str]:
    if name.endswith("_in"):
        return name[:-3], "in"
    if name.endswith("_out"):
        return name[:-4], "out"
    return name, ""


def max_flow(
    graph: GraphModel, source: str, target: str
) -> tuple[float, list[tuple[str, str]], list[str]]:
    """source→target の最大流量と、最小カットの (エッジ群, ノード群) を返す。

    内部はノード分割グラフ上で `minimum_cut` を実行。
    分割辺（v_in → v_out）が cut に含まれていればノード自体がボトルネック。
    """
    g = graph.to_node_split_networkx()
    s, t = f"{source}_in", f"{target}_out"

    flow_val, (reachable, unreachable) = nx.minimum_cut(g, s, t)

    cut_edges: list[tuple[str, str]] = []
    cut_nodes: list[str] = []
    for u in reachable:
        for v in g.successors(u):
            if v in unreachable:
                u_id, u_kind = _parse_split(u)
                v_id, v_kind = _parse_split(v)
                if u_id == v_id and u_kind == "in" and v_kind == "out":
                    cut_nodes.append(u_id)
                else:
                    cut_edges.append((u_id, v_id))

    return float(flow_val), cut_edges, cut_nodes
