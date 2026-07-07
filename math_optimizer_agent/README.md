# 製造工程 最適化エージェント

LLM × 数理最適化のデモ。製造工程の DAG に対して、自然言語の依頼から
適切な最適化アルゴリズム（RCSP / Dijkstra / Orienteering / CPM / TSP /
MaxFlow / Bottleneck / MinCostFlow）をエージェントが選び、結果をチャット +
経路ハイライトで返す。

**データモデル:**
- ノード（工場）: `t_proc`（分/個）、`v`（価値/個）、`lanes`（並列ライン数）
  → `cap = lanes × 60 / t_proc`（個/h、派生）
- エッジ（配送路）: `t_move`（分）、`cap`（個/h）

詳しい設計は以下を参照:
- [scenario/scenario.md](scenario/scenario.md) — 概要
- [scenario/demo_manufacturing.md](scenario/demo_manufacturing.md) — シナリオとツール仕様
- [scenario/architecture.md](scenario/architecture.md) — UI / 状態管理 / データフロー

## セットアップ

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# .env を編集して OPENAI_API_KEY を設定（OPENAI_MODEL は任意、既定は gpt-5）
```

## 起動

```bash
streamlit run app/main.py
```

ブラウザで `http://localhost:8501` を開く。

## 画面構成

- 左上: 工程グラフ（streamlit-agraph、経路ハイライト + ノード属性ツールチップ）
- 左下: 最適化結果（使用ツール / 総時間 / 総価値 / 経路）
- 右: チャット（マルチターン継続）
- サイドバー: OpenAI モデル選択（gpt-5 / gpt-5-mini / gpt-5-nano）、会話リセット

## 質問例

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
| `rcsp_tool` + min_throughput | 1 時間に 15 個以上流せる経路で、価値 100 以上を満たし最短で |

## ディレクトリ構成

```
app/
├── main.py            # Streamlit UI
├── state.py           # session_state
├── config.py          # env / モデル設定
├── graph_model.py     # GraphModel
├── graph_view.py      # streamlit-agraph 描画
├── agent_def.py       # pydantic-ai Agent + 5 tools
├── agent_runner.py    # チャット処理 + state 反映
└── algorithms/        # RCSP / Dijkstra / Orienteering / CPM / TSP
data/
└── process_dag.json
```
