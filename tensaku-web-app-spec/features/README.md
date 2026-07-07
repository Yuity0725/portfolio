# Feature Deep-Dives / 各機能の詳細

Per-feature write-ups focusing on the engineering decisions and their rationale.
機能ごとに、技術的な工夫点と「なぜそうしたか」を掘り下げたドキュメント群。

| # | Feature / 機能 | What it shows / 見どころ |
| --- | --- | --- |
| 01 | [Contract-First Design / コントラクトファースト設計](01-contract-first-design.md) | OpenAPI＋Protobufで契約を先に定義・並行開発・型整合 |
| 02 | [Partial-Credit Scoring / 部分点採点モデル](02-partial-credit-scoring.md) | 設問ツリー・加点グループ（排他）・減点・クランプの型設計 |

> 全体像は [../README.md](../README.md)、契約・採点モデル図は [../ARCHITECTURE.md](../ARCHITECTURE.md)、技術一覧は [../TECH_STACK.md](../TECH_STACK.md) を参照。
