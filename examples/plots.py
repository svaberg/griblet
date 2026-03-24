import numpy as np
import itertools
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


def flattened_dependency_graph(computation_graph):
    """
    Construct a flattened field-level dependency graph.

    Returns a directed graph with one node per field and an edge
    need → field for every need appearing in any way.
    Way structure and cost information are discarded.
    """
    dependency_graph = nx.DiGraph()
    # Add all fields as nodes first
    for name in computation_graph.ways:
        dependency_graph.add_node(name)
    for output, way_list in computation_graph.ways.items():
        for way in way_list:
            for need in way["needs"]:
                dependency_graph.add_edge(need, output)
    return dependency_graph


def collect_subtree_nodes_edges(path):
    """
    Collect nodes and edges from a chosen path.

    Traverses a PathNode and returns:
    - nodes: set of data names in the path
    - edges: set of (need, name) edges used by the path
    """
    nodes = set()
    edges = set()
    def visit(node):
        nodes.add(node.name)
        for need in getattr(node, "needs", []):
            edges.add((need.name, node.name))
            visit(need)
    visit(path)
    return nodes, edges


def plot_flattened_computation_graph(
    computation_graph,
    ax,
    title="Computation Graph Network",
    show_node_metadata=True,
    pos=None):
    """
    Plot a flattened dependency graph of the computation graph.

    Displays all fields as nodes and all possible dependency edges,
    ignoring way grouping. Optionally annotates nodes with
    per-way cost and selected metadata.
    """
    digraph = flattened_dependency_graph(computation_graph)

    # Build node labels with all recipes and their costs/metadata
    if show_node_metadata:
        node_labels = {}
        for n in digraph.nodes:
            ways = computation_graph.ways.get(n, [])
            lines = [str(n)]
            for i, way in enumerate(ways):
                cost = way["cost"]
                cost_str = cost if isinstance(cost, (int, float)) else "callable"
                desc = way["metadata"].get("description", "")
                unit = way["metadata"].get("unit", "")
                extra = []
                if desc: extra.append(desc)
                if unit: extra.append(f"[{unit}]")
                extra_str = " ".join(extra)
                if len(ways) > 1:
                    lines.append(f"({i+1}) cost={cost_str} {extra_str}")
                else:
                    lines.append(f"cost={cost_str} {extra_str}")
            node_labels[n] = "\n".join(lines)
    else:
        node_labels = {n: str(n) for n in digraph.nodes}

    # Use a circular layout if no edges (to avoid node overlap), else spring layout
    if not digraph.edges:
        pos = nx.circular_layout(digraph)
        subtitle = "\n(No computation recipes yet; only loader fields present.)"
    else:
        if pos is None:
            pos = nx.spring_layout(digraph, seed=42)
        subtitle = ""

    nx.draw_networkx_nodes(
        digraph, pos, node_color="skyblue", edgecolors="black",
        node_size=2100, linewidths=2, ax=ax
    )
    nx.draw_networkx_labels(
        digraph, pos, labels=node_labels, font_size=12,
        font_weight="bold", ax=ax
    )
    if digraph.edges:
        nx.draw_networkx_edges(
            digraph, pos, arrowstyle="->", arrowsize=20,
            width=2, edge_color="gray", ax=ax
        )
        # No edge labels

    ax.set_title(title + subtitle)
    ax.axis("off")


