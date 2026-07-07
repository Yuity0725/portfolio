# Tech Stack / 技術スタック

The stack used across the inference platform. Versions reflect what was actually deployed.
推論基盤全体で使用した技術一覧。バージョンは実際に構築した系を記載。

## Hardware / ハードウェア

| Technology | Spec | Purpose / 用途 |
| --- | --- | --- |
| NVIDIA DGX Spark × 2 | GB10 Superchip | 推論ノード（Node 1 = ヘッド / Node 2 = ワーカー） |
| GB10 (Grace Blackwell) | compute capability 12.1 (`sm_121`) | Grace CPU (ARM64) + Blackwell GPU、統合メモリ約120GB/ノード |
| 200GbE QSFP DAC | direct link | ノード間直結インターコネクト（スイッチレス） |
| RoCE v2 | RDMA over Converged Ethernet | NCCL / RPC / 同期のRDMA転送 |

## Inference backends / 推論バックエンド

| Technology | Version | Purpose / 用途 |
| --- | --- | --- |
| llama.cpp (llama-server) | b8xxx 系 CUDAビルド | 主力エンジン。GGUF量子化モデルのOpenAI互換サービング・連続バッチング |
| llama.cpp RPC (rpc-server) | 同上（`GGML_RPC=ON`ビルド） | 単一巨大モデルの2ノード分割（PoC） |
| vLLM | NVIDIA NGC コンテナ | 70B級モデルのサービング（FP8 / safetensors） |
| Ray | vLLM同梱 | 2ノードクラスタ化・Tensor Parallel実行基盤 |
| SGLang | Docker | 比較検証用バックエンド |
| nginx | distro標準 | データ並列レプリカのロードバランサ（ラウンドロビン） |

## Models / モデル

| Model | Format | Purpose / 用途 |
| --- | --- | --- |
| Qwen3-30B-A3B (MoE) | GGUF Q4_K_M | 主力。分類・抽出バッチ（プリフィル律速タスクで dense 比大幅高速） |
| Qwen3-32B / Qwen3-14B (dense) | GGUF Q4_K_M | 比較ベンチ・精度検証 |
| Qwen3.6-35B-A3B | safetensors FP8 | vLLM系での本番候補 |
| LFM2.5-1.2B (JP) | GGUF Q4_K_M | 小型・低レイテンシ用途（日本語版含む） |
| GLM-OCR | GGUF F16 | マルチモーダルOCR |

## Build & runtime / ビルド・ランタイム

| Technology | Version | Purpose / 用途 |
| --- | --- | --- |
| CUDA Toolkit | 13.0 | GPUランタイム・nvcc（`sbsa-linux` / ARM64） |
| CMake | — | llama.cppビルド（`CMAKE_CUDA_ARCHITECTURES=121` 明示） |
| Docker + NVIDIA Container Toolkit | — | vLLM / SGLang コンテナ実行 |
| Ubuntu (DGX OS) | ARM64 | ノードOS |

## Model ops & tooling / モデル管理・ツール

| Technology | Purpose / 用途 |
| --- | --- |
| Hugging Face CLI (`hf download`) | GGUF / safetensors の取得 |
| rsync (over 200GbE) | ノード間モデル同期 |
| md5sum | 同期後の整合性検証 |
| Python venv（最小構成） | `huggingface_hub` / `openai` のみ。モデルDLとAPI疎通確認専用 |
| OpenSSH (ed25519, passwordless) | クラスタ操作・リモート起動 |

## Client & quality / クライアント・品質

| Technology | Purpose / 用途 |
| --- | --- |
| OpenAI Python SDK (AsyncOpenAI) | OpenAI互換エンドポイントへの並列クライアント |
| JSON Schema + GBNF constrained decoding | 構造化出力のスキーマ準拠強制（`response_format=json_schema`） |
| Pydantic 2.x | クライアント側の型安全な結果バインド（`model_validate_json`） |
| 自作ベンチハーネス | スループット・スキーマ準拠率・並列度スイープの実測 |
