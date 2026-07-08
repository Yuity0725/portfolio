"""不変な GraphModel と mutate() / 派生 cap（技術デモ用の匿名サンプル）。

技術デモ用に書き起こした匿名サンプルであり、実運用コードではない
(illustrative demo authored for this portfolio; not production source).

設計意図:
- 工場ノードは (t_proc, v, lanes) を持ち、時間あたり処理能力 cap は
  `lanes × 60 / t_proc` の派生値として1箇所（プロパティ）で計算する。
- グラフは不変な値オブジェクト。制約適用は mutate() が「新しいグラフ」を返し、
  元グラフは決して破壊しない（マルチターンで基準グラフを無傷に保つため）。
- min_throughput は派生 cap を使った横断フックで、cap 不足の要素を自動除外する。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Node:
    """製造工程の工場ノード（不変）。

    t_proc: 1 個あたりの処理時間 (分/個)
    v:      1 個あたりに付与される価値
    lanes:  並列ライン数。倉庫など処理しないノードは t_proc=0 / lanes=0。
    """

    id: str
    t_proc: float
    v: float
    lanes: int = 1

    @property
    def cap(self) -> float | None:
        """時間あたり処理可能量 (個/h)。無制限（倉庫など）は None。"""
        if self.t_proc <= 0 or self.lanes <= 0:
            return None
        return float(self.lanes) * 60.0 / float(self.t_proc)


@dataclass(frozen=True)
class Edge:
    """配送路エッジ（不変）。cap=None は搬送量無制限。"""

    src: str
    dst: str
    t_move: float
    cap: float | None = None


@dataclass
class GraphModel:
    """DAG の値オブジェクト。摂動は必ず派生グラフとして返す。"""

    nodes: list[Node]
    edges: list[Edge]
    _by_id: dict[str, Node] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._by_id = {n.id: n for n in self.nodes}

    def node(self, node_id: str) -> Node:
        return self._by_id[node_id]

    def mutate(
        self,
        blocked_nodes: list[str] | None = None,
        blocked_edges: list[tuple[str, str]] | None = None,
        extra_edges: list[tuple[str, str, float]] | None = None,
        min_throughput: float | None = None,
    ) -> GraphModel:
        """摂動を適用した新しい GraphModel を返す（元グラフは不変）。

        min_throughput: cap < min_throughput のノード/エッジを自動で blocked 化。
        cap=None（無制限）は常に通過する。
        """
        blocked_n = set(blocked_nodes or [])
        blocked_e = set(blocked_edges or [])

        # 横断フック: 派生 cap がしきい値未満なら遮断対象に加える
        if min_throughput is not None:
            blocked_n |= {
                n.id for n in self.nodes
                if n.cap is not None and n.cap < min_throughput
            }
            blocked_e |= {
                (e.src, e.dst) for e in self.edges
                if e.cap is not None and e.cap < min_throughput
            }

        nodes = [n for n in self.nodes if n.id not in blocked_n]
        edges = [
            e for e in self.edges
            if e.src not in blocked_n
            and e.dst not in blocked_n
            and (e.src, e.dst) not in blocked_e
        ]
        edges += [Edge(src=s, dst=d, t_move=float(t)) for s, d, t in (extra_edges or [])]
        return GraphModel(nodes=nodes, edges=edges)