def plot_computation_paths(
    computation_graph,
    paths,
    ax,
    *,
    labels=None,
    colors=None,
    title="Computation Paths",
    node_size=1200,
    font_size=11
):
    """
    Plot multiple chosen paths as colored, curved arrows on top of the
    flattened dependency graph.

    computation_graph: Graph object (with .ways)
    paths: list of chosen path roots
    ax: matplotlib axis to draw on
    labels: list of labels for legend (optional)
    colors: list of colors (optional)
    """
    # Build flattened dependency graph
    digraph = flattened_dependency_graph(computation_graph)
    # DG = nx.DiGraph()
    # for node, ways in computation_graph.ways.items():
    #     for way in ways:
    #         for need in way["needs"]:
    #             DG.add_edge(dep, node)
    # Compute layout
    pos = nx.spring_layout(digraph, seed=42)

    # Collect union of all nodes/edges in any path
    all_path_nodes = set()
    all_path_edges = set()

    # Process all paths: get per-path nodes/edges
    path_nodes_edges = [collect_subtree_nodes_edges(path) for path in paths]
    for nodes, edges in path_nodes_edges:
        all_path_nodes.update(nodes)
        all_path_edges.update(edges)

    # Draw all nodes in lightgray, to show the union graph background
    # Draw all possible edges in lightgray (flattened)
    nx.draw_networkx_nodes(digraph, pos, node_color="lightgray", node_size=node_size, ax=ax)
    nx.draw_networkx_labels(digraph, pos, font_size=font_size, ax=ax)
    nx.draw_networkx_edges(digraph, pos, edgelist=digraph.edges, edge_color="gray", 
                           width=3, arrows=True, arrowstyle="->", ax=ax,
                           arrowsize=26)

    # Prepare colors, labels
    if colors is None:
        colors = [f"C{i}" for i in range(len(paths))]
    if labels is None:
        labels = [f"Path {i+1}" for i in range(len(paths))]

    rad_vals = [-0.1, 0.1, 0.3, -0.3, 0.2, -0.2]
    legend_elements = [Line2D([0], [0], marker='o', color='w', label='All possible dependencies',
                              markerfacecolor='lightgray', markersize=12)]
    # Draw each path's edges in its own color/curve
    for i, ((nodes, edges), color, label) in enumerate(zip(path_nodes_edges, colors, labels)):
        rad = rad_vals[i % len(rad_vals)]
        nx.draw_networkx_edges(
            digraph, pos, edgelist=edges,
            edge_color=color, width=3, ax=ax,
            arrows=True, arrowstyle="->", arrowsize=26,
            connectionstyle=f"arc3,rad={rad}"
        )
        legend_elements.append(Line2D([0], [0], color=color, lw=3, label=label))

    # Highlight path nodes (optional: only those in any path) with white faces, colored border
    nx.draw_networkx_nodes(digraph, pos, nodelist=list(all_path_nodes), node_color="white",
                           node_size=node_size, edgecolors="lightgray", linewidths=3, ax=ax)

    ax.legend(handles=legend_elements, loc="upper left")
    ax.set_title(title)
    ax.axis("off")


#
# # And-or graph stuff
#
def and_or_graph(computation_graph):
    """
    Build explicit AND–OR graph.

    OR nodes  : ("F", field)
    AND nodes : ("W", out_field, way_index)

    Edges:
      ("F", out) -> ("W", out, i)     alternative way for out
      ("W", out, i) -> ("F", dep)     required need
    """
    andor_graph = nx.DiGraph()

    for out, ways in computation_graph.ways.items():
        f_out = ("F", out)
        andor_graph.add_node(f_out, kind="field", field=out)

        for i, way in enumerate(ways):
            r_node = ("W", out, i)
            andor_graph.add_node(
                r_node,
                kind="way",
                out=out,
                idx=i,
                metadata=way.get("metadata", {}),
            )
            andor_graph.add_edge(f_out, r_node)

            for need in way["needs"]:
                f_need = ("F", need)
                andor_graph.add_node(f_need, kind="field", field=need)
                andor_graph.add_edge(r_node, f_need)

    return andor_graph


def field_ordinal_levels(comp_graph, direction="out_to_dep"):
    # 1) field projection
    H = nx.DiGraph()
    for out, ways in comp_graph.ways.items():
        H.add_node(out)
        for way in ways:
            if not way["needs"]:
                continue
            for need in way["needs"]:
                H.add_node(need)
                if direction == "out_to_dep":
                    H.add_edge(out, need)
                else:
                    H.add_edge(need, out)

    # 2) collapse cycles
    sccs = list(nx.strongly_connected_components(H))
    comp_of = {}
    for i, s in enumerate(sccs):
        for v in s:
            comp_of[v] = i

    # condensation DAG (nodes are SCC indices)
    C = nx.DiGraph()
    C.add_nodes_from(range(len(sccs)))
    for u, v in H.edges():
        cu, cv = comp_of[u], comp_of[v]
        if cu != cv:
            C.add_edge(cu, cv)

    # 3) longest-path levels on DAG
    level = {c: 0 for c in C.nodes()}
    for c in nx.topological_sort(C):
        for nxt in C.successors(c):
            level[nxt] = max(level[nxt], level[c] + 1)

    # 4) per-field ordinal level (same within SCC)
    return {f: level[comp_of[f]] for f in H.nodes()}


