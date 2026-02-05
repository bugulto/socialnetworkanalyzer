# Social Network Analyzer

Interactive social network analysis built with Streamlit and NetworkX. Load a student friendship dataset (nodes and weighted edges), explore graph metrics, visualize communities, compute shortest paths, and get friend recommendations.

## Features

- **Overview dashboard** with graph size, density, and connected components
- **Node metrics**: degree, strength, centrality measures, clustering coefficient
- **Shortest paths** with distance mode selection based on relationship closeness
- **Community detection** using Girvan-Newman
- **Friend recommendations** using Jaccard similarity
- **Interactive visualization** with PyVis (node metadata, path highlighting)

## Demo dataset

The repo includes demo CSVs in `data/`:

- `data/nodes.csv`: `id,name,department`
- `data/edges.csv`: `source_id,target_id,weight`

`weight` represents closeness on a 1-5 scale (5 = closest). The graph is undirected.

## Requirements

- Python 3.10+
- Dependencies listed in `requirements.txt`

## Quick start

```bash
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

Open the URL printed by Streamlit (usually `http://localhost:8501`).

## Using your own data

1. Prepare `nodes.csv` with columns:
   - `id`: unique node id (string or number)
   - `name`: display name
   - `department`: group or category
2. Prepare `edges.csv` with columns:
   - `source_id`: node id
   - `target_id`: node id
   - `weight`: closeness (1-5)
3. In the sidebar, choose **Upload CSVs** and select both files.

The app validates:
- all edge endpoints exist in `nodes.csv`
- no self-edges
- weights are in the allowed range
- no duplicate undirected pairs

## Shortest-path distance modes

Weights represent **closeness**, but shortest-path algorithms expect **cost**. The app converts weights to distance using one of these modes:

- **invert** (default): `distance = 6 - weight` (best for 1-5)
- **reciprocal**: `distance = 1 / weight`

## Project structure

```
app.py                  # Streamlit UI and app flow
src/
  communities.py        # Girvan-Newman partitioning
  graph_build.py        # Graph construction and distance conversion
  io.py                 # CSV loading and validation
  metrics.py            # Graph and node metrics
  paths.py              # Shortest path utility
  recommend.py          # Jaccard recommendations
  viz.py                # PyVis HTML rendering
```

## Notes

- The graph is **undirected**.
- Community detection ignores weights (structure only).
- Shortest paths respect the selected distance mode.

## License

MIT License

Copyright (c) 2026 Prabal Lamichhane

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
