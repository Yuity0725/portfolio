from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from app.algorithms import (
    bottleneck,
    critical_path,
    decompose_flow,
    dijkstra_path,
    max_flow,
    min_cost_flow,
    orienteering_dp,
    rcsp_dp,
    tour as tsp_tour,
)
from app.graph_model import GraphModel


@dataclass
class GraphCtx:
    store: GraphModel


_SYSTEM_PROMPT = (
    "あなたは製造工程の計画担当者を支援するエージェントです。\n"
    "グラフは DAG（始点 S、終点 G は倉庫で容量は無制限）。\n"
    "ノード（工場）の属性: "
    "t_proc (分/個)、v (価値/個)、lanes (並列ライン数)。"
    "派生スループット cap = lanes × 60 / t_proc (個/h)。\n"
    "エッジ（配送路）の属性: t_move (分)、cap (個/h)。\n"
    "ユーザーの依頼を読み取り、登録されたツールから最適な 1 つを選んで呼び出してください。\n"
    "- 始点・終点が指定されないときは、それぞれ S, G を使ってください。\n"
    "- 「ピーク時に何個流せる？」「最大スループットは？」→ max_flow_tool\n"
    "- 「どこが詰まっている？」「どの工場/区間を増強すべき？」→ bottleneck_tool\n"
    "- 「○○個流したい／○○個を最小コストで」→ min_cost_flow_tool（demand を渡す）\n"
    "- 単一経路系（最短時間／価値制約／時間予算／クリティカル／巡回）の依頼で"
    "「1時間に X 個以上流せる経路で」「cap が X 以上の所だけ通って」のような throughput 条件があれば、"
    "対応ツールに `min_throughput=X` を渡してください（cap < X のノード/エッジは自動で除外）。\n"
    "- 「全工場」「全ノード」など範囲が明示されない巡回依頼では tour_tool の node_set を渡さないこと。\n"
    "- 情報が足りないときは、追加質問を返してください。\n"
    "- 結果は短く現場の言葉で要約してください。"
    "数値には単位（個/h、分、分/個）を付けてください。"
)


# ---------- Argument models（OpenAI Tools API が tuple/prefixItems を扱えないため BaseModel 化）----------

class BlockedEdge(BaseModel):
    src: str
    dst: str


class ExtraEdge(BaseModel):
    src: str
    dst: str
    t_move: float


def _be(items: list[BlockedEdge] | None) -> list[tuple[str, str]]:
    return [(e.src, e.dst) for e in (items or [])]


def _ee(items: list[ExtraEdge] | None) -> list[tuple[str, str, float]]:
    return [(e.src, e.dst, e.t_move) for e in (items or [])]


# ---------- Result models ----------

class RcspResult(BaseModel):
    path: list[str] = Field(description="始点→終点のノード列")
    total_time: float
    total_value: float


class PathResult(BaseModel):
    path: list[str]
    total_time: float


class ValueResult(BaseModel):
    path: list[str]
    total_value: float
    total_time: float


class CpmResult(BaseModel):
    path: list[str]
    total_time: float


class TourResult(BaseModel):
    tour: list[str]
    total_time: float


class MaxFlowResult(BaseModel):
    max_flow: float = Field(description="単位時間あたりの最大流量")
    min_cut_nodes: list[str] = Field(description="最小カットに含まれる工場（ボトルネック）")
    min_cut_edges: list[tuple[str, str]] = Field(description="最小カットに含まれる配送路")


class BottleneckItem(BaseModel):
    kind: Literal["node", "edge"]
    id: str
    cap: float


class BottleneckResult(BaseModel):
    items: list[BottleneckItem]


class EdgeFlow(BaseModel):
    src: str
    dst: str
    flow: float


class PathFlow(BaseModel):
    path: list[str]
    flow: float = Field(description="このルートを流れる個数 (個/h)")
    total_value: float = Field(description="このルートで完成する全製品の価値 = Σ v on path × flow")


class MinCostFlowResult(BaseModel):
    achieved_flow: float = Field(description="単位時間に流せた個数の合計 (個/h)")
    total_value: float = Field(description="全パスを通過する単位の付与価値の総計")
    total_cost: float = Field(description="人時総計 = Σ flow × (t_proc + t_move) (分)")
    avg_time_per_unit: float = Field(
        description="1 個あたりの平均所要時間 = total_cost / achieved_flow (分/個)"
    )
    edge_flows: list[EdgeFlow]
    paths: list[PathFlow] = Field(description="フロー分解した経路ごとの (path, flow)")


# ---------- Agent factory (model-scoped) ----------

_agent_cache: dict[str, Agent[GraphCtx, str]] = {}


