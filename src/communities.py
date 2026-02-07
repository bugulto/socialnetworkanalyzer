from __future__ import annotations

from collections.abc import Iterable

import networkx as nx


def girvan_newman_partition(G: nx.Graph, *, k: int = 3) -> list[set[str]]:
    """Compute a Girvan-Newman community partition with k communities.

    If the algorithm cannot reach exactly k communities (small graphs), returns
    the deepest partition it reached.

    Note: This uses the unweighted graph structure.
    """
    if G.number_of_nodes() == 0:
        return []

    comp = nx.community.girvan_newman(G)

    last_partition: list[set[str]] = [set(G.nodes())]
    for partition in comp:
        current = [set(c) for c in partition]
        last_partition = current
        if len(current) >= k:
            # If we overshoot, keep the first k largest communities
            current_sorted = sorted(current, key=len, reverse=True)
            return current_sorted[:k]

    return last_partition


def community_map(partition: Iterable[Iterable[str]]) -> dict[str, int]:
    """Convert a partition into a node->community_id mapping."""
    mapping: dict[str, int] = {}
    for i, community in enumerate(partition):
        for node in community:
            mapping[str(node)] = i
    return mapping
