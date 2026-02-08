from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
import streamlit as st

from src.communities import community_map, girvan_newman_partition
from src.graph_build import build_graph
from src.io import load_dataset, load_edges_csv, load_nodes_csv, validate_dataset
from src.metrics import compute_graph_metrics, compute_node_metrics, connected_components_summary
from src.paths import shortest_path
from src.recommend import jaccard_recommendations
from src.viz import build_pyvis_html


DEFAULT_NODES = Path("data/nodes.csv")
DEFAULT_EDGES = Path("data/edges.csv")


st.set_page_config(page_title="Social Network Analyzer", layout="wide")

st.title("Social Network Analyzer")
st.caption("Graph Theory (NetworkX) + Streamlit + PyVis")


@st.cache_data
def _read_nodes_from_bytes(data: bytes) -> pd.DataFrame:
    return load_nodes_csv(io.BytesIO(data))


@st.cache_data
def _read_edges_from_bytes(data: bytes) -> pd.DataFrame:
    return load_edges_csv(io.BytesIO(data))


@st.cache_data
def _load_default_dataset() -> tuple[pd.DataFrame, pd.DataFrame]:
    ds = load_dataset(DEFAULT_NODES, DEFAULT_EDGES)
    return ds.nodes, ds.edges


def _id_options(nodes_df: pd.DataFrame) -> list[str]:
    return nodes_df["id"].astype(str).tolist()


def _id_to_label(nodes_df: pd.DataFrame) -> dict[str, str]:
    m = {}
    for _, r in nodes_df.iterrows():
        sid = str(r["id"]).strip()
        name = str(r.get("name", sid)).strip()
        dept = str(r.get("department", "")).strip()
        m[sid] = f"{name} ({sid})" + (f" - {dept}" if dept else "")
    return m


def _select_id(label: str, nodes_df: pd.DataFrame, key: str, default_id: str | None = None) -> str:
    mapping = _id_to_label(nodes_df)
    options = _id_options(nodes_df)

    default_index = 0
    if default_id in options:
        default_index = options.index(default_id)

    return st.selectbox(
        label,
        options=options,
        index=default_index,
        format_func=lambda x: mapping.get(x, x),
        key=key,
    )


with st.sidebar:
    st.header("Dataset")

    st.caption(
        "Required files: nodes.csv (id,name,department) and edges.csv (source_id,target_id,weight). "
        "Graph is undirected; weight is closeness (1..5)."
    )

    data_source = st.radio(
        "Data source",
        options=["Use demo data", "Upload CSVs"],
        index=0,
        horizontal=False,
    )

    try:
        if data_source == "Upload CSVs":
            nodes_up = st.file_uploader("Upload nodes.csv", type=["csv"], key="nodes_up")
            edges_up = st.file_uploader("Upload edges.csv", type=["csv"], key="edges_up")

            if nodes_up is None or edges_up is None:
                st.info("Upload both files to continue.")
                st.stop()

            nodes_df = _read_nodes_from_bytes(nodes_up.getvalue())
            edges_df = _read_edges_from_bytes(edges_up.getvalue())
            validate_dataset(nodes_df, edges_df)
        else:
            nodes_df, edges_df = _load_default_dataset()
    except Exception as e:
        st.error(f"Dataset error: {e}")
        st.stop()

    distance_mode = st.selectbox(
        "Shortest-path distance mode",
        options=["invert", "reciprocal"],
        index=0,
        help=(
            "Your CSV weight is closeness (5=closest). For shortest paths we convert it to a cost. "
            "invert uses distance = 6 - weight (recommended for 1..5). "
            "reciprocal uses distance = 1/weight."
        ),
    )


G = build_graph(nodes_df, edges_df, distance_mode=distance_mode)

graph_stats = compute_graph_metrics(G)
components_df = connected_components_summary(G)
node_metrics_df = compute_node_metrics(G)


tab_overview, tab_metrics, tab_paths, tab_communities, tab_recs = st.tabs(
    ["Overview", "Metrics", "Shortest Path", "Communities", "Suggested Friends"]
)


