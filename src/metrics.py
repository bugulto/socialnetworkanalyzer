from __future__ import annotations

from typing import Any

import networkx as nx
import pandas as pd


def compute_node_metrics(G: nx.Graph, *, distance_attr: str = "distance") -> pd.DataFrame:
    """Compute per-node metrics.

    Returns a DataFrame indexed by node id with columns:
    - degree
    - strength (sum of edge weights)
    - degree_centrality
    - closeness_centrality (weighted by distance_attr if present)
    - betweenness_centrality (weighted by distance_attr if present)
    - clustering_coefficient
    """
    nodes = list(G.nodes())

    degree = dict(G.degree())
    strength = {n: 0.0 for n in nodes}
    for u, v, data in G.edges(data=True):
        w = float(data.get("weight", 1.0))
        strength[u] += w
        strength[v] += w

    degree_c = nx.degree_centrality(G) if G.number_of_nodes() > 1 else {n: 0.0 for n in nodes}

    # Weighted closeness/betweenness: use distance as cost when available
    use_weight = distance_attr if any(distance_attr in d for _, _, d in G.edges(data=True)) else None

    closeness_c = nx.closeness_centrality(G, distance=use_weight)
    betweenness_c = nx.betweenness_centrality(G, weight=use_weight, normalized=True)
    clustering = nx.clustering(G, weight=None)

    df = pd.DataFrame(
        {
            "degree": pd.Series(degree),
            "strength": pd.Series(strength),
            "degree_centrality": pd.Series(degree_c),
            "closeness_centrality": pd.Series(closeness_c),
            "betweenness_centrality": pd.Series(betweenness_c),
            "clustering_coefficient": pd.Series(clustering),
        }
    )

    # Attach metadata if present
    df["name"] = pd.Series({n: G.nodes[n].get("name", n) for n in nodes})
    df["department"] = pd.Series({n: G.nodes[n].get("department", "") for n in nodes})

    df.index.name = "id"
    return df


def connected_components_summary(G: nx.Graph) -> pd.DataFrame:
    """Return a small summary table of connected components."""
    comps = list(nx.connected_components(G))
    rows = []
    for i, comp in enumerate(sorted(comps, key=len, reverse=True), start=1):
        rows.append({"component": i, "size": len(comp)})
    return pd.DataFrame(rows)


def compute_graph_metrics(G: nx.Graph) -> dict[str, Any]:
    """Compute graph-level metrics.

    Notes:
    - diameter/radius are computed on the largest connected component if graph is disconnected.
    """
    n = G.number_of_nodes()
    m = G.number_of_edges()

    density = nx.density(G) if n > 1 else 0.0
    avg_clustering = nx.average_clustering(G) if n > 0 else 0.0
    num_components = nx.number_connected_components(G) if n > 0 else 0

    diameter = None
    radius = None
    if n > 0 and m > 0:
        largest_cc = max(nx.connected_components(G), key=len)
        H = G.subgraph(largest_cc).copy()
        if H.number_of_nodes() > 1 and nx.is_connected(H):
            diameter = nx.diameter(H)
            radius = nx.radius(H)

    return {
        "num_nodes": n,
        "num_edges": m,
        "density": float(density),
        "avg_clustering": float(avg_clustering),
        "num_components": int(num_components),
        "diameter_largest_cc": diameter,
        "radius_largest_cc": radius,
    }
