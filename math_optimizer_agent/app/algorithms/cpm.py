from __future__ import annotations

import networkx as nx

from app.graph_model import GraphModel


def critical_path(graph: GraphModel, source: str, target: str) -> tuple[list[str], float]:
    """Longest source→target path in the DAG.

    Interpreted as the completion-time lower bound when every step is on the critical path.
    """
    g = graph.to_networkx()
    if not nx.is_directed_acyclic_graph(g):
        raise ValueError("critical_path requires a DAG")

    # Restrict to nodes reachable from source AND able to reach target.
    desc = nx.descendants(g, source) | {source}
    anc = nx.ancestors(g, target) | {target}
    sub = g.subgraph(desc & anc).copy()

    path = nx.dag_longest_path(sub, weight="weight")
    if not path or path[0] != source or path[-1] != target:
        raise ValueError(f"No path from {source} to {target}")
    total = sum(sub[u][v]["weight"] for u, v in zip(path, path[1:]))
    return path, float(total)
