from __future__ import annotations

from app.algorithms.max_flow import max_flow
from app.graph_model import GraphModel


def bottleneck(
    graph: GraphModel, source: str, target: str, top_k: int = 3
) -> list[dict]:
    """最小カットから増強優先のボトルネック要素を上位 top_k 件返す。

    各要素: {"kind": "node"|"edge", "id": str, "cap": float}
    cap が小さいほど増強優先度が高い（並びは cap 昇順）。
    """
    _, cut_edges, cut_nodes = max_flow(graph, source, target)

    items: list[dict] = []
    by_id = {n.id: n for n in graph.nodes}
    edge_lookup = {(e.src, e.dst): e for e in graph.edges}

    for nid in cut_nodes:
        n = by_id.get(nid)
        if n is None:
            continue
        items.append({
            "kind": "node",
            "id": nid,
            "cap": float(n.cap) if n.cap is not None else float("inf"),
        })
    for src, dst in cut_edges:
        e = edge_lookup.get((src, dst))
        if e is None:
            continue
        items.append({
            "kind": "edge",
            "id": f"{src}->{dst}",
            "cap": float(e.cap) if e.cap is not None else float("inf"),
        })

    items.sort(key=lambda x: x["cap"])
    return items[:top_k]
