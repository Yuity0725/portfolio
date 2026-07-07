from __future__ import annotations

import sys
from pathlib import Path

# `streamlit run app/main.py` だとリポジトリルートが sys.path に入らないので明示的に追加
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st  # noqa: E402

from app.agent_runner import enqueue_user_input, process_pending  # noqa: E402
from app.config import AVAILABLE_MODELS, DEFAULT_MODEL  # noqa: E402
from app.graph_view import render_graph  # noqa: E402
from app.state import get_state  # noqa: E402

st.set_page_config(layout="wide", page_title="製造工程 最適化エージェント")


def render_sidebar(state) -> None:
    with st.sidebar:
        st.header("⚙️ 設定")
        idx = AVAILABLE_MODELS.index(state.model_name) if state.model_name in AVAILABLE_MODELS else 0
        chosen = st.selectbox("OpenAI モデル", AVAILABLE_MODELS, index=idx)
        if chosen != state.model_name:
            state.model_name = chosen

        if st.button("🗑️ 会話リセット", use_container_width=True):
            state.reset_conversation()
            st.rerun()

        st.divider()
        st.caption(f"DAG: `{state.graph.source_path}`")
        st.caption(f"ノード数: {len(state.graph.nodes)} / エッジ数: {len(state.graph.edges)}")
        st.caption(f"デフォルトモデル: `{DEFAULT_MODEL}`")


def render_result(state) -> None:
    if state.last_result is None:
        st.caption("まだ最適化は実行されていません。右側のチャットから依頼してください。")
        return

    tool = state.last_tool_name or "tool"
    st.markdown(f"**使用ツール:** `{tool}`")

    data = state.last_result

    # --- 1. 複数ルート（min_cost_flow） ---
    paths = data.get("paths")
    if isinstance(paths, list) and paths:
        cols = st.columns(4)
        cols[0].metric("生産個数 合計", f"{_fmt_num(data.get('achieved_flow'))} 個/h")
        cols[1].metric("価値 総計", _fmt_num(data.get("total_value")))
        cols[2].metric("人時 総計", f"{_fmt_num(data.get('total_cost'))} 分")
        cols[3].metric("1 個 平均", f"{_fmt_num(data.get('avg_time_per_unit'))} 分/個")

        st.markdown("**経路ごとの生産個数と完成品価値:**")
        for p in paths:
            path_str = " → ".join(p.get("path", []))
            flow_str = _fmt_num(p.get("flow"))
            value_str = _fmt_num(p.get("total_value"))
            st.write(f"- {path_str} : **{flow_str} 個/h** / 価値 **{value_str}**")
        return

    # --- 2. 最大流（max_flow） ---
    if "max_flow" in data and ("min_cut_nodes" in data or "min_cut_edges" in data):
        cols = st.columns(3)
        cols[0].metric("最大流量", f"{_fmt_num(data.get('max_flow'))} 個/h")
        cols[1].metric("詰まっている工場", len(data.get("min_cut_nodes") or []))
        cols[2].metric("詰まっている区間", len(data.get("min_cut_edges") or []))

        if data.get("min_cut_nodes"):
            st.write("**ボトルネック工場:** " + ", ".join(data["min_cut_nodes"]))
        if data.get("min_cut_edges"):
            mce = data["min_cut_edges"]
            es = ", ".join(f"{e[0]}→{e[1]}" for e in mce if len(e) >= 2)
            st.write("**ボトルネック区間:** " + es)
        return

    # --- 3. ボトルネック優先順（bottleneck） ---
    items = data.get("items")
    if isinstance(items, list) and items and all(
        isinstance(it, dict) and "kind" in it for it in items
    ):
        st.markdown("**増強優先順（cap 昇順）:**")
        for it in items:
            cap = it.get("cap")
            cap_str = "∞" if cap == float("inf") else _fmt_num(cap)
            kind_jp = "工場" if it.get("kind") == "node" else "区間"
            st.write(f"- {kind_jp} `{it.get('id')}` — cap = **{cap_str} 個/h**")
        return

    # --- 4. 単一経路（rcsp / dijkstra / orienteering / cpm / tour） ---
    cols = st.columns(3)
    cols[0].metric("総時間", f"{_fmt_num(data.get('total_time'))} 分")
    cols[1].metric("総価値", _fmt_num(data.get("total_value")))
    seq = data.get("path") or data.get("tour") or []
    cols[2].metric("経路長", f"{len(seq)} ノード")

    if seq:
        st.write("**経路:** " + " → ".join(str(x) for x in seq))


def _fmt_num(x) -> str:
    if x is None:
        return "-"
    if isinstance(x, float):
        return f"{x:.1f}"
    return str(x)


def render_chat(state) -> None:
    with st.container(height=640, border=True):
        for msg in state.chat_history:
            with st.chat_message(msg.role):
                st.markdown(msg.content)
        if state.pending_prompt:
            with st.chat_message("assistant"):
                with st.spinner("考え中..."):
                    process_pending(state)
            st.rerun()


def main() -> None:
    state = get_state()
    render_sidebar(state)

    left, right = st.columns([2, 1])

    with left:
        st.markdown("### 🗺️ 工程グラフ")
        with st.container(height=460, border=True):
            render_graph(
                state.graph,
                state.highlighted_path,
                state.edge_flows,
                state.highlighted_nodes,
                state.highlighted_edges,
            )
        st.markdown("### 📊 最適化結果")
        with st.container(height=240, border=True):
            render_result(state)

    with right:
        st.markdown("### 💬 チャット")
        render_chat(state)
        if prompt := st.chat_input("依頼を入力（例: 価値 100 以上で S から G まで最短で）"):
            enqueue_user_input(state, prompt)
            st.rerun()


if __name__ == "__main__":
    main()
