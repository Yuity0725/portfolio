"""価値制約付き最短経路（RCSP）の状態DP骨子（技術デモ用の匿名サンプル）。

技術デモ用に書き起こした匿名サンプルであり、実運用コードではない
(illustrative demo authored for this portfolio; not production source).

設計意図:
- 状態を (node, 累積価値) に取り、各状態の「最小到達時間」を DAG の
  トポロジカル順で更新する動的計画法。
- しきい値 Σv ≥ threshold を満たす終端状態のうち最小時間のものから、
  親ポインタを辿って経路を復元する。
- 辺重み weight は「移動時間 + 宛先ノードの処理時間」を畳み込んだ値とし、
  素の総和がそのまま総所要時間になるようにモデル化する。
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class DagView:
    """DP に必要な最小限のグラフビュー（デモ用に簡略化）。

    topo_order:  トポロジカル順のノード列
    value_of:    ノード → 付与価値（整数近似）
    successors:  ノード → [(隣接ノード, 辺重み=move+dst.t_proc), ...]
    """

    topo_order: list[str]
    value_of: dict[str, int]
    successors: dict[str, list[tuple[str, float]]]


# 状態 (node, 累積価値) が持つ最良時間と、経路復元用の親
@dataclass(frozen=True)
class _Cell:
    time: float
    prev_node: str | None
    prev_value: int | None


class RcspSolver:
    """resource-constrained shortest path を状態DPで解くソルバ。"""

    def __init__(self, graph: DagView) -> None:
        self._g = graph

    def solve(
        self, source: str, target: str, value_threshold: float
    ) -> tuple[list[str], float, float]:
        """Σv ≥ value_threshold を満たす最小総時間の経路を返す。

        Returns: (path, total_time, total_value)
        """
        # dp[node][accumulated_value] = _Cell(最小時間, 親ノード, 親の累積価値)
        dp: dict[str, dict[int, _Cell]] = {n: {} for n in self._g.topo_order}
        v0 = self._g.value_of[source]
        dp[source][v0] = _Cell(time=0.0, prev_node=None, prev_value=None)

        for u in self._g.topo_order:
            for v_acc, cell in list(dp[u].items()):
                for w, weight in self._g.successors.get(u, []):
                    new_time = cell.time + weight
                    new_value = v_acc + self._g.value_of[w]
                    current = dp[w].get(new_value)
                    if current is None or new_time < current.time:
                        dp[w][new_value] = _Cell(new_time, u, v_acc)

        threshold = math.ceil(value_threshold)
        best = self._best_terminal(dp[target], threshold)
        if best is None:
            raise ValueError(
                f"No path {source}→{target} satisfies Σv ≥ {value_threshold}"
            )

        total_value, total_time = best
        path = self._reconstruct(dp, target, total_value)
        return path, total_time, float(total_value)

    @staticmethod
    def _best_terminal(
        terminals: dict[int, _Cell], threshold: int
    ) -> tuple[int, float] | None:
        """しきい値を満たす終端状態のうち最小時間のものを (価値, 時間) で返す。"""
        feasible = [
            (v_acc, cell.time)
            for v_acc, cell in terminals.items()
            if v_acc >= threshold
        ]
        return min(feasible, key=lambda pair: pair[1]) if feasible else None

    @staticmethod
    def _reconstruct(
        dp: dict[str, dict[int, _Cell]], target: str, value: int
    ) -> list[str]:
        """親ポインタを終端から辿って経路を復元する。"""
        path: list[str] = [target]
        node, v = target, value
        while True:
            cell = dp[node][v]
            if cell.prev_node is None:
                break
            path.append(cell.prev_node)
            node, v = cell.prev_node, cell.prev_value  # type: ignore[assignment]
        path.reverse()
        return path
