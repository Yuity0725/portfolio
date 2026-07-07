# Civic Document Intelligence Platform

> AI-powered cross-search, summarization, and deep-research platform for Japanese public-sector documents (local-government council minutes, plans, budgets, and ministry documents).
>
> 日本の行政公開文書（自治体の議会議事録・計画・予算、および省庁文書）を横断的にAI検索・要約・深掘り分析する基盤。

> **Note / 注記**
> This is a **portfolio case study**. To protect commercial IP and credentials, no proprietary source code is published here — the repository contains architecture write-ups and **hand-authored, anonymized snippets** that illustrate the engineering.
> これは**ポートフォリオ用のケーススタディ**です。商用IPと認証情報保護のため実プロダクトのソースは掲載していません。掲載コードはすべて**技術デモ用に書き起こした匿名サンプル**です。

---

## English (Summary)

A production system that makes Japan's vast, hard-to-navigate public-sector documents accessible to citizens and analysts. It combines **Japanese-aware full-text search (OpenSearch + Sudachi)**, a **streaming RAG chat (Gemini)**, and a **multi-agent deep-research** capability, on a **serverless AWS backend** driven by an automated **TiDB → OpenSearch data pipeline**.

Engineered end-to-end by a single engineer: frontend, multiple backend services (Python & Node.js), the data pipeline, and the Infrastructure-as-Code.

**Highlights**
- **Multi-language full-stack** — Next.js/TypeScript frontend, FastAPI/Python and Node.js/Mastra backends.
- **Serverless-first AWS** — Lambda (arm64) via Lambda Web Adapter, API Gateway **response streaming**, ECS Fargate batch orchestrated by Step Functions + EventBridge.
- **AI / RAG** — Gemini with SSE streaming, a dynamic **BROAD vs. TARGETED** retrieval strategy, and multi-agent research (Mastra + Exa web search).
- **Japanese search** — OpenSearch with **Sudachi** morphological analysis; user & synonym dictionaries auto-generated and re-indexed on a schedule.
- **Scalable data pipeline** — a reusable **TiDB → OpenSearch** sync library with incremental (delta) sync and parallel bulk ingestion.
- **Quality & operability** — Terraform IaC, Pydantic type-safety everywhere, observability via Logfire + OpenTelemetry + X-Ray.

See **[ARCHITECTURE.md](ARCHITECTURE.md)** for diagrams and **[TECH_STACK.md](TECH_STACK.md)** for the full stack.

---

## 日本語（詳細）

### これは何か

日本の自治体・省庁が公開している膨大な行政文書（議会議事録・計画資料・予算書・省庁文書など）は、量が多く構造も不揃いで、市民や有識者が「知りたいことを探す」のが困難です。本プロジェクトは、それらの公開文書を **AIで横断検索・要約・深掘り分析** できるようにする基盤です。

### 解決した課題 → アプローチ

| 課題 | アプローチ |
| --- | --- |
| 大量・不揃いの行政文書へアクセスしづらい | OpenSearch＋**Sudachi**による日本語全文検索。用語辞書・シノニム辞書を自動生成し検索品質を維持 |
| キーワードだけでは要点にたどり着けない | 検索結果を根拠にした**RAGチャット**（Geminiのストリーミング応答）で対話的に要約・回答 |
| 単純検索では見つからない関係性・動向 | **マルチエージェントのDeep Research**が関連情報を自動で掘り下げてレポート化 |
| 継続的に増えるソースデータの取り込み | **TiDB → OpenSearch** を差分同期・並列投入する基盤ライブラリ＋定期バッチで自動更新 |

### 主要機能

1. **全文検索基盤** — 議事録・計画資料・省庁文書を独立インデックスで横断検索
2. **RAGチャット** — 検索コンテキストを与え、議事録について対話形式で回答（SSEストリーミング）
3. **Deep Research** — エージェントがキーワードから自動で関連調査を実行しレポート生成
4. **ドキュメント自動分類** — ルールベース＋スコアリングで行政文書を分類
5. **辞書自動管理** — Sudachi用ユーザー辞書/シノニム辞書を自動生成し、OpenSearchパッケージを更新・Reindex
6. **データ同期** — 自治体データ／省庁データを TiDB から OpenSearch へ定期同期

