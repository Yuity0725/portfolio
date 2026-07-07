"""部分点採点モデルとスコア計算（技術デモ用の匿名サンプル）。

このファイルはポートフォリオ用に書き起こした簡略版であり、実運用コードではない。
採点ドメインの設計意図を示す:
  - 採点モデルは frozen dataclass の不変な値オブジェクト
  - 採点基準 = 加点グループ（グループ内で高々1つ加点=排他）＋ 減点
  - スコア = Σ加点 − Σ減点 を [0, 満点] にクランプ（純粋計算・副作用なし）

フィールド名・ID・値はすべて一般的な例（プレースホルダ）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class QuestionFormat(Enum):
    """設問の解答形式。"""

    CHOICE = 0        # 選択式
    SHORT_ANSWER = 1  # 短答式
    FREE = 2          # 自由記述
    UNANSWERABLE = 3  # 回答不可（採点対象外）


@dataclass(frozen=True)
class Position:
    """答案上の描画位置（ページ＋座標）。"""

    page: int
    x: float
    y: float


@dataclass(frozen=True)
class Addition:
    """加点（1観点あたりの得点）。"""

    addition_id: str
    description: str
    amount: int


@dataclass(frozen=True)
class Deduction:
    """減点。"""

    deduction_id: str
    description: str
    amount: int


@dataclass(frozen=True)
class AdditionGroup:
    """排他な加点の集合: グループ内から高々1つだけ加点される。"""

    additions: tuple[Addition, ...]


@dataclass(frozen=True)
class Criterion:
    """採点基準: 加点グループ（排他）＋減点。"""

    addition_groups: tuple[AdditionGroup, ...] = ()
    deductions: tuple[Deduction, ...] = ()


@dataclass(frozen=True)
class Question:
    """設問（再帰ツリー: 大問 → 小問）。末端が実際の採点対象。"""

    question_id: str
    max_score: int
    format: QuestionFormat
    criteria: tuple[Criterion, ...] = ()
    children: tuple["Question", ...] = ()
    score_position: Position | None = None
    mark_position: Position | None = None
    comment_position: Position | None = None


@dataclass(frozen=True)
class GradedSelection:
    """採点者（または自動採点）が付与した「該当した加点/減点」の集合。"""

    applied_addition_ids: frozenset[str] = field(default_factory=frozenset)
    applied_deduction_ids: frozenset[str] = field(default_factory=frozenset)


class PartialCreditScorer:
    """設問と採点結果から得点を計算する。

    純粋計算に寄せて副作用を持たせず、境界条件（マイナス点・満点超過・
    二重加点）を型と計算ロジックで安全に扱う。
    """

    def score(self, question: Question, selection: GradedSelection) -> int:
        """1設問のスコアを [0, 満点] にクランプして返す。"""
        total = 0
        for criterion in question.criteria:
            total += self._additions_points(criterion, selection)
            total -= self._deductions_points(criterion, selection)
        return self._clamp(total, question.max_score)

    def _additions_points(
        self, criterion: Criterion, selection: GradedSelection
    ) -> int:
        """加点の合計。各グループから該当加点の最大1つだけを採用（排他）。"""
        subtotal = 0
        for group in criterion.addition_groups:
            applicable = [
                addition.amount
                for addition in group.additions
                if addition.addition_id in selection.applied_addition_ids
            ]
            # 排他: グループ内で該当が複数あっても最大値のみ採用
            if applicable:
                subtotal += max(applicable)
        return subtotal

    def _deductions_points(
        self, criterion: Criterion, selection: GradedSelection
    ) -> int:
        """減点の合計。"""
        return sum(
            deduction.amount
            for deduction in criterion.deductions
            if deduction.deduction_id in selection.applied_deduction_ids
        )

    @staticmethod
    def _clamp(total: int, max_score: int) -> int:
        """スコアを [0, 満点] に収める。"""
        return max(0, min(total, max_score))