with tab_overview:
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Nodes", graph_stats["num_nodes"])
    c2.metric("Edges", graph_stats["num_edges"])
    c3.metric("Components", graph_stats["num_components"])
    c4.metric("Density", f"{graph_stats['density']:.3f}")
    c5.metric("Avg clustering", f"{graph_stats['avg_clustering']:.3f}")

    st.write("Connected components (sizes):")
    st.dataframe(components_df, width="stretch", hide_index=True)

    st.write("Graph visualization:")
    html = build_pyvis_html(G, color_by="department")
    st.components.v1.html(html, height=700, scrolling=True)


with tab_metrics:
    st.subheader("Node Metrics")
    st.caption(
        "Centrality shows influence/importance. Strength is the sum of relationship weights. "
        "Closeness/Betweenness use the chosen shortest-path distance mode."
    )

    sort_col = st.selectbox(
        "Sort by",
        options=[
            "degree",
            "strength",
            "degree_centrality",
            "closeness_centrality",
            "betweenness_centrality",
            "clustering_coefficient",
        ],
        index=3,
    )

    df_show = node_metrics_df.sort_values(sort_col, ascending=False).reset_index()
    st.dataframe(df_show, width="stretch", hide_index=True)

    st.subheader("Inspect One Student")
    chosen = _select_id("Student", nodes_df, key="metrics_student", default_id="S001")
    row = node_metrics_df.loc[[chosen]].reset_index()
    st.dataframe(row, width="stretch", hide_index=True)


with tab_paths:
    st.subheader("Shortest Path")

    colA, colB = st.columns(2)
    with colA:
        src_id = _select_id("Source", nodes_df, key="path_src", default_id="S001")
    with colB:
        dst_id = _select_id("Target", nodes_df, key="path_dst", default_id="S030")

    result = shortest_path(G, src_id, dst_id)
    if result is None:
        st.warning("No path available between these two students (disconnected graph).")
        st.write("Tip: try choosing nodes from the same connected component.")
    else:
        id_to_name = {n: G.nodes[n].get("name", n) for n in G.nodes()}
        readable = " → ".join([f"{id_to_name[n]} ({n})" for n in result.path])
        st.write(f"Path: {readable}")
        st.write(f"Total cost (distance): {result.total_cost:.2f}")

        st.write("Visualization (path highlighted):")
        html = build_pyvis_html(G, highlight_path=result.path, highlight_nodes=set(result.path), color_by="department")
        st.components.v1.html(html, height=700, scrolling=True)


with tab_communities:
    st.subheader("Community Detection (Girvan–Newman)")
    st.caption("Communities are detected from the connection structure (department is not used).")

    k = st.slider("Number of communities (k)", min_value=2, max_value=8, value=3, step=1)
    partition = girvan_newman_partition(G, k=k)
    cmap = community_map(partition)

    st.write("Visualization (colored by community):")
    html = build_pyvis_html(G, communities=cmap, color_by="community")
    st.components.v1.html(html, height=700, scrolling=True)

    # Build a simple table: node -> community
    rows = []
    for node_id in G.nodes():
        rows.append(
            {
                "id": node_id,
                "name": G.nodes[node_id].get("name", node_id),
                "department": G.nodes[node_id].get("department", ""),
                "community": int(cmap.get(node_id, -1)),
            }
        )
    comm_df = pd.DataFrame(rows).sort_values(["community", "name"]).reset_index(drop=True)
    st.dataframe(comm_df, width="stretch", hide_index=True)


with tab_recs:
    st.subheader("Suggested Friends (Jaccard Similarity)")
    st.caption(
        "Jaccard score = mutual friends / total unique friends. Existing friends are excluded. "
        "Higher score = stronger recommendation."
    )

    user_id = _select_id("Student", nodes_df, key="rec_user", default_id="S001")
    top_n = st.slider("Top N", min_value=3, max_value=20, value=10, step=1)

    recs = jaccard_recommendations(G, user_id, top_n=top_n)
    if recs.empty:
        st.info("No non-zero recommendations found for this student.")
    else:
        st.dataframe(recs, width="stretch", hide_index=True)