### 技術的な工夫（抜粋）

- **API Gatewayレスポンスストリーミング × Lambda Web Adapter** で、サーバーレスながらAIのリアルタイム応答とコールドスタート最小化を両立
- **入力分類（BROAD / TARGETED）** によりRAGの検索戦略を動的に切り替え、コンテキスト構築を最適化 → 実装イメージは [snippets/rag_query_router.py](snippets/rag_query_router.py)
- **差分同期＋並列投入**（`is_opensearch` フラグで未同期分を追跡、パーティション単位で並列ワーカー投入）で大量データ投入を高速化 → [snippets/tidb_opensearch_sync.py](snippets/tidb_opensearch_sync.py)
- **arm64（Graviton）** 採用でコスト最適化、**Step Functions＋EventBridge Scheduler** でバッチを直列・定期実行
- **型安全徹底** — 構造化データはすべて Pydantic `BaseModel`、`Any` を排除 → [snippets/pydantic_models.py](snippets/pydantic_models.py)

### 担当領域

設計〜実装〜インフラ〜運用までを一気通貫で担当（フロントエンド、Python/Node.js の複数バックエンド、データパイプライン、Terraform IaC、CI/CD）。

---

## Feature deep-dives / 各機能の詳細

各機能ごとに技術的な工夫点をまとめた個別ドキュメントを用意しています（→ [features/](features/README.md)）。

| # | Feature / 機能 | 見どころ / Highlights |
| --- | --- | --- |
| 01 | [日本語全文検索 / Full-Text Search](features/01-japanese-fulltext-search.md) | Sudachi形態素解析・機能別インデックス・検索DSLの型付き抽象化 |
| 02 | [RAGチャット / Streaming RAG Chat](features/02-rag-chat.md) | BROAD/TARGETED動的検索戦略・コンテキスト最適化・E2Eストリーミング |
| 03 | [Deep Research / Multi-Agent Research](features/03-deep-research.md) | Mastraマルチエージェント・非同期ジョブ・API/ワーカー分離 |
| 04 | [ドキュメント自動分類 / Classification](features/04-document-classification.md) | ルールベース＋スコアリング・本文分類のオプトイン・改善ループ |
| 05 | [辞書自動管理 / Dictionary Automation](features/05-dictionary-automation.md) | Sudachi辞書の生成→反映→Reindex全自動化 |
| 06 | [データ同期パイプライン / Data Pipeline](features/06-data-pipeline.md) | 差分同期・並列投入・省メモリ読み出し・変換標準化 |

## Repository layout / このリポジトリの構成

```
civic-document-ai-platform/
├── README.md            # 本書 / this file
├── ARCHITECTURE.md      # 構成図（Mermaid）と設計判断 / diagrams & design decisions
├── TECH_STACK.md        # 技術スタック一覧 / full tech stack table
├── features/            # 各機能の工夫点（個別ドキュメント）/ per-feature deep-dives
│   ├── 01-japanese-fulltext-search.md
│   ├── 02-rag-chat.md
│   ├── 03-deep-research.md
│   ├── 04-document-classification.md
│   ├── 05-dictionary-automation.md
│   └── 06-data-pipeline.md
└── snippets/            # 匿名の技術デモ用サンプル / anonymized illustrative samples
    ├── pydantic_models.py
    ├── fastapi_lambda_handler.py
    ├── rag_query_router.py
    ├── tidb_opensearch_sync.py
    └── lambda_apigw.tf
```

## Disclaimer / ディスクレーマー

All identifiers (account IDs, endpoints, hostnames, keys) shown anywhere in this repository are **placeholders**. The snippets are simplified illustrations authored for this portfolio and are **not** the production source.

本リポジトリ内の識別子（アカウントID・エンドポイント・ホスト名・キー等）はすべて**プレースホルダ**です。掲載コードはポートフォリオ用に簡略化して書き起こしたものであり、実運用ソースではありません。
