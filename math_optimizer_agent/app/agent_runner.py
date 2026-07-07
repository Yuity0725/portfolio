from __future__ import annotations

from typing import Any

from app.agent_def import GraphCtx, get_agent
from app.state import AppState, ChatMessage


def _extract_tool_return(messages: list[Any]) -> tuple[str | None, dict | None]:
    """Walk messages and return the last (tool_name, content_as_dict)."""
    last: tuple[str | None, dict | None] = (None, None)
    for msg in messages:
        for part in getattr(msg, "parts", []) or []:
            if getattr(part, "part_kind", None) != "tool-return":
                continue
            content = getattr(part, "content", None)
            data: dict | None
            if hasattr(content, "model_dump"):
                data = content.model_dump()
            elif isinstance(content, dict):
                data = content
            else:
                data = None
            last = (getattr(part, "tool_name", None), data)
    return last


def _parse_edge_id(eid: str) -> tuple[str, str] | None:
    if "->" in eid:
        s, d = eid.split("->", 1)
        return s.strip(), d.strip()
    return None


def _extract_visuals(
    data: dict | None,
) -> tuple[
    list[str], list[str], list[tuple[str, str]], list[tuple[str, str, float]]
]:
    """戻り値から (path, nodes, edges, edge_flows) を抽出する。

    - min_cost_flow_tool 等: edge_flows
    - max_flow_tool / bottleneck_tool: highlighted_nodes / highlighted_edges
    - rcsp / tour 等: highlighted_path
    """
    if not data:
        return [], [], [], []

    # 複数ルート（min_cost_flow など）
    ef_raw = data.get("edge_flows")
    if isinstance(ef_raw, list) and ef_raw:
        ef = [
            (str(it["src"]), str(it["dst"]), float(it.get("flow", 0)))
            for it in ef_raw
            if isinstance(it, dict) and "src" in it and "dst" in it
        ]
        if ef:
            return [], [], [], ef

    # bottleneck_tool: items[{kind, id, cap}]
    items = data.get("items")
    if isinstance(items, list) and items and all(
        isinstance(it, dict) and "kind" in it for it in items
    ):
        nodes: list[str] = []
        edges: list[tuple[str, str]] = []
        for it in items:
            if it.get("kind") == "node":
                nodes.append(str(it.get("id")))
            elif it.get("kind") == "edge":
                parsed = _parse_edge_id(str(it.get("id", "")))
                if parsed:
                    edges.append(parsed)
        if nodes or edges:
            return [], nodes, edges, []

    # max_flow_tool: min_cut_nodes / min_cut_edges
    mcn = data.get("min_cut_nodes")
    mce = data.get("min_cut_edges")
    if (isinstance(mcn, list) and mcn) or (isinstance(mce, list) and mce):
        nodes = [str(x) for x in (mcn or [])]
        edges = []
        for e in mce or []:
            if isinstance(e, (list, tuple)) and len(e) >= 2:
                edges.append((str(e[0]), str(e[1])))
        return [], nodes, edges, []

    # 単一経路（rcsp / dijkstra / orienteering / cpm / tour）
    for key in ("path", "tour"):
        if key in data and isinstance(data[key], list):
            return [str(x) for x in data[key]], [], [], []

    return [], [], [], []


def enqueue_user_input(state: AppState, prompt: str) -> None:
    """ユーザー入力を即時履歴に追加し、agent 呼び出しは次の rerun に回す。"""
    state.chat_history.append(ChatMessage(role="user", content=prompt))
    state.pending_prompt = prompt


def process_pending(state: AppState) -> None:
    """pending_prompt があれば agent を呼び出し、assistant メッセージと state を更新する。"""
    prompt = state.pending_prompt
    if not prompt:
        return
    state.pending_prompt = None

    agent = get_agent(state.model_name)
    try:
        result = agent.run_sync(
            prompt,
            message_history=state.agent_messages,
            deps=GraphCtx(store=state.graph),
        )
    except Exception as e:   # noqa: BLE001
        state.chat_history.append(
            ChatMessage(role="assistant", content=f"⚠️ エラー: {type(e).__name__}: {e}")
        )
        return

    state.agent_messages = result.all_messages()
    state.chat_history.append(ChatMessage(role="assistant", content=str(result.output)))

    tool_name, data = _extract_tool_return(state.agent_messages)
    if data is not None:
        state.last_tool_name = tool_name
        state.last_result = data
        path, nodes, edges, ef = _extract_visuals(data)
        state.highlighted_path = path
        state.highlighted_nodes = nodes
        state.highlighted_edges = edges
        state.edge_flows = ef


def handle_user_input(state: AppState, prompt: str) -> None:
    """互換用：一度に enqueue→process まで行う。"""
    enqueue_user_input(state, prompt)
    process_pending(state)
