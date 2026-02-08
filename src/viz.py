from __future__ import annotations

from pathlib import Path
from typing import Literal

import networkx as nx


ColorBy = Literal["community", "department", "none"]


def _community_palette() -> list[str]:
    # A small, readable palette (no hard-coded theme assumptions)
    return [
        "#1f77b4",
        "#ff7f0e",
        "#2ca02c",
        "#d62728",
        "#9467bd",
        "#8c564b",
        "#e377c2",
        "#7f7f7f",
        "#bcbd22",
        "#17becf",
    ]


def build_pyvis_html(
    G: nx.Graph,
    *,
    communities: dict[str, int] | None = None,
    highlight_nodes: set[str] | None = None,
    highlight_path: list[str] | None = None,
    color_by: ColorBy = "community",
    height: str = "650px",
    width: str = "100%",
) -> str:
    """Render the graph to an HTML string using PyVis.

    - communities: node->community_id (used if color_by='community')
    - highlight_nodes: nodes to visually emphasize
    - highlight_path: ordered node ids forming a path; edges on this path are emphasized

    Returns HTML string suitable for embedding in Streamlit.
    """
    try:
        from pyvis.network import Network
    except Exception as e:  # pragma: no cover
        raise RuntimeError("PyVis is required for visualization. Install 'pyvis'.") from e

    highlight_nodes = {str(n) for n in (highlight_nodes or set())}
    highlight_edges = set()
    if highlight_path and len(highlight_path) >= 2:
        hp = [str(n) for n in highlight_path]
        for a, b in zip(hp, hp[1:]):
            highlight_edges.add(tuple(sorted((a, b))))

    net = Network(height=height, width=width, bgcolor="#ffffff", font_color="#111111")
    net.barnes_hut()

    palette = _community_palette()

    # Add nodes
    for n, attrs in G.nodes(data=True):
        node_id = str(n)
        label = attrs.get("name", node_id)
        title = f"ID: {node_id}<br>Name: {label}<br>Dept: {attrs.get('department','')}"

        color = None
        if color_by == "community" and communities is not None:
            cid = int(communities.get(node_id, 0))
            color = palette[cid % len(palette)]
        elif color_by == "department":
            # Simple stable hashing to palette
            dept = str(attrs.get("department", ""))
            color = palette[hash(dept) % len(palette)] if dept else palette[0]
        elif color_by == "none":
            color = palette[0]

        size = 18
        if node_id in highlight_nodes:
            size = 28

        net.add_node(node_id, label=label, title=title, color=color, size=size)

    # Add edges
    for u, v, attrs in G.edges(data=True):
        a, b = str(u), str(v)
        w = float(attrs.get("weight", 1))
        value = max(1.0, w)  # thickness in PyVis
        is_path = tuple(sorted((a, b))) in highlight_edges
        net.add_edge(a, b, value=value, title=f"weight: {w}", color="#111111" if is_path else None, width=4 if is_path else None)

    return net.generate_html()
