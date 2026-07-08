"""run_sync + session_state + agraph 描画パターン（技術デモ用の匿名サンプル）。

技術デモ用に書き起こした匿名サンプルであり、実運用コードではない
(illustrative demo authored for this portfolio; not production source).

設計意図:
- 会話とグラフ状態を 1 つの AppState に集約し、Streamlit の session_state に保持。
- run_sync に message_history を渡してマルチターンを継続する。
- ツール戻り値（Pydantic → dict）の「形」で描画モードを自動判定する。
  edge_flows があればフロー、min_cut/items があれば警告、path/tour があれば経路。
- streamlit / pydantic-ai の import はデモ用に省略（呼び出し形だけ示す）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal


@dataclass
class ChatMessage:
    role: Literal["user", "assistant"]
    content: str


@dataclass
class AppState:
    """会話・グラフ・可視化対象をまとめて session_state に載せる状態。"""

    graph: Any  # GraphModel（基準グラフ。mutate の元として不変に保つ）
    chat_history: list[ChatMessage] = field(default_factory=list)
    agent_messages: list[Any] = field(default_factory=list)  # pydantic-ai 履歴
    last_result: dict | None = None
    highlighted_path: list[str] = field(default_factory=list)
    highlighted_nodes: list[str] = field(default_factory=list)
    edge_flows: list[tuple[str, str, float]] = field(default_factory=list)
    pending_prompt: str | None = None

    def reset(self) -> None:
        self.chat_history.clear()
        self.agent_messages.clear()
        self.last_result = None
        self.highlighted_path = []
        self.highlighted_nodes = []
        self.edge_flows = []
        self.pending_prompt = None


class RenderMode(str, Enum):
    """ツール結果の形から決まる描画モード。"""

    FLOW = "flow"        # 複数ルート: edge_flows を太さで表現
    WARNING = "warning"  # ボトルネック: min_cut / items を警告色で強調
    ROUTE = "route"      # 単一経路: path / tour をハイライト


class AgentRunner:
    """1 ターンの処理（agent 呼び出し → 状態反映）を担うフック。"""

    def __init__(self, agent: Any, deps_factory: Any) -> None:
        self._agent = agent
        self._deps_factory = deps_factory  # graph -> GraphCtx

    def enqueue(self, state: AppState, prompt: str) -> None:
        """入力を即履歴へ積み、実処理は次の rerun に回す。"""
        state.chat_history.append(ChatMessage("user", prompt))
        state.pending_prompt = prompt

    def process_pending(self, state: AppState) -> None:
        """pending があれば agent を呼び、結果を state へ反映する。"""
        prompt = state.pending_prompt
        if not prompt:
            return
        state.pending_prompt = None

        # message_history を渡してマルチターンを継続
        result = self._agent.run_sync(
            prompt,
            message_history=state.agent_messages,
            deps=self._deps_factory(state.graph),
        )
        state.agent_messages = result.all_messages()
        state.chat_history.append(ChatMessage("assistant", str(result.output)))

        data = self._extract_tool_return(state.agent_messages)
        if data is not None:
            state.last_result = data
            self._apply_visuals(state, data)

    @staticmethod
    def _extract_tool_return(messages: list[Any]) -> dict | None:
        """最後の tool-return を dict 化して取り出す（Pydantic → dict）。"""
        found: dict | None = None
        for msg in messages:
            for part in getattr(msg, "parts", []) or []:
                if getattr(part, "part_kind", None) != "tool-return":
                    continue
                content = getattr(part, "content", None)
                if hasattr(content, "model_dump"):
                    found = content.model_dump()
                elif isinstance(content, dict):
                    found = content
        return found

    @classmethod
    def _apply_visuals(cls, state: AppState, data: dict) -> None:
        """結果の形で描画モードを判定し、ハイライト対象を state に設定。"""
        # まず全ハイライトをクリア
        state.highlighted_path, state.highlighted_nodes, state.edge_flows = [], [], []

        mode = cls.classify(data)
        if mode is RenderMode.FLOW:
            state.edge_flows = [
                (str(it["src"]), str(it["dst"]), float(it["flow"]))
                for it in data["edge_flows"]
            ]
        elif mode is RenderMode.WARNING:
            state.highlighted_nodes = [str(x) for x in data.get("min_cut_nodes", [])]
        else:  # ROUTE
            state.highlighted_path = [str(x) for x in (data.get("path") or data.get("tour") or [])]

    @staticmethod
    def classify(data: dict) -> RenderMode:
        """ツール結果の鍵を見て描画モードを決める（1 箇所に集約）。"""
        if data.get("edge_flows"):
            return RenderMode.FLOW
        if data.get("min_cut_nodes") or data.get("min_cut_edges") or data.get("items"):
            return RenderMode.WARNING
        return RenderMode.ROUTE
