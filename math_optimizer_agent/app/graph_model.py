from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import networkx as nx


@dataclass(frozen=True)
class Node:
    """製造工程の工場ノード。

    属性:
      t_proc: 1 個あたりの処理時間 (分/個)
      v: 1 個あたりに付与される価値
      lanes: 並列ライン数（1 個ずつ流れる）。倉庫など処理しないノードは t_proc=0。

    派生:
      cap: 時間あたり処理可能量 (個/h) = lanes × 60 / t_proc。
           t_proc <= 0 または lanes <= 0 のときは None（無制限扱い、倉庫向け）。
    """
    id: str
    t_proc: float
    v: float
    lanes: int = 1

    @property
    def cap(self) -> float | None:
        if self.t_proc <= 0 or self.lanes <= 0:
            return None
        return float(self.lanes) * 60.0 / float(self.t_proc)


@dataclass(frozen=True)
class Edge:
    src: str
    dst: str
    t_move: float
    cap: float | None = None   # 時間あたり搬送可能量。None は無制限


@dataclass
class GraphModel:
    nodes: list[Node]
    edges: list[Edge]
    source_path: str = ""
    _by_id: dict[str, Node] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._by_id = {n.id: n for n in self.nodes}

    def node(self, node_id: str) -> Node:
        return self._by_id[node_id]

    def to_networkx(self) -> nx.DiGraph:
        """Build a NetworkX DiGraph. Edge weight = t_move + dst's t_proc.

        Source's t_proc is folded into outgoing edges' weight via the destination
        node, so plain Dijkstra/longest-path gives correct totals (origin has 0).
        """
        g = nx.DiGraph()
        for n in self.nodes:
            g.add_node(n.id, t_proc=n.t_proc, v=n.v, cap=n.cap)
        for e in self.edges:
            dst = self._by_id[e.dst]
            g.add_edge(
                e.src, e.dst,
                t_move=e.t_move,
                cap=e.cap,
                weight=e.t_move + dst.t_proc,
            )
        return g

    def to_node_split_networkx(self, default_cap: float = float("inf")) -> nx.DiGraph:
        """Node-split DiGraph for max-flow / min-cost-flow.

        Each node `v` splits into `v_in` and `v_out` joined by an edge whose
        capacity is `v.cap` (or `default_cap` if None) and weight is `t_proc`.
        Each original edge `(u, v)` becomes `(u_out, v_in)` with capacity
        `e.cap` (or `default_cap`) and weight `t_move`.

        Capacity/weight are coerced to int because network_simplex requires
        integer values.
        """
        g = nx.DiGraph()
        for n in self.nodes:
            cap = int(round(n.cap)) if n.cap is not None else _safe_int(default_cap)
            g.add_edge(
                f"{n.id}_in", f"{n.id}_out",
                capacity=cap, weight=int(round(n.t_proc)),
            )
        for e in self.edges:
            cap = int(round(e.cap)) if e.cap is not None else _safe_int(default_cap)
            g.add_edge(
                f"{e.src}_out", f"{e.dst}_in",
                capacity=cap, weight=int(round(e.t_move)),
            )
        return g

    def mutate(
        self,
        blocked_nodes: list[str] | None = None,
        blocked_edges: list[tuple[str, str]] | None = None,
        extra_edges: list[tuple[str, str, float]] | None = None,
        min_throughput: float | None = None,
    ) -> GraphModel:
        """Return a derived graph with the given perturbations applied.

        min_throughput: ノード/エッジのうち `cap < min_throughput` を満たすものを
        自動的に blocked 化する（cap=None=無制限 は常に通過）。
        """
        bn = set(blocked_nodes or [])
        be = set(blocked_edges or [])
        if min_throughput is not None:
            for n in self.nodes:
                if n.cap is not None and n.cap < min_throughput:
                    bn.add(n.id)
            for e in self.edges:
                if e.cap is not None and e.cap < min_throughput:
                    be.add((e.src, e.dst))
        nodes = [n for n in self.nodes if n.id not in bn]
        edges = [
            e for e in self.edges
            if e.src not in bn and e.dst not in bn and (e.src, e.dst) not in be
        ]
        for src, dst, t in extra_edges or []:
            edges.append(Edge(src=src, dst=dst, t_move=float(t)))
        return GraphModel(nodes=nodes, edges=edges, source_path=self.source_path)


def _safe_int(x: float) -> int:
    """inf を NetworkX 互換の大きな整数に変換。"""
    if x == float("inf"):
        return 10**9
    return int(round(x))


def load_graph(path: str | Path) -> GraphModel:
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    nodes = [Node(**n) for n in data["nodes"]]
    edges = [Edge(**e) for e in data["edges"]]
    return GraphModel(nodes=nodes, edges=edges, source_path=str(p))
