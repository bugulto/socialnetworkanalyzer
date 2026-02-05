from __future__ import annotations

from typing import Literal

import networkx as nx
import pandas as pd


DistanceMode = Literal["invert", "reciprocal"]


def add_node_attributes(G: nx.Graph, nodes: pd.DataFrame) -> None:
    """Attach node metadata from nodes DataFrame to graph."""
    for _, row in nodes.iterrows():
        node_id = str(row["id"]).strip()
        G.add_node(
            node_id,
            name=str(row.get("name", node_id)).strip(),
            department=str(row.get("department", "")).strip(),
        )


def build_graph(
    nodes: pd.DataFrame,
    edges: pd.DataFrame,
    *,
    weight_col: str = "weight",
    min_weight: int = 1,
    max_weight: int = 5,
    distance_mode: DistanceMode = "invert",
) -> nx.Graph:
    """Build an undirected NetworkX graph.

    Edge attributes:
    - weight: closeness (higher is closer)
    - distance: cost for shortest-path algorithms (lower is closer)

    distance_mode:
    - "invert": distance = (max_weight + 1) - weight
    - "reciprocal": distance = 1 / weight
    """
    G = nx.Graph()

    add_node_attributes(G, nodes)

    for _, row in edges.iterrows():
        u = str(row["source_id"]).strip()
        v = str(row["target_id"]).strip()
        w = int(row[weight_col])

        if distance_mode == "invert":
            dist = (max_weight + 1) - w
        elif distance_mode == "reciprocal":
            dist = 1.0 / float(w)
        else:
            raise ValueError(f"Unsupported distance_mode: {distance_mode}")

        G.add_edge(u, v, weight=w, distance=dist)

    # Convenience: store bounds for later use
    G.graph["min_weight"] = min_weight
    G.graph["max_weight"] = max_weight
    G.graph["distance_mode"] = distance_mode

    return G
