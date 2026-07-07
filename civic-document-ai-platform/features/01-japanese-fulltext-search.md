# 01. Japanese Full-Text Search / 日本語全文検索基盤

> Accurate Japanese search over public-sector documents using OpenSearch + Sudachi, with independently-tuned indices.
> OpenSearch＋Sudachiによる、行政文書向けの高精度な日本語全文検索。インデックスを機能別に独立管理して品質を最適化。

関連スニペット: [pydantic_models.py](../snippets/pydantic_models.py) / [rag_query_router.py](../snippets/rag_query_router.py)

---

## 課題 / Problem

行政文書は語彙が特殊（固有名詞・制度用語・複合語）で、英語前提の単純なトークナイズでは正しく分割できない。「再開発事業」「議会運営委員会」などが不適切に切られると検索がヒットしない／ノイズが増える。

Public-sector text is full of domain-specific compound nouns. Naive tokenization mis-segments them, hurting both recall and precision.

## 技術的な工夫 / Key engineering decisions

- **Sudachi形態素解析＋ユーザー辞書**
  日本語を意味単位で正しく分かち書きし、制度固有語はユーザー辞書で1語として扱う。辞書は自動生成・自動更新される（→ [05. 辞書自動管理](05-dictionary-automation.md)）。

- **機能別の独立インデックス設計**
  議事録 / 計画資料 / 計画本文 / 省庁文書 を別インデックスで管理。文書種別ごとにアナライザ・マッピング・スコアリングを個別最適化でき、1つの巨大インデックスに詰め込むより検索品質と運用性が高い。

- **検索DSLのライブラリ化（Pydantic）**
  クエリ組み立てを型付きの共通ライブラリに抽象化し、各API/バッチから再利用。リクエスト/レスポンスはすべて `BaseModel`（[pydantic_models.py](../snippets/pydantic_models.py) 参照）で表現し、`Any` を排除して境界でバリデーション。

- **スニペット検索と全文取得の使い分け**
  ピンポイントな問いには「ヒット箇所＋前後文脈」を返すスニペット検索、俯瞰的な問いには全文（上位N件）を返す全文取得を用意し、上位のRAG層が動的に選択（→ [02. RAGチャット](02-rag-chat.md)）。

- **セキュリティ**
  OpenSearchはVPC内に配置し、セキュリティグループ＋IAMロールでアクセスを限定。

## 効果 / Impact

- 日本語特有の複合語・固有名詞に対する検索の取りこぼしを削減
- インデックス独立化により、文書種別ごとのチューニングとスキーマ変更の影響範囲を局所化
- 検索DSLの共通化で、新しい文書種別の追加コストを低減
