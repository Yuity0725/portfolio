# Feature Deep-Dives / 各機能の詳細

Per-topic write-ups focusing on the engineering decisions and their rationale.
トピックごとに、技術的な工夫点と「なぜそうしたか」を掘り下げたドキュメント群。

| # | Topic / トピック | What it shows / 見どころ |
| --- | --- | --- |
| 01 | [Modular Monolith / モジュラーモノリス構成](01-modular-monolith.md) | 境界づけられたコンテキスト・単一デプロイ・なぜマイクロサービスにしないか |
| 02 | [Clean Architecture & DDD / クリーンアーキテクチャとDDD](02-clean-architecture-ddd.md) | domain/usecase/adapter・依存性逆転・Repository/Specification/Builder |
| 03 | [Type Safety & Testing / 型安全とテスト戦略](03-type-safety-and-testing.md) | Pydantic境界・mypy/flake8・フェイク差し替えのユニット/インテグレーション |
| 04 | [Operations Integration / 運用連携](04-operations-integration.md) | Slackファサード・レガシー腐敗防止層・LP割当の内部API |

> 全体像は [../README.md](../README.md)、構成図は [../ARCHITECTURE.md](../ARCHITECTURE.md)、技術一覧は [../TECH_STACK.md](../TECH_STACK.md) を参照。
