"""pydantic-ai Agent + 型付き依存注入 + ツール定義（技術デモ用の匿名サンプル）。

技術デモ用に書き起こした匿名サンプルであり、実運用コードではない
(illustrative demo authored for this portfolio; not production source).

設計意図:
- Agent は「ルーター」。依頼文を読んで 1 ツールを選び引数を埋める役に徹し、
  数値計算はツール内の自作アルゴリズムが決定的に行う。
- グラフ本体は deps（RunContext）で注入。ツールが埋める引数は「依頼から
  読み取る値」だけに絞る。
- ツールの戻り値はすべて Pydantic BaseModel。tuple を含む引数は引数モデルで
  受けて OpenAI Tools API の制約（prefixItems 不可）を回避する。
- モデル ID・API キーは環境変数からのみ注入し、コードに秘密を置かない。
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from graph_model import GraphModel


# ---------- 依存（RunContext で注入するグラフ） ----------

@dataclass
class GraphCtx:
    """ツールが共有する依存。基準グラフを保持する。"""

    store: GraphModel


# ---------- 引数モデル（tuple を Tools API 互換に受けるため） ----------

class BlockedEdge(BaseModel):
    src: str
    dst: str


# ---------- 戻り値モデル（型付きでUIへ渡す） ----------

class RcspResult(BaseModel):
    path: list[str] = Field(description="始点→終点のノード列")
    total_time: float = Field(description="総所要時間 (分)")
    total_value: float = Field(description="経路上で付与される価値の合計")


class PathResult(BaseModel):
    path: list[str]
    total_time: float = Field(description="総所要時間 (分)")


_SYSTEM_PROMPT = (
    "あなたは製造工程の計画担当を支援するエージェントです。\n"
    "グラフは DAG。ノード属性は t_proc(分/個)・v(価値/個)・lanes(並列数)、"
    "派生スループット cap = lanes × 60 / t_proc (個/h)。\n"
    "依頼を読み、登録ツールから最適な 1 つを選んで呼び出してください。\n"
    "- 価値の下限を満たしつつ最短 → rcsp_tool\n"
    "- 価値を気にせず最短時間 → shortest_time_tool\n"
    "- 「cap が X 以上の所だけ通って」等の条件があれば min_throughput=X を渡す。\n"
    "- 情報が足りなければ追加質問を返す。数値には単位を付けて短く要約する。"
)


class SolverBackend:
    """自作アルゴリズムの呼び出し口（デモ用スタブ）。

    実際には RCSP の状態DPや Dijkstra を呼ぶ。ここでは意図のみ示す。
    """

    def rcsp(
        self, graph: GraphModel, source: str, target: str, threshold: float
    ) -> tuple[list[str], float, float]:
        raise NotImplementedError

    def shortest_time(
        self, graph: GraphModel, source: str, target: str
    ) -> tuple[list[str], float]:
        raise NotImplementedError


def build_agent(backend: SolverBackend) -> Agent[GraphCtx, str]:
    """モデル ID を環境変数から取り、ツールを登録した Agent を組み立てる。"""
    model_id = os.getenv("OPENAI_MODEL", "openai-chat")
    agent = Agent[GraphCtx, str](
        model=model_id,
        deps_type=GraphCtx,
        system_prompt=_SYSTEM_PROMPT,
    )

    @agent.tool
    def rcsp_tool(
        ctx: RunContext[GraphCtx],
        source: str,
        target: str,
        value_threshold: float,
        min_throughput: float | None = None,
        blocked_edges: list[BlockedEdge] | None = None,
    ) -> RcspResult:
        """価値制約付き最短経路。Σv ≥ value_threshold を満たす最小総時間の経路。

        min_throughput 指定時は cap 不足のノード/エッジが自動除外される。
        """
        # 制約適用は mutate() に一元化。元グラフは壊さず派生グラフで解く。
        graph = ctx.deps.store.mutate(
            blocked_edges=[(e.src, e.dst) for e in (blocked_edges or [])],
            min_throughput=min_throughput,
        )
        path, total_time, total_value = backend.rcsp(
            graph, source, target, value_threshold
        )
        return RcspResult(path=path, total_time=total_time, total_value=total_value)

    @agent.tool
    def shortest_time_tool(
        ctx: RunContext[GraphCtx],
        source: str,
        target: str,
        min_throughput: float | None = None,
    ) -> PathResult:
        """価値制約を無視した最短時間経路 (Dijkstra)。"""
        graph = ctx.deps.store.mutate(min_throughput=min_throughput)
        path, total_time = backend.shortest_time(graph, source, target)
        return PathResult(path=path, total_time=total_time)

    return agent
