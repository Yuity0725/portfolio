# Tech Stack / 技術スタック

The stack used across the demo. Versions reflect the minimums pinned in the project.
デモ全体で使用した技術一覧。バージョンはプロジェクトで固定した下限（`>=`）を記載。

## Core language / 言語

| Technology | Version | Purpose / 用途 |
| --- | --- | --- |
| Python | 3.11+ | 実装言語（`X | None` 記法・`dataclass` を多用） |

## Agent / LLM

| Technology | Version | Purpose / 用途 |
| --- | --- | --- |
| pydantic-ai | >= 0.0.14 | LLMエージェント基盤。`Agent[Deps, Out]`・`@agent.tool`・`RunContext` DI・`run_sync` |
| OpenAI Chat models | — | 推論・ツール選択・結果要約（モデルIDは `OPENAI_MODEL` 環境変数で指定） |
| Pydantic | >= 2.7 | ツール入出力の型定義・境界バリデーション（`BaseModel` / `Field`） |
| python-dotenv | >= 1.0 | `.env` からの環境変数読み込み（APIキー・モデルID） |

## Optimization core / 最適化コア

| Technology | Version | Purpose / 用途 |
| --- | --- | --- |
| NetworkX | >= 3.2 | グラフ表現と一部アルゴリズムの土台（`dijkstra`・`dag_longest_path`・`minimum_cut`・`network_simplex`） |
| Pure Python (自作) | — | RCSP / Orienteering の状態DP、TSP（ビットマスクDP・2-opt・焼きなまし）、フロー分解、ボトルネック抽出 |

## UI / Visualization / UI・可視化

| Technology | Version | Purpose / 用途 |
| --- | --- | --- |
| Streamlit | >= 1.36 | シングルページUI・マルチターンチャット・`session_state` 状態管理・`st.rerun` |
| streamlit-agraph | >= 0.0.45 | 工程グラフの描画（vis.js ベース）。経路ハイライト・フロー太さ・ボトルネック警告・階層レイアウト |

## Data model / データモデル

| Technology | Purpose / 用途 |
| --- | --- |
| JSON (DAG 定義) | ノード（`t_proc` / `v` / `lanes`）とエッジ（`t_move` / `cap`）を定義。読み込み時に `GraphModel` へマッピング |
| dataclass (frozen) | `Node` / `Edge` を不変値オブジェクトとして表現。派生 `cap` は `@property` で計算 |

## Config & Dev / 設定・開発

| Technology | Purpose / 用途 |
| --- | --- |
| 環境変数（`OPENAI_API_KEY` / `OPENAI_MODEL` / `DAG_PATH`） | 秘密情報・モデル選択・データパスの注入（コードにハードコードしない） |
| venv | ローカル実行環境の分離 |

> LLM への接続はすべて環境変数経由で、キーはリポジトリに含めません。数値計算は LLM ではなく自作アルゴリズムが担当し、決定的な解を返します。
