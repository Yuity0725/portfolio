from __future__ import annotations

import networkx as nx

from app.graph_model import GraphModel


def dijkstra_path(graph: GraphModel, source: str, target: str) -> tuple[list[str], float]:
    """Minimum total time (move + processing) from source to target."""
    g = graph.to_networkx()
    path = nx.dijkstra_path(g, source, target, weight="weight")
    total = nx.dijkstra_path_length(g, source, target, weight="weight")
    return path, float(total)
