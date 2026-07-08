# Feature Deep-Dives / 各機能の詳細

Per-feature write-ups focusing on the engineering decisions and their rationale.
機能ごとに、技術的な工夫点と「なぜそうしたか」を掘り下げたドキュメント群。

| # | Feature / 機能 | What it shows / 見どころ |
| --- | --- | --- |
| 01 | [LLM Tool Routing / ツール自動選択](01-llm-tool-routing.md) | pydantic-ai Agent・`RunContext` 依存注入・型付き戻り値・引数モデルでTools API制約を回避 |
| 02 | [OR Algorithms / 最適化アルゴリズムの自前実装](02-optimization-algorithms.md) | RCSP/CPM/Orienteering の状態DP・TSP規模別解法・最大流のノード分割・最小費用流の network simplex |
| 03 | [Cross-Cutting Constraints / 横断的な制約適用](03-cross-cutting-constraints.md) | `min_throughput` フック・`blocked_nodes/edges`・不変な `GraphModel.mutate()` |
| 04 | [Conversational UI / 対話UIと可視化](04-conversational-ui.md) | Streamlit マルチターン・`session_state`・描画モード自動切替・agraph 経路/フローハイライト |

> 全体像は [../README.md](../README.md)、構成図は [../ARCHITECTURE.md](../ARCHITECTURE.md)、技術一覧は [../TECH_STACK.md](../TECH_STACK.md) を参照。
