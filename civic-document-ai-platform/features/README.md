# Feature Deep-Dives / 各機能の詳細

Per-feature write-ups focusing on the engineering decisions and their rationale.
機能ごとに、技術的な工夫点と「なぜそうしたか」を掘り下げたドキュメント群。

| # | Feature / 機能 | What it shows / 見どころ |
| --- | --- | --- |
| 01 | [Japanese Full-Text Search / 日本語全文検索](01-japanese-fulltext-search.md) | Sudachi形態素解析・機能別インデックス・検索DSLの型付き抽象化 |
| 02 | [Streaming RAG Chat / RAGチャット](02-rag-chat.md) | BROAD/TARGETED動的検索戦略・コンテキスト最適化・E2Eストリーミング |
| 03 | [Multi-Agent Deep Research / Deep Research](03-deep-research.md) | Mastraマルチエージェント・非同期ジョブ・API/ワーカー分離 |
| 04 | [Document Classification / ドキュメント自動分類](04-document-classification.md) | ルールベース＋スコアリング・本文分類のオプトイン・改善ループ |
| 05 | [Dictionary Automation / 辞書自動管理](05-dictionary-automation.md) | Sudachi辞書の生成→反映→Reindex全自動化 |
| 06 | [Data Sync Pipeline / データ同期パイプライン](06-data-pipeline.md) | 差分同期・並列投入・省メモリ読み出し・変換標準化 |

> 全体像は [../README.md](../README.md)、構成図は [../ARCHITECTURE.md](../ARCHITECTURE.md)、技術一覧は [../TECH_STACK.md](../TECH_STACK.md) を参照。