def get_agent(model_name: str) -> Agent[GraphCtx, str]:
    if model_name in _agent_cache:
        return _agent_cache[model_name]

    agent = Agent[GraphCtx, str](
        model=f"openai-chat:{model_name}",
        deps_type=GraphCtx,
        system_prompt=_SYSTEM_PROMPT,
    )

    # ----- 単一経路系（cap 制約は min_throughput で受ける） -----

    @agent.tool
    def rcsp_tool(
        ctx: RunContext[GraphCtx],
        source: str,
        target: str,
        value_threshold: float,
        min_throughput: float | None = None,
        blocked_nodes: list[str] | None = None,
        blocked_edges: list[BlockedEdge] | None = None,
        extra_edges: list[ExtraEdge] | None = None,
    ) -> RcspResult:
        """価値制約付き最短経路。Σv ≥ value_threshold を満たす最小総時間の経路を返す。

        min_throughput が指定されれば、cap が満たないノード/エッジは経路から除外される。
        """
        g = ctx.deps.store.mutate(
            blocked_nodes, _be(blocked_edges), _ee(extra_edges), min_throughput
        )
        path, t, v = rcsp_dp(g, source, target, value_threshold)
        return RcspResult(path=path, total_time=t, total_value=v)

    @agent.tool
    def shortest_time_tool(
        ctx: RunContext[GraphCtx],
        source: str,
        target: str,
        min_throughput: float | None = None,
        blocked_nodes: list[str] | None = None,
        blocked_edges: list[BlockedEdge] | None = None,
    ) -> PathResult:
        """価値制約を無視した最短時間経路 (Dijkstra)。"""
        g = ctx.deps.store.mutate(
            blocked_nodes, _be(blocked_edges), None, min_throughput
        )
        path, t = dijkstra_path(g, source, target)
        return PathResult(path=path, total_time=t)

    @agent.tool
    def max_value_tool(
        ctx: RunContext[GraphCtx],
        source: str,
        target: str,
        time_budget: float,
        min_throughput: float | None = None,
        blocked_nodes: list[str] | None = None,
        blocked_edges: list[BlockedEdge] | None = None,
    ) -> ValueResult:
        """総時間 ≤ time_budget を満たす最大価値経路 (Orienteering on DAG)。"""
        g = ctx.deps.store.mutate(
            blocked_nodes, _be(blocked_edges), None, min_throughput
        )
        path, v, t = orienteering_dp(g, source, target, time_budget)
        return ValueResult(path=path, total_value=v, total_time=t)

    @agent.tool
    def critical_path_tool(
        ctx: RunContext[GraphCtx],
        source: str,
        target: str,
        min_throughput: float | None = None,
    ) -> CpmResult:
        """DAG の最長パス (CPM)。全工程を経た場合の完成時間下限。"""
        g = ctx.deps.store.mutate(min_throughput=min_throughput)
        path, t = critical_path(g, source, target)
        return CpmResult(path=path, total_time=t)

    @agent.tool
    def tour_tool(
        ctx: RunContext[GraphCtx],
        start_node: str = "S",
        node_set: list[str] | None = None,
        method: Literal["exact", "2opt", "sa", "auto"] = "auto",
        min_throughput: float | None = None,
    ) -> TourResult:
        """視察モード: 指定ノードを 1 回ずつ巡回する最短ルート (DAG 制約を緩和)。

        node_set が None または空のときはグラフ全ノードを対象。
        min_throughput を指定すると cap 不足ノード/エッジは自動除外される。
        """
        store = ctx.deps.store.mutate(min_throughput=min_throughput)
        if not node_set:
            node_set = [n.id for n in store.nodes]
        t, c = tsp_tour(store, node_set, start_node, method=method)
        return TourResult(tour=t, total_time=c)

    # ----- スループット系（新規 3 ツール） -----

    @agent.tool
    def max_flow_tool(
        ctx: RunContext[GraphCtx],
        source: str = "S",
        sink: str = "G",
    ) -> MaxFlowResult:
        """ピーク時に source→sink へ流せる単位時間あたりの最大量と、ボトルネック区間を返す。"""
        flow, edges, nodes = max_flow(ctx.deps.store, source, sink)
        return MaxFlowResult(max_flow=flow, min_cut_edges=edges, min_cut_nodes=nodes)

    @agent.tool
    def bottleneck_tool(
        ctx: RunContext[GraphCtx],
        source: str = "S",
        sink: str = "G",
        top_k: int = 3,
    ) -> BottleneckResult:
        """source→sink で最大流を阻害するボトルネック要素を増強優先順に top_k 件返す。"""
        items = bottleneck(ctx.deps.store, source, sink, top_k=top_k)
        return BottleneckResult(items=[BottleneckItem(**it) for it in items])

    @agent.tool
    def min_cost_flow_tool(
        ctx: RunContext[GraphCtx],
        demand: float,
        source: str = "S",
        sink: str = "G",
    ) -> MinCostFlowResult:
        """目標流量 demand を最小総コストで流す計画。容量不足なら最大可能量で切り詰める。

        戻り値には流量分解されたパスと、各パスの単位当たり付与価値の合計
        （total_value）も含まれる。"""
        achieved, cost, ef = min_cost_flow(ctx.deps.store, source, sink, demand)
        decomp = decompose_flow(ef, source, sink)

        by_id = {n.id: n for n in ctx.deps.store.nodes}
        path_models: list[PathFlow] = []
        total_value = 0.0
        for p, f in decomp:
            v_sum = sum(by_id[n].v for n in p if n in by_id)
            path_value = v_sum * f
            total_value += path_value
            path_models.append(PathFlow(path=p, flow=f, total_value=path_value))

        avg = float(cost) / float(achieved) if achieved else 0.0
        return MinCostFlowResult(
            achieved_flow=achieved,
            total_value=float(total_value),
            total_cost=cost,
            avg_time_per_unit=avg,
            edge_flows=[EdgeFlow(src=s, dst=d, flow=f) for s, d, f in ef],
            paths=path_models,
        )

    _agent_cache[model_name] = agent
    return agent
