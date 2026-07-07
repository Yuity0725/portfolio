# システムアーキテクチャ — UI 含む全体像

Streamlit + pydantic-ai + NetworkX で構成される、現状実装の完全版アーキテクチャ。
`scenario/architecture.md` の初期設計に対し、throughput/lanes 追加 + 8 ツール構成 +
4 種類の描画モードまで反映した最新版。

<!-- @import "[TOC]" {cmd="toc" depthFrom=1 depthTo=6 orderedList=false} -->

---

## 1. UI レイアウト

```mermaid
flowchart TB
    subgraph App["Streamlit App (layout='wide')"]
        direction LR
        subgraph Side["🔧 Sidebar"]
            ModelSel["OpenAI モデル<br/>(gpt-5 / mini / nano)"]
            Reset["会話リセット"]
            GraphInfo["DAG / ノード数 / エッジ数"]
        end
        subgraph Left["左カラム (cols=[2,1] の 2)"]
            direction TB
            Graph["🗺️ 工程グラフ<br/>streamlit-agraph<br/>(height=460)"]
            Result["📊 最適化結果<br/>(height=240)"]
        end
        subgraph Right["右カラム (1)"]
            Chat["💬 チャット履歴<br/>(scrollable, height=640)"]
            Input["st.chat_input"]
        end
    end
```

