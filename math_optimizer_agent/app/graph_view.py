from __future__ import annotations

import networkx as nx
from streamlit_agraph import Config, Edge, Node, agraph

from app.graph_model import GraphModel

HIGHLIGHT_FWD = "#ff6b6b"   # 解の経路（DAG エッジに沿う）
HIGHLIGHT_REV = "#3b82f6"   # 巡回の逆走（DAG を逆向きに辿る／中継）
WARNING_COLOR = "#f59e0b"   # ボトルネック / 最小カット警告
BASE_NODE = "#9aa5b1"
BASE_EDGE = "#cbd2d9"

WAREHOUSE_EMOJI = "🏬"
FACTORY_EMOJI = "🏭"


def _warehouse_ids(graph: GraphModel) -> set[str]:
    """DAG の source（入次数 0）と sink（出次数 0）を倉庫として扱う。"""
    in_deg = {n.id: 0 for n in graph.nodes}
    out_deg = {n.id: 0 for n in graph.nodes}
    for e in graph.edges:
        out_deg[e.src] += 1
        in_deg[e.dst] += 1
    return {nid for nid in in_deg if in_deg[nid] == 0 or out_deg[nid] == 0}


def _compute_levels(graph: GraphModel) -> dict[str, int]:
    """Longest-path depth from any source node — vis.js hierarchical layout uses this."""
    g = nx.DiGraph()
    g.add_nodes_from(n.id for n in graph.nodes)
    g.add_edges_from((e.src, e.dst) for e in graph.edges)
    levels: dict[str, int] = {}
    for n in nx.topological_sort(g):
        preds = list(g.predecessors(n))
        levels[n] = 0 if not preds else max(levels[p] for p in preds) + 1
    return levels


def _classify_tour_edges(
    graph: GraphModel, path: list[str]
) -> tuple[set[tuple[str, str]], list[tuple[str, str, str]]]:
    """path の連続ペアを「DAG 順方向」「それ以外（逆走 / 中継）」に分類する。

    Returns:
        fwd: DAG エッジ集合のうち順方向で辿る集合（既存エッジを赤太線にする対象）
        extras: (u, v, kind) のリスト。kind は "reverse" or "shortcut"
                これらは追加 Edge として青矢印で描く。
    """
    dag = {(e.src, e.dst) for e in graph.edges}
    fwd: set[tuple[str, str]] = set()
    extras: list[tuple[str, str, str]] = []
    for u, v in zip(path, path[1:]):
        if (u, v) in dag:
            fwd.add((u, v))
        elif (v, u) in dag:
            extras.append((u, v, "reverse"))
        else:
            extras.append((u, v, "shortcut"))
    return fwd, extras


def _flow_width(flow: float, max_flow: float, base: int = 2, scale: int = 8) -> int:
    if max_flow <= 0:
        return base
    return int(round(base + (flow / max_flow) * scale))


