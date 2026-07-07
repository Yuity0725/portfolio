from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

import streamlit as st

from app.config import DEFAULT_DAG_PATH, DEFAULT_MODEL
from app.graph_model import GraphModel, load_graph


@dataclass
class ChatMessage:
    role: Literal["user", "assistant"]
    content: str


@dataclass
class AppState:
    graph: GraphModel
    model_name: str = DEFAULT_MODEL
    chat_history: list[ChatMessage] = field(default_factory=list)
    agent_messages: list[Any] = field(default_factory=list)
    last_result: dict | None = None
    last_tool_name: str | None = None
    highlighted_path: list[str] = field(default_factory=list)
    highlighted_nodes: list[str] = field(default_factory=list)
    highlighted_edges: list[tuple[str, str]] = field(default_factory=list)
    edge_flows: list[tuple[str, str, float]] = field(default_factory=list)
    pending_prompt: str | None = None

    def reset_conversation(self) -> None:
        self.chat_history.clear()
        self.agent_messages.clear()
        self.last_result = None
        self.last_tool_name = None
        self.highlighted_path = []
        self.highlighted_nodes = []
        self.highlighted_edges = []
        self.edge_flows = []
        self.pending_prompt = None


def get_state() -> AppState:
    if "app_state" not in st.session_state:
        st.session_state.app_state = AppState(graph=load_graph(DEFAULT_DAG_PATH))
    return st.session_state.app_state
