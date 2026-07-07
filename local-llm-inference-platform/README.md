# Local LLM Inference Platform

> Design, build, and operation of an on-premises LLM inference platform on a 2-node NVIDIA DGX Spark (GB10) cluster — multi-backend (llama.cpp / vLLM), three distribution strategies, and workload-driven model selection.
>
> NVIDIA DGX Spark（GB10）2ノードクラスタ上に構築した、オンプレミスLLM推論基盤の設計・構築・運用。llama.cpp / vLLM のマルチバックエンド構成、3種類の分散方式、ワークロード駆動のモデル選定。

> **Note / 注記**
> This is a **portfolio case study**. All hostnames, IP addresses, and paths shown in this repository are **placeholders**; scripts and configs are hand-authored illustrations, not the operational originals.
> これは**ポートフォリオ用のケーススタディ**です。掲載しているホスト名・IPアドレス・パスはすべて**プレースホルダ**であり、スクリプト・設定は説明用に書き起こしたもので、実運用のものではありません。

---

## English (Summary)

An on-premises inference platform for serving open-weight LLMs on sensitive data that must not leave the premises. Two NVIDIA DGX Spark nodes (GB10 — Grace Blackwell, unified memory ~120 GB/node, ARM64) are directly linked with **200 GbE + RoCE v2 (RDMA)** and serve models through **two backends and three distribution strategies**, chosen per workload:

- **llama.cpp (CUDA build for `sm_121`)** as the primary engine for quantized GGUF models — single-node, **data-parallel replicas behind an nginx load balancer** (main throughput configuration), or **RPC-distributed** when a single model exceeds one node's memory.
- **vLLM + Ray** with **tensor parallelism across both nodes** for 70B-class models in FP8/safetensors.

**Highlights**
- **Workload-driven topology selection** — a decision framework mapping model size × throughput needs to the four serving configurations, validated with real benchmarks (prefill-bound classification workloads, MoE vs. dense).
- **ARM64 + CUDA 13 + `sm_121` build engineering** — building llama.cpp for the Grace Blackwell architecture (`CMAKE_CUDA_ARCHITECTURES=121`), where default builds fail with `no kernel image`.
- **Model operations** — GGUF (Q4_K_M) / FP8 safetensors / F16 assets managed per-backend, downloaded via the Hugging Face CLI and synchronized across nodes over 200 GbE with checksum verification.
- **Structured-output serving** — OpenAI-compatible endpoints with JSON-Schema constrained decoding (GBNF), consumed by Pydantic-validated clients.
- **Runbook-first operations** — every start/stop/scale/model-update procedure documented as a reproducible runbook instead of tribal knowledge.

See **[ARCHITECTURE.md](ARCHITECTURE.md)** for diagrams and **[TECH_STACK.md](TECH_STACK.md)** for the full stack.

---

## 日本語（詳細）

### これは何か

外部APIに出せない機密性の高いデータ（例: 行政文書・業務データ）に対してLLM処理を行うための、**完全オンプレミスの推論基盤**です。NVIDIA DGX Spark（GB10）2台を200GbEで直結したクラスタ上に、オープンウェイトモデル（Qwen3系ほか）を複数のバックエンド・分散方式で配備し、下流のアプリケーション（文書分類・情報抽出など）へOpenAI互換APIとして提供します。

### 解決した課題 → アプローチ

| 課題 | アプローチ |
| --- | --- |
| 機密データを外部LLM APIへ送信できない | オープンウェイトモデルをオンプレ推論。全処理がクラスタ内で完結 |
| 1ノードのメモリ（約120GB）を超えるモデルを動かしたい | **vLLM + Ray のTensor Parallel**（2ノード分割）と **llama.cpp RPC分散** の2方式を検証・使い分け |
| 10〜30Bクラスの大量バッチ処理でスループットが欲しい | 各ノードに同一モデルを配置し **nginxロードバランサでデータ並列**（主用途構成） |
| GB10（ARM64/Grace + `sm_121`）でOSSがそのまま動かない | CUDAアーキテクチャ明示ビルド等、実機での動作条件を確立しrunbook化 |
| モデル資産（数十GB）の管理・2ノード間同期 | HF CLIでの取得 → 200GbE経由rsync同期 → チェックサム検証、を手順化 |