def render_graph(
    graph: GraphModel,
    highlighted_path: list[str],
    edge_flows: list[tuple[str, str, float]] | None = None,
    highlighted_nodes: list[str] | None = None,
    highlighted_edges: list[tuple[str, str]] | None = None,
) -> None:
    levels = _compute_levels(graph)
    warehouses = _warehouse_ids(graph)

    # 描画モード判定:
    # 1) edge_flows あり → 流量モード（複数ルート、太さで濃淡）
    # 2) highlighted_nodes / highlighted_edges あり → 警告モード（min cut / bottleneck）
    # 3) それ以外 → 単一経路モード（path + 逆走/中継）
    use_flow_mode = bool(edge_flows)
    warn_nodes = set(highlighted_nodes or [])
    warn_edges = set(highlighted_edges or [])
    use_warn_mode = (not use_flow_mode) and bool(warn_nodes or warn_edges)

    flow_map: dict[tuple[str, str], float] = {}
    if use_flow_mode:
        for s, d, f in edge_flows or []:
            flow_map[(s, d)] = flow_map.get((s, d), 0.0) + float(f)
        max_flow_val = max(flow_map.values()) if flow_map else 1.0
        hl_nodes = {n for pair in flow_map.keys() for n in pair}
        fwd_set: set[tuple[str, str]] = set()
        extras: list[tuple[str, str, str]] = []
    elif use_warn_mode:
        hl_nodes = set()
        fwd_set = set()
        extras = []
        max_flow_val = 1.0
    else:
        hl_nodes = set(highlighted_path)
        fwd_set, extras = _classify_tour_edges(graph, highlighted_path)
        max_flow_val = 1.0

    nodes = []
    for n in graph.nodes:
        is_warehouse = n.id in warehouses
        icon = WAREHOUSE_EMOJI if is_warehouse else FACTORY_EMOJI
        kind = "倉庫" if is_warehouse else "工場"
        cap_str = "∞" if n.cap is None else f"{n.cap:.1f}"
        if is_warehouse:
            tooltip = f"{kind} {n.id}\ncap=∞ (個/h)"
        else:
            tooltip = (
                f"{kind} {n.id}\n"
                f"t_proc={n.t_proc:g} 分/個\n"
                f"lanes={n.lanes}\n"
                f"cap={cap_str} 個/h\n"
                f"v={n.v:g} /個"
            )
        if use_warn_mode and n.id in warn_nodes:
            n_color = WARNING_COLOR
            n_size = 34
            n_label = f"⚠️ {icon} {n.id}"
        elif n.id in hl_nodes:
            n_color = HIGHLIGHT_FWD
            n_size = 32
            n_label = f"{icon} {n.id}"
        else:
            n_color = BASE_NODE
            n_size = 24
            n_label = f"{icon} {n.id}"
        nodes.append(
            Node(
                id=n.id,
                label=n_label,
                title=tooltip,
                color=n_color,
                size=n_size,
                level=levels[n.id],
                shape="box" if is_warehouse else "ellipse",
                font={"size": 16, "color": "#1f2937"},
            )
        )

    edges = []
    for e in graph.edges:
        cap_str = "∞" if e.cap is None else f"{e.cap:g}"
        flow = flow_map.get((e.src, e.dst))
        dashes = False
        if use_flow_mode:
            on_path = flow is not None and flow > 0
            width = _flow_width(flow or 0.0, max_flow_val) if on_path else 1
            label = (
                f"t={e.t_move:g}分 / c={cap_str}個/h / f={flow:g}個/h"
                if on_path else f"t={e.t_move:g}分 / c={cap_str}個/h"
            )
            color = HIGHLIGHT_FWD if on_path else BASE_EDGE
        elif use_warn_mode:
            is_warn = (e.src, e.dst) in warn_edges
            is_to_warn_node = e.src in warn_nodes or e.dst in warn_nodes
            on_path = is_warn or is_to_warn_node
            color = WARNING_COLOR if is_warn else (
                BASE_EDGE if not is_to_warn_node else WARNING_COLOR
            )
            width = 5 if is_warn else (3 if is_to_warn_node else 1)
            dashes = is_warn
            label = (
                f"⚠️ t={e.t_move:g}分 / c={cap_str}個/h"
                if is_warn else f"t={e.t_move:g}分 / c={cap_str}個/h"
            )
        else:
            on_path = (e.src, e.dst) in fwd_set
            width = 4 if on_path else 1
            label = f"t={e.t_move:g}分 / c={cap_str}個/h"
            color = HIGHLIGHT_FWD if on_path else BASE_EDGE
        edges.append(
            Edge(
                source=e.src,
                target=e.dst,
                label=label,
                title=f"{e.src} → {e.dst}\nt_move={e.t_move:g} 分\ncap={cap_str} 個/h"
                + (f"\nflow={flow:g} 個/h" if flow else ""),
                color=color,
                width=width,
                dashes=dashes,
            )
        )

    # 逆走 / 中継（巡回モードのみ）: 巡回方向 (u → v) で青矢印を追加描画。
    for u, v, kind in extras:
        edges.append(
            Edge(
                source=u,
                target=v,
                label="逆走" if kind == "reverse" else "中継",
                color=HIGHLIGHT_REV,
                width=3,
                dashes=(kind == "shortcut"),
                smooth={"type": "curvedCCW", "roundness": 0.3},
            )
        )

    config = Config(
        width=700,
        height=420,
        directed=True,
        hierarchical=True,
        physics=False,
        nodeHighlightBehavior=True,
        direction="LR",
        sortMethod="directed",
        levelSeparation=120,
        nodeSpacing=70,
    )
    agraph(nodes=nodes, edges=edges, config=config)
