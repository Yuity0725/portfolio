# Feature Deep-Dives / 各テーマの詳細

Per-topic write-ups focusing on the engineering decisions and their rationale.
テーマごとに、技術的な工夫点と「なぜそうしたか」を掘り下げたドキュメント群。

| # | Feature / 機能 | What it shows / 見どころ |
| --- | --- | --- |
| 01 | [Multi-Backend Strategy / マルチバックエンド戦略](01-multi-backend-strategy.md) | llama.cpp vs vLLM vs SGLang の技術選定と使い分け基準 |
| 02 | [Distributed Inference / 分散推論](02-distributed-inference.md) | TP・データ並列レプリカ・RPC分散の3方式比較と選択フレームワーク |
| 03 | [CUDA on ARM64 Build / ARM64+CUDAビルド](03-cuda-arm-build.md) | GB10（`sm_121`, CUDA 13, Grace/aarch64）向けビルドの要点 |
| 04 | [Model Ops / モデルオペレーション](04-model-ops.md) | 量子化選定・HF CLI取得・ノード間同期・整合性検証 |

> 全体像は [../README.md](../README.md)、構成図は [../ARCHITECTURE.md](../ARCHITECTURE.md)、技術一覧は [../TECH_STACK.md](../TECH_STACK.md) を参照。
