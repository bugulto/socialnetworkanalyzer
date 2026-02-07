from __future__ import annotations

from dataclasses import dataclass

import networkx as nx


@dataclass(frozen=True)
class PathResult:
    path: list[str]
    total_cost: float


def shortest_path(
    G: nx.Graph,
    source_id: str,
    target_id: str,
    *,
    cost_attr: str = "distance",
) -> PathResult | None:
    """Compute shortest path between two nodes.

    Uses Dijkstra when cost_attr exists; otherwise falls back to unweighted shortest path.

    Returns None if no path exists.
    """
    source_id = str(source_id).strip()
    target_id = str(target_id).strip()

    if source_id not in G or target_id not in G:
        raise ValueError("source_id/target_id not found in graph")

    has_cost = any(cost_attr in d for _, _, d in G.edges(data=True))

    try:
        if has_cost:
            path = nx.dijkstra_path(G, source_id, target_id, weight=cost_attr)
            total = nx.dijkstra_path_length(G, source_id, target_id, weight=cost_attr)
        else:
            path = nx.shortest_path(G, source_id, target_id)
            total = float(len(path) - 1)
        return PathResult(path=list(path), total_cost=float(total))
    except nx.NetworkXNoPath:
        return None
