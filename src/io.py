from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd


@dataclass(frozen=True)
class Dataset:
    nodes: pd.DataFrame
    edges: pd.DataFrame


def load_nodes_csv(path: str | Path) -> pd.DataFrame:
    """Load nodes CSV.

    Required columns: id,name,department

    Returns a DataFrame with normalized string columns.
    """
    path = Path(path)
    df = pd.read_csv(path)

    required = {"id", "name", "department"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"nodes.csv missing columns: {sorted(missing)}")

    df = df.copy()
    for col in ["id", "name", "department"]:
        df[col] = df[col].astype(str).str.strip()

    if (df["id"] == "").any():
        raise ValueError("nodes.csv has empty id values")

    if df["id"].duplicated().any():
        dups = df.loc[df["id"].duplicated(), "id"].tolist()
        raise ValueError(f"nodes.csv has duplicate ids: {dups[:20]}")

    return df


def load_edges_csv(path: str | Path) -> pd.DataFrame:
    """Load edges CSV.

    Required columns: source_id,target_id,weight

    Returns a DataFrame with normalized ids and integer weight.
    """
    path = Path(path)
    df = pd.read_csv(path)

    required = {"source_id", "target_id", "weight"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"edges.csv missing columns: {sorted(missing)}")

    df = df.copy()
    df["source_id"] = df["source_id"].astype(str).str.strip()
    df["target_id"] = df["target_id"].astype(str).str.strip()

    if (df["source_id"] == "").any() or (df["target_id"] == "").any():
        raise ValueError("edges.csv has empty source_id/target_id values")

    # Parse weight as integer
    df["weight"] = pd.to_numeric(df["weight"], errors="raise").astype(int)

    return df


def validate_dataset(nodes: pd.DataFrame, edges: pd.DataFrame, *, min_weight: int = 1, max_weight: int = 5) -> None:
    """Validate nodes/edges consistency.

    Checks:
    - all edge endpoints exist in nodes
    - no self-edges
    - weight is within [min_weight, max_weight]
    - no duplicate undirected pairs
    """
    node_ids = set(nodes["id"].astype(str))

    unknown = edges.loc[(~edges["source_id"].isin(node_ids)) | (~edges["target_id"].isin(node_ids))]
    if not unknown.empty:
        sample = unknown.head(10)[["source_id", "target_id"]].to_dict(orient="records")
        raise ValueError(f"edges.csv has edges with unknown node ids (sample): {sample}")

    self_edges = edges.loc[edges["source_id"] == edges["target_id"]]
    if not self_edges.empty:
        sample = self_edges.head(10)[["source_id", "target_id"]].to_dict(orient="records")
        raise ValueError(f"edges.csv has self-edges (sample): {sample}")

    bad_w = edges.loc[(edges["weight"] < min_weight) | (edges["weight"] > max_weight)]
    if not bad_w.empty:
        sample = bad_w.head(10)[["source_id", "target_id", "weight"]].to_dict(orient="records")
        raise ValueError(f"edges.csv has invalid weights outside {min_weight}..{max_weight} (sample): {sample}")

    undirected_pairs = edges.apply(lambda r: tuple(sorted((r["source_id"], r["target_id"]))), axis=1)
    dup = undirected_pairs.duplicated()
    if dup.any():
        idx = dup[dup].index[:10].tolist()
        sample = edges.loc[idx, ["source_id", "target_id", "weight"]].to_dict(orient="records")
        raise ValueError(f"edges.csv has duplicate undirected pairs (sample): {sample}")


def load_dataset(
    nodes_path: str | Path = Path("data/nodes.csv"),
    edges_path: str | Path = Path("data/edges.csv"),
    *,
    min_weight: int = 1,
    max_weight: int = 5,
) -> Dataset:
    """Load and validate dataset from CSVs."""
    nodes = load_nodes_csv(nodes_path)
    edges = load_edges_csv(edges_path)
    validate_dataset(nodes, edges, min_weight=min_weight, max_weight=max_weight)
    return Dataset(nodes=nodes, edges=edges)