### 主要機能

1. **マルチバックエンド構成** — llama.cpp（GGUF/量子化・軽量高速）と vLLM（FP8/safetensors・大規模TP）をワークロードで使い分け
2. **3種の分散方式** — Tensor Parallel（モデル分割）/ データ並列レプリカ＋nginx LB（スループット）/ RPC分散（メモリ超過時）
3. **OpenAI互換サービング** — `response_format=json_schema` による制約デコード対応。下流はPydanticで型安全に受領
4. **モデルオペレーション** — 量子化形式（Q4_K_M / FP8 / F16）を用途別に選定し、取得・配置・ノード間同期を標準化
5. **ベンチマーク駆動の構成選定** — プリフィル律速の特定、MoE vs dense、並列度スイープなど実測に基づく意思決定

### 技術的な工夫（抜粋）

- **「モデル規模 × 要求特性 → 構成」の選択フレームワーク**を確立し、4構成（vLLM TP / llama.cpp単体 / レプリカ+LB / RPC）を迷わず選べるようにした → [features/02-distributed-inference.md](features/02-distributed-inference.md)
- **200GbE直結 + RoCE v2（RDMA）** をノード間インターコネクトに採用し、TP通信・RPC・モデル同期を高速化
- **`CMAKE_CUDA_ARCHITECTURES=121` の明示指定**ほか、GB10（ARM64 + CUDA 13）でのビルド要件を確立 → [features/03-cuda-arm-build.md](features/03-cuda-arm-build.md)
- **プレフィル律速の性能モデル**（docs/s ≒ prefill速度 ÷ プロンプトtoken数）を実測で裏付け、モデル選定（MoE採用）とバッチ設計に反映
- **推論本体とPythonツールの分離** — サービングはネイティブバイナリ/コンテナに任せ、Python環境はモデルDLとAPI検証用の最小構成に留める

### 担当領域

ハードウェア選定後のクラスタ設計〜OS/ネットワーク設定（200GbE/RoCE）〜推論スタック構築〜ベンチマーク〜運用手順書の整備までを一人で担当。

---

## Feature deep-dives / 各機能の詳細

| # | Feature / 機能 | 見どころ / Highlights |
| --- | --- | --- |
| 01 | [マルチバックエンド戦略 / Multi-Backend Strategy](features/01-multi-backend-strategy.md) | llama.cpp vs vLLM vs SGLang の技術選定と使い分け基準 |
| 02 | [分散推論 / Distributed Inference](features/02-distributed-inference.md) | TP・データ並列レプリカ・RPC分散の3方式比較と選択フレームワーク |
| 03 | [ARM64+CUDAビルド / CUDA on ARM64 Build](features/03-cuda-arm-build.md) | GB10（`sm_121`, CUDA 13, Grace/aarch64）向けビルドの要点 |
| 04 | [モデルオペレーション / Model Ops](features/04-model-ops.md) | 量子化選定・HF CLI取得・ノード間同期・整合性検証 |

## Repository layout / このリポジトリの構成

```
local-llm-inference-platform/
├── README.md            # 本書 / this file
├── ARCHITECTURE.md      # 構成図（Mermaid）と設計判断 / diagrams & design decisions
├── TECH_STACK.md        # 技術スタック一覧 / full tech stack table
├── features/            # 各テーマの工夫点（個別ドキュメント）/ per-topic deep-dives
│   ├── 01-multi-backend-strategy.md
│   ├── 02-distributed-inference.md
│   ├── 03-cuda-arm-build.md
│   └── 04-model-ops.md
└── snippets/            # 匿名の技術デモ用サンプル / anonymized illustrative samples
    ├── llama_server_lb.conf
    ├── run_two_node_cluster.sh
    └── structured_client.py
```

## Disclaimer / ディスクレーマー

All identifiers (hostnames, IP addresses, usernames, paths, ports) shown anywhere in this repository are **placeholders**. The snippets are simplified illustrations authored for this portfolio and are **not** the operational originals.

本リポジトリ内の識別子（ホスト名・IPアドレス・ユーザー名・パス・ポート等）はすべて**プレースホルダ**です。掲載しているスクリプト・設定はポートフォリオ用に簡略化して書き起こしたものであり、実運用のものではありません。