実装: [app/main.py:125-150](app/main.py#L125-L150)

---

## 2. システム構成

```mermaid
flowchart LR
    User["👤"]
    subgraph UI["Streamlit UI (app/main.py)"]
        ChatA["💬 Chat"]
        GraphA["🗺️ Graph"]
        ResultA["📊 Result"]
        Sidebar["🔧 Sidebar"]
    end
    State[("🧠 st.session_state<br/>AppState")]
    Runner["⚙️ Agent Runner<br/>(app/agent_runner.py)"]
    Agent["🤖 pydantic-ai Agent<br/>(app/agent_def.py)"]
    Config["📝 Config<br/>(app/config.py, .env)"]
    subgraph Tools["🛠️ 8 Tools (app/algorithms/)"]
        T1["rcsp_tool"]
        T2["shortest_time_tool"]
        T3["max_value_tool"]
        T4["critical_path_tool"]
        T5["tour_tool"]
        T6["max_flow_tool"]
        T7["bottleneck_tool"]
        T8["min_cost_flow_tool"]
    end
    Graph[("🗄️ GraphModel<br/>(DAG: Node/Edge)")]
    Data[("📁 data/process_dag.json")]

    User --> ChatA
    Sidebar --> State
    ChatA --> Runner
    Runner --> Agent
    Config --> Agent
    Agent --> Tools
    Tools <--> Graph
    Data --> Graph
    Tools --> Agent
    Agent --> Runner
    Runner --> State
    State --> ChatA & GraphA & ResultA
```

---

## 3. データモデル

### Node（工場 / 倉庫）
- `id`: 識別子
- `t_proc` (float, 分/個): 1 個あたり処理時間
- `v` (float): 1 個あたり付与価値
- `lanes` (int): 並列ライン数
- `cap` (派生 property, 個/h) = `lanes × 60 / t_proc`
  - `t_proc=0` または `lanes=0` のとき `None`（倉庫扱い、無制限）

### Edge（配送路）
- `src`, `dst`: 端点
- `t_move` (float, 分): 移動時間
- `cap` (float | None, 個/h): 搬送容量

実装: [app/graph_model.py](app/graph_model.py)

---

## 4. アルゴリズム層（8 ツール）

| グループ | ツール | 内部アルゴリズム | 実装 |
|---|---|---|---|
| **単一経路** | `shortest_time_tool` | NetworkX Dijkstra | [shortest_path.py](app/algorithms/shortest_path.py) |
|  | `rcsp_tool` | DAG 上の `(node, value_bucket)` DP | [rcsp.py](app/algorithms/rcsp.py) |
|  | `max_value_tool` | DAG 上の `(node, time_bucket)` DP | [orienteering.py](app/algorithms/orienteering.py) |
|  | `critical_path_tool` | NetworkX `dag_longest_path` | [cpm.py](app/algorithms/cpm.py) |
|  | `tour_tool` | bitmask DP / NN+2-opt / SA (自前実装) | [tsp.py](app/algorithms/tsp.py) |
| **フロー系** | `max_flow_tool` | NetworkX `minimum_cut` + ノード分割 | [max_flow.py](app/algorithms/max_flow.py) |
|  | `bottleneck_tool` | max-flow の最小カット結果を cap 昇順に整列 | [bottleneck.py](app/algorithms/bottleneck.py) |
|  | `min_cost_flow_tool` | NetworkX `network_simplex` + フロー分解 | [min_cost_flow.py](app/algorithms/min_cost_flow.py) |

**共通フック**: 単一経路系すべてに `min_throughput` 引数。`cap < min_throughput` のノード/エッジを
`GraphModel.mutate(min_throughput=...)` で自動 blocked 化（[graph_model.py:79-90](app/graph_model.py#L79-L90)）。

---

## 5. Agent 層（pydantic-ai）

```python
agent = Agent[GraphCtx, str](
    model=f"openai-chat:{model_name}",   # gpt-5 / gpt-5-mini / gpt-5-nano
    deps_type=GraphCtx,
    system_prompt=_SYSTEM_PROMPT,
)
```

- **モデル切替**: サイドバー selectbox → `state.model_name` → `get_agent(model_name)` が
  `_agent_cache: dict[str, Agent]` に積む（[agent_def.py:88](app/agent_def.py#L88)）
- **DI**: `RunContext[GraphCtx]` 経由で各ツールが `ctx.deps.store` (GraphModel) を参照
- **マルチターン**: `agent.run_sync(prompt, message_history=state.agent_messages, deps=...)`
  → `result.all_messages()` を session_state に積み戻す
- **ツール戻り値**: 各ツールは `pydantic.BaseModel` を返す
  （例: `MinCostFlowResult{achieved_flow, total_value, total_cost, avg_time_per_unit, edge_flows, paths}`）

---

## 6. st.session_state（AppState）

| キー | 型 | 役割 |
|---|---|---|
| `graph` | `GraphModel` | DAG 本体（読み込み済み） |
| `model_name` | `str` | 現在の OpenAI モデル名 |
| `chat_history` | `list[ChatMessage]` | UI 描画用の会話履歴 |
| `agent_messages` | `list[ModelMessage]` | pydantic-ai に渡すマルチターン履歴 |
| `last_result` | `dict \| None` | 最後のツール戻り値（`model_dump()` 済み） |
| `last_tool_name` | `str \| None` | 最後に呼ばれたツール名 |
| `highlighted_path` | `list[str]` | 単一経路系の path |
| `highlighted_nodes` | `list[str]` | 警告強調するノード（min cut 等） |
| `highlighted_edges` | `list[tuple[str,str]]` | 警告強調するエッジ |
| `edge_flows` | `list[tuple[str,str,float]]` | min_cost_flow の流量結果 |
| `pending_prompt` | `str \| None` | rerun 待ちの未処理依頼 |

実装: [app/state.py](app/state.py)

---

## 7. 1 ターンのデータフロー

```mermaid
sequenceDiagram
    autonumber
    actor U as 👤
    participant UI as Streamlit
    participant ST as session_state (AppState)
    participant R as agent_runner
    participant A as pydantic-ai Agent
    participant T as Tool
    participant G as GraphModel

    U->>UI: st.chat_input
    UI->>R: enqueue_user_input(prompt)
    R->>ST: chat_history += user / pending_prompt=prompt
    UI->>UI: st.rerun()  ← user 発話を即時表示

    Note over UI,ST: 次の rerun で pending を検知
    UI->>UI: render_chat 内で<br/>st.chat_message("assistant") + spinner
    UI->>R: process_pending(state)
    R->>A: agent.run_sync(prompt, message_history, deps=GraphCtx)
    A->>T: 引数抽出 → ツール呼び出し
    T->>G: 必要なら mutate(min_throughput=, blocked_*=)
    T-->>A: BaseModel
    A-->>R: AgentRunResult
    R->>ST: agent_messages 更新<br/>chat_history += assistant<br/>highlighted_* / edge_flows 更新
    UI->>UI: st.rerun()  ← 結果描画
    ST-->>UI: 3 エリア（graph / result / chat）再描画
```

実装: [app/agent_runner.py](app/agent_runner.py)

---

## 8. 描画モード（4 種、自動切替）

`agent_runner._extract_visuals(data)` が戻り値の形を見て **どの session_state を埋めるか** を決め、
`graph_view.render_graph` がその state を見て **どのモードで描くか** を分岐する。

```mermaid
flowchart TD
    R["ツール戻り値 dict"] --> C{"含まれるキーは？"}
    C -- "edge_flows + paths" --> M1["**流量モード**<br/>min_cost_flow_tool<br/>→ エッジ太さで流量、複数ルート"]
    C -- "min_cut_nodes / min_cut_edges" --> M2["**警告モード**<br/>max_flow_tool<br/>→ オレンジ + 点線でカット強調"]
    C -- "items[{kind, id, cap}]" --> M3["**警告モード**<br/>bottleneck_tool<br/>→ 同上、cap 昇順でリスト"]
    C -- "path / tour" --> M4["**経路モード**<br/>rcsp/dijkstra/orienteering/cpm/tour<br/>→ 赤太線 + tour は青で逆走/中継"]
```

結果パネル（`render_result`）も同じ 4 モードに分岐。
- 流量: 生産個数 / 価値 / 人時 / 1個平均 + 経路ごとの個数と価値
- 最大流: 最大流量 + ボトルネック工場・区間リスト
- ボトルネック: 増強優先順リスト
- 単一経路: 総時間 / 総価値 / 経路長 + 経路

実装: [agent_runner.py:_extract_visuals](app/agent_runner.py)、[graph_view.py:render_graph](app/graph_view.py)、[main.py:render_result](app/main.py#L39)

---

## 9. ファイル構成

```
app/
├── main.py              # ページレイアウト + チャットループ
├── state.py             # AppState / session_state
├── config.py            # .env / OPENAI_MODEL / AVAILABLE_MODELS
├── graph_model.py       # Node (lanes 派生 cap) / Edge / GraphModel
├── graph_view.py        # streamlit-agraph 描画 (4 モード)
├── agent_def.py         # pydantic-ai Agent + 8 tool 登録 + system_prompt
├── agent_runner.py      # enqueue / process_pending / 戻り値抽出
└── algorithms/          # rcsp / shortest_path / orienteering /
                         # cpm / tsp / max_flow / bottleneck / min_cost_flow
data/
└── process_dag.json     # サンプル DAG (12 ノード, 23 エッジ)
scenario/
├── scenario.md                  # 概要
├── demo_manufacturing.md        # シナリオ詳細とツール仕様
├── architecture.md              # 初期設計（旧）
├── system_architecture.md       # 本ファイル — 最新の全体像
└── industry_applications.md     # 産業応用の整理
```

---

## 10. 拡張ポイント

| 拡張 | 主な変更箇所 |
|---|---|
| 新ツール追加 | `app/algorithms/<new>.py` 作成 → `app/algorithms/__init__.py` で export → `app/agent_def.py` に `@agent.tool` 登録 + `system_prompt` 更新 |
| 新業界へ移植 | `data/<domain>_graph.json` 用意 → `system_prompt` の語彙を差し替え |
| 新しい描画モード | `state.py` に新フィールド → `agent_runner._extract_visuals` で抽出 → `graph_view.render_graph` で分岐追加 |
| 別 LLM プロバイダ | `app/config.py` の `AVAILABLE_MODELS` + `agent_def.get_agent` の model 文字列を変更（pydantic-ai が anthropic/google など多数サポート） |
| ストリーミング応答 | `agent.iter()` / `agent.run_stream()` に切替 + `process_pending` を async 化 |
