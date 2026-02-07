from __future__ import annotations

import networkx as nx
import pandas as pd


def jaccard_recommendations(G: nx.Graph, user_id: str, *, top_n: int = 10) -> pd.DataFrame:
    """Recommend new friends for user based on Jaccard coefficient.

    - Excludes existing neighbors and self
    - Returns top_n candidates with score and mutual friend count
    """
    user_id = str(user_id).strip()
    if user_id not in G:
        raise ValueError("user_id not found in graph")

    neighbors = set(G.neighbors(user_id))
    candidates = [n for n in G.nodes() if n != user_id and n not in neighbors]

    # Compute Jaccard for (user_id, candidate)
    preds = nx.jaccard_coefficient(G, [(user_id, c) for c in candidates])

    rows = []
    for u, v, score in preds:
        mutual = len(set(G.neighbors(u)).intersection(set(G.neighbors(v))))
        rows.append(
            {
                "user_id": u,
                "candidate_id": v,
                "score": float(score),
                "mutual_friends": int(mutual),
                "candidate_name": G.nodes[v].get("name", v),
                "candidate_department": G.nodes[v].get("department", ""),
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df = df.loc[df["score"] > 0].sort_values(["score", "mutual_friends"], ascending=[False, False])
    return df.head(top_n).reset_index(drop=True)
