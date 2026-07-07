"""質問をBROAD/TARGETEDに分類し検索戦略を切り替える設計（技術デモ用の匿名サンプル）。

このファイルはポートフォリオ用に書き起こした簡略版であり、実運用コードではない。
RAGの中核である「入力分類 → 検索戦略の動的切替 → コンテキスト構築」の骨子を示す。
ネストは早期returnで浅く保ち、1関数1責務を意識する。
"""

from __future__ import annotations

from pydantic_models import (
    Passage,
    SearchRequest,
    SearchResponse,
    SearchStrategy,
)


class SearchBackend:
    """OpenSearch検索のインターフェース（デモ用スタブ）。"""

    def snippet_search(self, query: str, top_k: int) -> list[Passage]:
        """スニペット類似度で絞り込み、前後文脈付きで返す（TARGETED用）。"""
        raise NotImplementedError

    def full_document_search(self, query: str, top_k: int) -> list[Passage]:
        """全文（上位N件）を返す（BROAD用）。"""
        raise NotImplementedError


class QueryClassifier:
    """質問の性質から検索戦略を判定する。

    実運用ではLLMや軽量分類器を用いるが、ここでは意図が伝わる簡易ルールで示す。
    """

    # ピンポイントな問いを示唆する手掛かり語（マジックワードは定数化）
    _TARGETED_CUES: tuple[str, ...] = ("いくら", "何円", "誰が", "いつ", "件数", "予算")

    def classify(self, query: str) -> SearchStrategy:
        """クエリを分類する。手掛かり語を含めばTARGETED、なければBROAD。"""
        has_targeted_cue = any(cue in query for cue in self._TARGETED_CUES)
        return SearchStrategy.TARGETED if has_targeted_cue else SearchStrategy.BROAD


class RagQueryRouter:
    """分類結果に応じて検索を振り分けるルーター。"""

    def __init__(self, backend: SearchBackend, classifier: QueryClassifier) -> None:
        self._backend = backend
        self._classifier = classifier

    def route(self, request: SearchRequest) -> SearchResponse:
        """検索戦略を選び、対応する検索を実行して結果を返す。"""
        strategy = self._classifier.classify(request.query)

        # 早期returnで戦略ごとの分岐を浅く保つ
        if strategy is SearchStrategy.TARGETED:
            passages = self._backend.snippet_search(request.query, request.top_k)
            return SearchResponse(strategy=strategy, passages=self._dedupe(passages))

        passages = self._backend.full_document_search(request.query, request.top_k)
        return SearchResponse(strategy=strategy, passages=self._dedupe(passages))

    @staticmethod
    def _dedupe(passages: list[Passage]) -> list[Passage]:
        """文書IDで重複を除去し、限られたトークン枠を有効活用する。"""
        seen: set[str] = set()
        unique: list[Passage] = []
        for passage in passages:
            if passage.document_id in seen:
                continue
            seen.add(passage.document_id)
            unique.append(passage)
        return unique
