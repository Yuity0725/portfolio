# Manufacturing Optimization Agent / 製造工程 最適化エージェント

> An LLM × mathematical-optimization agent: describe a planning problem in natural language, and an agent picks the right optimization tool, runs a hand-implemented algorithm over a manufacturing-process graph, and answers in chat with a highlighted route / flow visualization.
>
> LLM × 数理最適化のエージェント。製造工程のグラフに対して自然言語で依頼すると、エージェントが最適なツールを選び、自作の最適化アルゴリズムを実行し、チャット回答と経路・フローのハイライト可視化で返す。

> **Note / 注記**
> This is a **portfolio case study** of the author's own public demo. The full application source has been removed; what remains are architecture write-ups and **hand-authored, anonymized snippets** that illustrate the engineering.
> これは作者自身の公開デモを題材にした**ポートフォリオ用のケーススタディ**です。アプリの全ソースは掲載しておらず、残しているのは設計解説と、**技術デモ用に書き起こした匿名サンプル**のみです。

---

## English (Summary)

A single-page demo that turns natural-language questions about a factory line into concrete optimization answers. A [pydantic-ai](https://ai.pydantic.dev/) `Agent` reads a request such as *"find the shortest route to G that clears a value of 100"* or *"where is the bottleneck?"*, **selects one of nine optimization tools**, runs the corresponding **hand-implemented algorithm** over a manufacturing-process **DAG**, and returns a short chat answer plus a **highlighted route / flow visualization** rendered with `streamlit-agraph`.

The graph is the domain model: **nodes are factories** (`t_proc` processing time, `v` value, `lanes` parallel lines → a derived hourly `cap`acity), and **edges are transport links** (`t_move` minutes, `cap` throughput). Around eight classic OR algorithms are implemented from scratch on top of this model, and a single cross-cutting `min_throughput` hook lets any single-route query be re-solved on a capacity-filtered graph.

Built end-to-end by one engineer: concept, UI, the agent layer, and all eight algorithms.

**Highlights**
- **LLM-driven tool routing** — a pydantic-ai `Agent` reads the request and auto-selects one of nine typed tools; a `RunContext`-injected graph is the shared dependency.
- **~8 OR algorithms, hand-implemented** — RCSP (DP), Dijkstra, Orienteering (budgeted max-value DP), CPM (DAG longest path), TSP (bitmask DP / 2-opt / simulated annealing, **auto-selected by size**), Max-Flow (**node-splitting**), Bottleneck, Min-Cost-Flow (**network simplex**).
- **Typed tool boundaries** — every tool returns a Pydantic `BaseModel`; the UI dispatches on the *shape* of the result, not on brittle string parsing.
- **One cross-cutting constraint** — a shared `min_throughput` hook derives capacity and auto-blocks under-capacity nodes/edges via an immutable `GraphModel.mutate()`.
- **Conversational UI with live visualization** — Streamlit multi-turn chat kept in `session_state`, with an agraph view that **auto-switches rendering mode** (single route / multi-route flow / bottleneck warning) based on the tool result.

See **[ARCHITECTURE.md](ARCHITECTURE.md)** for diagrams and **[TECH_STACK.md](TECH_STACK.md)** for the full stack.

---

## 日本語（詳細）

### これは何か

製造ラインの計画に関する問いは、見た目が似ていても「最短経路」「価値制約付き最短」「時間予算内の最大価値」「クリティカルパス」「巡回」「最大スループット」「ボトルネック」「最小費用フロー」と、**必要な数理最適化の道具が毎回違います**。本プロジェクトは、これらを**自然言語の依頼から自動で選び分けて解く**エージェント型のデモです。

工程は **DAG（有向非巡回グラフ）** でモデル化します。

- **ノード（工場）**: `t_proc`（分/個）、`v`（価値/個）、`lanes`（並列ライン数）
  → 派生スループット `cap = lanes × 60 / t_proc`（個/h）
- **エッジ（配送路）**: `t_move`（分）、`cap`（個/h）

このモデルの上に、古典的な最適化アルゴリズムを**約8種類すべて自前で実装**し、pydantic-ai の `Agent` がユーザーの依頼を読んで適切な1つのツールを呼び出します。結果はすべて型付きの Pydantic `BaseModel` で返り、Streamlit UI がその形に応じて可視化モードを切り替えます。

### 解決した課題 → アプローチ

| 課題 | アプローチ |
| --- | --- |
| 似た依頼でも最適な解法が毎回違い、利用者が手法を選べない | **pydantic-ai の Agent** が依頼文を解釈し、登録された9ツールから最適な1つを自動選択（[feature 01](features/01-llm-tool-routing.md)） |
| 最短・価値制約・時間予算・巡回・フローなど多様な問いを1つの土台で解きたい | 共通の `GraphModel` 上に **RCSP / Dijkstra / Orienteering / CPM / TSP / 最大流 / ボトルネック / 最小費用流** を自前実装（[feature 02](features/02-optimization-algorithms.md)） |
| 「1時間にX個以上流せる経路で」等のスループット条件を全ツール共通で効かせたい | 派生 `cap` を用いた横断フック `min_throughput` が、容量不足のノード/エッジを `GraphModel.mutate()` で自動除外（[feature 03](features/03-cross-cutting-constraints.md)） |
| 結果を現場が直感的に理解でき、対話を継続できるUIにしたい | Streamlit マルチターン＋`session_state`、`streamlit-agraph` で**結果の形に応じて描画モードを自動切替**（[feature 04](features/04-conversational-ui.md)） |

### 主要機能

1. **ツール自動選択** — 依頼文から `rcsp_tool` / `shortest_time_tool` / `max_value_tool` / `critical_path_tool` / `tour_tool` / `max_flow_tool` / `bottleneck_tool` / `min_cost_flow_tool` を Agent が選択
2. **数理最適化エンジン** — 単一経路系（DP・Dijkstra・DAG最長路・巡回）とフロー系（最大流・最小費用流）を自前実装
3. **横断的な容量制約** — `min_throughput` と `blocked_nodes` / `blocked_edges` を `mutate()` で適用し、派生グラフ上で再求解
4. **対話UIと可視化** — チャット履歴の継続、経路ハイライト、フロー太さ表現、ボトルネック警告表示の自動切替

質問例とツールの対応（実際に UI で通る依頼の例）:

| ツール | 質問例 |
|---|---|
| `rcsp_tool` | 価値 100 以上を満たして S から G まで最短で完成させたい |
| `shortest_time_tool` | 価値は気にしない、とにかく最短時間で完成までの経路は？ |
| `max_value_tool` | 90 分以内で集められる価値の上限は？ |
| `critical_path_tool` | 全工程を経た場合の完成時間下限を知りたい |
| `rcsp_tool` + blocked | 工場 F3 が停止中。閾値 100 維持で最短経路は？ |
| `tour_tool` | 視察で F1..F8 を 1 回ずつ回りたい、最短は？ |
| `max_flow_tool` | ピーク時に S から G まで 1 時間に何個流せる？ |
| `bottleneck_tool` | どこがボトルネック？どの工場・配送路を増強すれば一番効く？ |
| `min_cost_flow_tool` | 1 時間に 30 個を最小コストで流す計画は？ |
| `rcsp_tool` + `min_throughput` | 1 時間に 15 個以上流せる経路で、価値 100 以上を満たし最短で |

### 技術的な工夫（抜粋）

- **型付きの依存注入（DI）でツールを定義** — `Agent[GraphCtx, str]` に `deps_type` としてグラフを渡し、各ツールは `RunContext[GraphCtx]` からグラフを取得。ツールの戻り値はすべて Pydantic `BaseModel` にして OpenAI Tools API の制約（tuple/prefixItems 不可）も回避 → [snippets/agent_and_tools.py](snippets/agent_and_tools.py)
- **不変な値オブジェクトとしてのグラフ** — `GraphModel.mutate()` は blocked / extra-edge / `min_throughput` を適用した**新しいグラフを返す**（元は破壊しない）。派生 `cap` は `Node.cap` プロパティで一元計算 → [snippets/graph_model.py](snippets/graph_model.py)
- **規模で解法を切り替える巡回ソルバ** — TSP は `n ≤ 12` はビットマスクDPで厳密解、それ以上は最近傍＋2-opt、大規模は焼きなまし法へ**自動フォールバック** → [snippets/tsp.py](snippets/tsp.py)
- **状態(state)ベースDPの経路復元** — RCSP は `(node, 累積価値)` を状態に持つDPで、閾値を満たす最小時間の状態から親ポインタを辿って経路を復元 → [snippets/rcsp.py](snippets/rcsp.py)
- **結果の形に反応するUI** — `run_sync` の戻りからツール返却値（Pydantic）を取り出し、`edge_flows` / `min_cut` / `path` のどれを持つかで可視化モードを自動判定 → [snippets/streamlit_agent_hook.py](snippets/streamlit_agent_hook.py)

### 担当領域

個人開発。**企画〜データモデル設計〜UI〜LLMエージェント〜8アルゴリズムの実装まで単独**で担当（Python / Streamlit / pydantic-ai / NetworkX）。

---

## Feature deep-dives / 各機能の詳細

各機能ごとに技術的な工夫点をまとめた個別ドキュメントを用意しています（→ [features/](features/README.md)）。

| # | Feature / 機能 | 見どころ / Highlights |
| --- | --- | --- |
| 01 | [LLMによるツール自動選択 / LLM Tool Routing](features/01-llm-tool-routing.md) | pydantic-ai Agent・`RunContext` 依存注入・型付き戻り値・引数モデルでTools API制約を回避 |
| 02 | [数理最適化アルゴリズムの自前実装 / OR Algorithms](features/02-optimization-algorithms.md) | RCSP/CPM/Orienteering の状態DP・TSP規模別解法・最大流のノード分割・最小費用流の network simplex |
| 03 | [横断的な制約適用 / Cross-Cutting Constraints](features/03-cross-cutting-constraints.md) | `min_throughput` フック・`blocked_nodes/edges`・不変な `GraphModel.mutate()` |
| 04 | [対話UIと可視化 / Conversational UI](features/04-conversational-ui.md) | Streamlit マルチターン・`session_state`・描画モード自動切替・agraph 経路/フローハイライト |

## Repository layout / このリポジトリの構成

```
math_optimizer_agent/
├── README.md            # 本書 / this file
├── ARCHITECTURE.md      # 構成図（Mermaid）と設計判断 / diagrams & design decisions
├── TECH_STACK.md        # 技術スタック一覧 / full tech stack table
├── features/            # 各機能の工夫点（個別ドキュメント）/ per-feature deep-dives
│   ├── 01-llm-tool-routing.md
│   ├── 02-optimization-algorithms.md
│   ├── 03-cross-cutting-constraints.md
│   └── 04-conversational-ui.md
└── snippets/            # 匿名の技術デモ用サンプル / anonymized illustrative samples
    ├── agent_and_tools.py       # pydantic-ai Agent + 型付き依存注入 + ツール定義
    ├── graph_model.py           # 不変な GraphModel と mutate() / 派生 cap
    ├── rcsp.py                  # 価値制約付き最短経路の状態DP（骨子）
    ├── tsp.py                   # 規模で解法を切り替える巡回ソルバ（骨子）
    └── streamlit_agent_hook.py  # run_sync + session_state + agraph 描画パターン
```

## Disclaimer / ディスクレーマー

This is the author's own public demo, so there is no employer to anonymize and no production secrets. The snippets under `snippets/` are **simplified illustrations authored for this portfolio** — they convey the design intent but are **not** the full application source, which has been removed from this repository. Any model names, node identifiers, and numbers are **illustrative**. LLM access is configured entirely through environment variables (e.g. `OPENAI_API_KEY`, `OPENAI_MODEL`); no keys appear in this repository.

本プロジェクトは作者自身の公開デモであり、匿名化すべき所属企業や実運用の秘密情報はありません。`snippets/` のコードは**ポートフォリオ用に簡略化して書き起こした説明用サンプル**で、設計意図を伝えるためのものです。アプリの全ソースは本リポジトリから削除しており、掲載コードは実プロダクトそのものではありません。モデル名・ノード識別子・数値はすべて**例示**です。LLM への接続は環境変数（`OPENAI_API_KEY`、`OPENAI_MODEL` 等）のみで設定し、キーはリポジトリに含めていません。
