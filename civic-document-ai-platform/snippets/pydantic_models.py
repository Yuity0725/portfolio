"""型安全な検索リクエスト/レスポンスモデル（技術デモ用の匿名サンプル）。

このファイルはポートフォリオ用に書き起こした簡略版であり、実運用コードではない。
構造化データは dict ではなく Pydantic BaseModel で表現し、Field の description /
examples でメタデータを明示する、というプロジェクト方針を示す。
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class SearchStrategy(str, Enum):
    """RAGの検索戦略。質問の性質に応じて動的に選択する。"""

    BROAD = "broad"        # 俯瞰的な問い: 全文を広く投入
    TARGETED = "targeted"  # ピンポイントな問い: スニペット類似度で絞り込み


class SearchRequest(BaseModel):
    """検索APIへのリクエスト。境界でバリデーションする。"""

    query: str = Field(
        ...,
        min_length=1,
        max_length=512,
        description="ユーザーの検索クエリ（日本語）",
        examples=["再開発事業の予算はいくらか"],
    )
    index: str = Field(
        default="minutes_full",
        description="検索対象のOpenSearchインデックス名",
        examples=["minutes_full", "gov_documents"],
    )
    top_k: int = Field(
        default=10,
        ge=1,
        le=50,
        description="取得する上位件数",
    )


class Passage(BaseModel):
    """検索でヒットした本文断片（前後文脈を含む）。"""

    document_id: str = Field(..., description="元文書の識別子")
    score: float = Field(..., ge=0.0, description="関連スコア")
    text: str = Field(..., description="ヒット箇所の本文")
    context_before: str = Field(default="", description="ヒット箇所の直前文脈")
    context_after: str = Field(default="", description="ヒット箇所の直後文脈")


class SearchResponse(BaseModel):
    """検索APIのレスポンス。"""

    strategy: SearchStrategy = Field(..., description="適用した検索戦略")
    passages: list[Passage] = Field(default_factory=list, description="ヒット断片の配列")

    @property
    def is_empty(self) -> bool:
        """結果が空かどうか。"""
        return len(self.passages) == 0

    def top_document_ids(self, limit: int = 3) -> list[str]:
        """上位の文書IDを内包表記で抽出する。"""
        return [passage.document_id for passage in self.passages[:limit]]
