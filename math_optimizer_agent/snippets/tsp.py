"""規模で解法を切り替える巡回ソルバ（技術デモ用の匿名サンプル）。

技術デモ用に書き起こした匿名サンプルであり、実運用コードではない
(illustrative demo authored for this portfolio; not production source).

設計意図:
- 巡回（TSP）は入力サイズで厳密性と速度が両立しない。そこでノード数に応じて
  ビットマスクDP（厳密）／最近傍＋2-opt／焼きなまし法へ自動フォールバックする。
- 焼きなましは乱数シードを固定し、同じ入力なら同じ解が出る（再現性を確保）。
- ここでは骨子のみ。距離行列は事前計算済みとして受け取る。
"""

from __future__ import annotations

import math
import random
from typing import Literal

Method = Literal["exact", "2opt", "sa", "auto"]
DistMatrix = dict[tuple[str, str], float]


class TourSolver:
    """指定ノードを 1 回ずつ巡回する最小コスト閉路を求めるソルバ。"""

    _EXACT_MAX = 12    # これ以下はビットマスクDPで厳密解
    _HEURISTIC_MAX = 100  # これ以下は 2-opt、超えたら焼きなまし

    def __init__(self, dist: DistMatrix, seed: int = 42) -> None:
        self._dist = dist
        self._rng = random.Random(seed)

    def solve(
        self, nodes: list[str], start: str, method: Method = "auto"
    ) -> tuple[list[str], float]:
        """巡回路と総コストを返す。method='auto' で規模別に解法を選ぶ。"""
        if method == "auto":
            method = self._pick_method(len(nodes))

        if method == "exact":
            tour = self._bitmask_dp(nodes, start)
        elif method == "2opt":
            tour = self._two_opt(self._nearest_neighbor(nodes, start))
        else:  # "sa"
            seed_tour = self._two_opt(self._nearest_neighbor(nodes, start))
            tour = self._simulated_annealing(seed_tour)
        return tour, self._cost(tour)

    def _pick_method(self, n: int) -> Method:
        if n <= self._EXACT_MAX:
            return "exact"
        return "2opt" if n <= self._HEURISTIC_MAX else "sa"

    # ---- コスト ----

    def _cost(self, tour: list[str]) -> float:
        return sum(self._dist[(tour[i], tour[i + 1])] for i in range(len(tour) - 1))

    # ---- 厳密解: ビットマスク DP (Held–Karp) ----

    def _bitmask_dp(self, nodes: list[str], start: str) -> list[str]:
        others = [n for n in nodes if n != start]
        n = len(others)
        inf = math.inf
        dp = [[inf] * n for _ in range(1 << n)]
        parent = [[-1] * n for _ in range(1 << n)]
        for j in range(n):
            dp[1 << j][j] = self._dist[(start, others[j])]

        for mask in range(1 << n):
            for j in range(n):
                if not (mask >> j) & 1 or dp[mask][j] == inf:
                    continue
                for k in range(n):
                    if (mask >> k) & 1:
                        continue
                    nmask = mask | (1 << k)
                    cand = dp[mask][j] + self._dist[(others[j], others[k])]
                    if cand < dp[nmask][k]:
                        dp[nmask][k] = cand
                        parent[nmask][k] = j

        full = (1 << n) - 1
        best_j = min(
            range(n), key=lambda j: dp[full][j] + self._dist[(others[j], start)]
        )
        order = self._unwind(parent, full, best_j)
        return [start, *(others[i] for i in order), start]

    @staticmethod
    def _unwind(parent: list[list[int]], full: int, last: int) -> list[int]:
        idx: list[int] = []
        mask, j = full, last
        while j != -1:
            idx.append(j)
            pj = parent[mask][j]
            mask ^= 1 << j
            j = pj
        idx.reverse()
        return idx

    # ---- 近似解: 最近傍 → 2-opt → 焼きなまし ----

    def _nearest_neighbor(self, nodes: list[str], start: str) -> list[str]:
        remaining = {n for n in nodes if n != start}
        tour, cur = [start], start
        while remaining:
            nxt = min(remaining, key=lambda n: self._dist[(cur, n)])
            tour.append(nxt)
            remaining.remove(nxt)
            cur = nxt
        tour.append(start)
        return tour

    def _two_opt(self, tour: list[str]) -> list[str]:
        improved, n = True, len(tour)
        while improved:
            improved = False
            for i in range(1, n - 2):
                for k in range(i + 1, n - 1):
                    a, b, c, d = tour[i - 1], tour[i], tour[k], tour[k + 1]
                    delta = (self._dist[(a, c)] + self._dist[(b, d)]) - (
                        self._dist[(a, b)] + self._dist[(c, d)]
                    )
                    if delta < -1e-9:
                        tour[i : k + 1] = reversed(tour[i : k + 1])
                        improved = True
        return tour

    def _simulated_annealing(self, tour: list[str], iters: int = 5000) -> list[str]:
        cur = list(tour)
        cur_cost = self._cost(cur)
        best, best_cost = list(cur), cur_cost
        temp, cooling = max(cur_cost * 0.1, 1.0), 0.995
        for _ in range(iters):
            i, k = sorted(self._rng.sample(range(1, len(cur) - 1), 2))
            cand = cur[:i] + cur[i : k + 1][::-1] + cur[k + 1 :]
            cand_cost = self._cost(cand)
            accept = cand_cost < cur_cost or self._rng.random() < math.exp(
                -(cand_cost - cur_cost) / max(temp, 1e-9)
            )
            if accept:
                cur, cur_cost = cand, cand_cost
                if cur_cost < best_cost:
                    best, best_cost = list(cur), cur_cost
            temp *= cooling
        return best