def plot_and_or_graph(comp_graph, ax, title="Computation graph"):
    """
    Full AND–OR structure with ways as small round nodes near their output field.
      - field nodes: larger circles
      - way nodes: smaller circles, colored per way
      - way color applies to the way node and its outgoing edges (needs)
    """

    # --- build explicit AND–OR graph ---
    andor_graph = nx.DiGraph()
    field_nodes = set()
    way_nodes = []

    for out, ways in comp_graph.ways.items():
        f_out = ("F", out)
        andor_graph.add_node(f_out, kind="field", label=str(out))
        field_nodes.add(f_out)

        for i, way in enumerate(ways):
            if not way["needs"]:
                continue   # Skip loader recipes (no dependencies, no edges)
            r_node = ("W", out, i)
            andor_graph.add_node(r_node, kind="way", out=out, idx=i, label=f"{i+1}")
            way_nodes.append(r_node)

            # OR edge: field -> way
            andor_graph.add_edge(f_out, r_node, kind="alt")

            # AND edges: way -> needs
            for need in way["needs"]:
                f_need = ("F", need)
                andor_graph.add_node(f_need, kind="field", label=str(need))
                field_nodes.add(f_need)
                andor_graph.add_edge(r_node, f_need, kind="req")

    field_nodes = list(field_nodes)

    # --- layout only the FIELD subgraph (min crossings), then pin recipes near outputs ---
    field_sub = nx.DiGraph()
    field_sub.add_nodes_from(field_nodes)
    # induced edges between fields if any way references (need -> out)
    for (u, v, d) in andor_graph.edges(data=True):
        if u[0] == "W" and v[0] == "F":
            # u is way(out,i), v is need field; add need -> out for layout
            out_field = ("F", u[1])
            need_field = v
            field_sub.add_edge(need_field, out_field)

 
    try:
        from networkx.drawing.nx_agraph import graphviz_layout
        posF = graphviz_layout(field_sub, prog="dot")
    except ImportError:
        posF = nx.kamada_kawai_layout(field_sub)
    pos = dict(posF)

    #
    # place way nodes on a ring around the output field
    #
    ring_r = 0.08
    ring_r = 30
    for out, ways in comp_graph.ways.items():
        f_out = ("F", out)
        if f_out not in pos:
            continue

        x0, y0 = pos[f_out]
        n = len(ways)
        if n == 0:
            continue

        for i in range(n):
            r_node = ("W", out, i)
            angle = 2.0 * np.pi * i / n
            angle += np.pi / 2.0  
            pos[r_node] = (
                x0 + ring_r * np.cos(angle),
                y0 + ring_r * np.sin(angle),
            )
    # --- colors per way ---
    color_cycle = itertools.cycle(plt.cm.tab10.colors)
    way_color = {}
    for out in sorted(comp_graph.ways.keys(), key=str):
        for i, way in enumerate(comp_graph.ways[out]):
            if not way["needs"]:
                continue
            way_color[("W", out, i)] = next(color_cycle)


    # way nodes grouped by color (so each group gets its color)
    for r in way_nodes:
        nx.draw_networkx_nodes(
            andor_graph, pos,
            nodelist=[r],
            node_shape="o",
            node_size=450,
            # edgecolors="black",
            node_color=[way_color[r]],
            ax=ax
        )
    way_labels = {n: andor_graph.nodes[n]["label"] for n in way_nodes}
    nx.draw_networkx_labels(andor_graph, pos, labels=way_labels, font_size=8, ax=ax, font_color='white')

    # --- draw nodes ---
    nx.draw_networkx_nodes(
        andor_graph, pos,
        nodelist=field_nodes,
        node_shape="o",
        node_size=1600,
        node_color="lightgray",
        edgecolors="black",
        ax=ax,
    )

    field_labels = {n: andor_graph.nodes[n]["label"] for n in field_nodes}
    nx.draw_networkx_labels(andor_graph, pos, labels=field_labels, font_size=10, ax=ax)

    # --- edges ---
    # field -> way edges: colored by way (same as way node)
    for r in way_nodes:
        u = ("F", r[1])   # output field node
        v = r            # way node
        if andor_graph.has_edge(u, v):
            nx.draw_networkx_edges(
                andor_graph, pos,
                # edgelist=[(u, v)],
                edgelist=[(v, u)],
                arrows=True, arrowstyle="->", arrowsize=16,
                # arrows=False,
                width=4,
                edge_color=[way_color[r]],
                connectionstyle="arc3,rad=0.08",
                min_source_margin=10, min_target_margin=20,
                ax=ax
            )

    # way -> need edges: colored by way
    for r in way_nodes:
        req_edges = [(v, u) for (u, v, d) in andor_graph.out_edges(r, data=True)
                    if d.get("kind") == "req"]  # <-- flipped
        if req_edges:
            nx.draw_networkx_edges(
                andor_graph, pos,
                edgelist=req_edges,
                arrows=True, arrowstyle="->", arrowsize=16,
                # arrows=False,
                width=2.2,
                edge_color=[way_color[r]],
                connectionstyle="arc3,rad=0.18",
                min_source_margin=20, min_target_margin=10,
                ax=ax
            )
    ax.set_title(title)
    ax.axis("off")
    return andor_graph, pos
