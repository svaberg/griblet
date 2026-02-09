import numpy as np
import itertools
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D



def flattened_dependency_graph(computation_graph):
    """
    Construct a flattened field-level dependency graph.

    Returns a directed graph with one node per field and an edge
    dep → field for every dependency appearing in any recipe.
    Recipe structure and cost information are discarded.
    """
    DG = nx.DiGraph()
    # Add all fields as nodes first
    for field in computation_graph.recipes:
        DG.add_node(field)
    # Add edges for all recipes with dependencies
    for output, recipe_list in computation_graph.recipes.items():
        for recipe in recipe_list:
            for dep in recipe['deps']:
                DG.add_edge(dep, output)
    return DG

def collect_subtree_nodes_edges(tree):
    """
    Collect nodes and edges from a resolved computation tree.

    Traverses a ComputationTreeNode and returns:
    - nodes: set of field names in the tree
    - edges: set of (dep_field, field) edges used by the plan
    """
    nodes = set()
    edges = set()
    def visit(node):
        nodes.add(node.field)
        for dep in getattr(node, "deps", []):
            edges.add((dep.field, node.field))
            visit(dep)
    visit(tree)
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
    ignoring recipe grouping. Optionally annotates nodes with
    per-recipe cost and selected metadata.
    """
    DG = flattened_dependency_graph(computation_graph)

    # Build node labels with all recipes and their costs/metadata
    if show_node_metadata:
        node_labels = {}
        for n in DG.nodes:
            recipes = computation_graph.recipes.get(n, [])
            lines = [str(n)]
            for i, r in enumerate(recipes):
                # Format cost (show 'callable' if not number)
                cost = r['cost']
                cost_str = cost if isinstance(cost, (int, float)) else "callable"
                # Get metadata fields
                desc = r['metadata'].get('description', '')
                unit = r['metadata'].get('unit', '')
                extra = []
                if desc: extra.append(desc)
                if unit: extra.append(f"[{unit}]")
                extra_str = " ".join(extra)
                # Multiple recipes: number them
                if len(recipes) > 1:
                    lines.append(f"({i+1}) cost={cost_str} {extra_str}")
                else:
                    lines.append(f"cost={cost_str} {extra_str}")
            node_labels[n] = "\n".join(lines)
    else:
        node_labels = {n: str(n) for n in DG.nodes}

    # Use a circular layout if no edges (to avoid node overlap), else spring layout
    if not DG.edges:
        pos = nx.circular_layout(DG)
        subtitle = "\n(No computation recipes yet; only loader fields present.)"
    else:
        if pos is None:
            pos = nx.spring_layout(DG, seed=42)
        subtitle = ""

    nx.draw_networkx_nodes(
        DG, pos, node_color="skyblue", edgecolors="black",
        node_size=2100, linewidths=2, ax=ax
    )
    nx.draw_networkx_labels(
        DG, pos, labels=node_labels, font_size=12,
        font_weight="bold", ax=ax
    )
    if DG.edges:
        nx.draw_networkx_edges(
            DG, pos, arrowstyle="->", arrowsize=20,
            width=2, edge_color="gray", ax=ax
        )
        # No edge labels

    ax.set_title(title + subtitle)
    ax.axis("off")



def plot_recipe_colored_edges(computation_graph, ax, node_pos=None):
    """
    Plot the dependency graph with edges colored by recipe.

    Each recipe contributing to a field is assigned a distinct color,
    and all edges belonging to that recipe are drawn in that color.
    Nodes are shared across all recipes.
    """
    DG = nx.DiGraph()
    # Add all nodes first
    for node in computation_graph.recipes.keys():
        DG.add_node(node)
    # Layout
    if node_pos is None:
        node_pos = nx.spring_layout(DG, seed=42)

    # Assign a unique color to each recipe of each node
    color_cycle = itertools.cycle(plt.cm.tab10.colors)
    edge_segments = []
    edge_colors = []
    legend_labels = []
    for node, recipes in computation_graph.recipes.items():
        for i, recipe in enumerate(recipes):
            color = next(color_cycle)
            label = f"{node} recipe {i+1}"
            for dep in recipe['deps']:
                edge_segments.append((dep, node))
                edge_colors.append(color)
                legend_labels.append(label)

    # Plot all nodes
    nx.draw_networkx_nodes(DG, node_pos, node_color="white", edgecolors="black", node_size=1500, ax=ax)
    nx.draw_networkx_labels(DG, node_pos, font_weight="bold", ax=ax)

    # Plot each recipe edge with its own color
    for (u, v), color, label in zip(edge_segments, edge_colors, legend_labels):
        nx.draw_networkx_edges(
            DG, node_pos, edgelist=[(u, v)],
            edge_color=[color], arrowsize=20, width=3, ax=ax, label=label
        )

    # Build unique legend
    import matplotlib.lines as mlines
    seen = {}
    handles = []
    for label, color in zip(legend_labels, edge_colors):
        if label not in seen:
            handles.append(mlines.Line2D([], [], color=color, label=label, linewidth=3))
            seen[label] = True
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(1,1))
    ax.set_title("Computation Graph with Recipe-colored Edges")
    ax.axis("off")


def plot_recipe_colored_edges_curved(computation_graph, ax, node_pos=None):
    """
    Plot the dependency graph with recipe-colored curved edges.

    Similar to plot_recipe_colored_edges, but uses curved edges with
    varying curvature to reduce overlap when multiple recipes share
    the same dependencies.
    """
    DG = nx.DiGraph()
    for node in computation_graph.recipes:
        DG.add_node(node)
    if node_pos is None:
        node_pos = nx.spring_layout(DG, seed=42)
    color_cycle = itertools.cycle(plt.cm.tab10.colors)
    rad_vals = [-0.3, 0, 0.3, 0.6, -0.6, 0.9, -0.9]
    legend_handles = []
    seen_labels = set()
    for node, recipes in computation_graph.recipes.items():
        for i, recipe in enumerate(recipes):
            if not recipe['deps']:
                continue  # Skip loader recipes (no dependencies, no edges)
            color = next(color_cycle)
            rad = rad_vals[i % len(rad_vals)]
            label = f"{node} recipe {i+1}"
            # Draw edges for this recipe
            for dep in recipe['deps']:
                nx.draw_networkx_edges(
                    DG, node_pos, edgelist=[(dep, node)],
                    edge_color=[color], arrowsize=20, width=3, ax=ax,
                    connectionstyle=f"arc3,rad={rad}", label=label,
                    arrows=True, arrowstyle="->", 
                    # arrowsize=28,                
                    )
            # Only add one legend handle per recipe label/color
            if label not in seen_labels:
                import matplotlib.lines as mlines
                legend_handles.append(mlines.Line2D([], [], color=color, label=label, linewidth=3))
                seen_labels.add(label)
    # Draw all nodes and labels (once)
    nx.draw_networkx_labels(DG, node_pos, font_weight="bold", ax=ax)
    nx.draw_networkx_nodes(DG, node_pos, node_color="white", edgecolors="black", node_size=400, ax=ax)
    ax.legend(handles=legend_handles, loc="upper left")
    ax.set_title("Computation Graph with Curved, Recipe-colored Edges")
    ax.axis("off")


def plot_computation_paths(
    computation_graph,
    trees,
    ax,
    *,
    labels=None,
    colors=None,
    title="Computation Paths",
    node_size=1200,
    font_size=11
):
    """
    Plot multiple computation trees as colored, curved arrows on top of the 
    flattened dependency graph.

    computation_graph: ComputationGraph object (with .recipes)
    trees: list of computation tree roots (e.g., from DependencySolver.resolve_field)
    ax: matplotlib axis to draw on
    labels: list of labels for legend (optional)
    colors: list of colors (optional)
    """
    # Build flattened dependency graph
    DG = flattened_dependency_graph(computation_graph)
    # DG = nx.DiGraph()
    # for node, recipes in computation_graph.recipes.items():
    #     for recipe in recipes:
    #         for dep in recipe['deps']:
    #             DG.add_edge(dep, node)
    # Compute layout
    pos = nx.spring_layout(DG, seed=42)

    # Collect union of all nodes/edges in any tree
    all_tree_nodes = set()
    all_tree_edges = set()

    # Process all trees: get per-tree nodes/edges
    trees_nodes_edges = [collect_subtree_nodes_edges(t) for t in trees]
    for nodes, edges in trees_nodes_edges:
        all_tree_nodes.update(nodes)
        all_tree_edges.update(edges)

    # Draw all nodes in lightgray, to show the union graph background
    # Draw all possible edges in lightgray (flattened)
    nx.draw_networkx_nodes(DG, pos, node_color="lightgray", node_size=node_size, ax=ax)
    nx.draw_networkx_labels(DG, pos, font_size=font_size, ax=ax)
    nx.draw_networkx_edges(DG, pos, edgelist=DG.edges, edge_color="gray", 
                           width=3, arrows=True, arrowstyle="->", ax=ax,
                           arrowsize=26)

    # Prepare colors, labels
    if colors is None:
        colors = [f"C{i}" for i in range(len(trees))]
    if labels is None:
        labels = [f"Path {i+1}" for i in range(len(trees))]

    rad_vals = [-0.1, 0.1, 0.3, -0.3, 0.2, -0.2]
    legend_elements = [Line2D([0], [0], marker='o', color='w', label='All possible dependencies',
                              markerfacecolor='lightgray', markersize=12)]
    # Draw each tree's edges in its own color/curve
    for i, ((nodes, edges), color, label) in enumerate(zip(trees_nodes_edges, colors, labels)):
        rad = rad_vals[i % len(rad_vals)]
        # import pdb; pdb.set_trace()
        print(color, label)
        nx.draw_networkx_edges(
            DG, pos, edgelist=edges,
            edge_color=color, width=3, ax=ax,
            arrows=True, arrowstyle="->", arrowsize=26,
            connectionstyle=f"arc3,rad={rad}"
        )
        legend_elements.append(Line2D([0], [0], color=color, lw=3, label=label))

    # Highlight tree nodes (optional: only those in any tree) with white faces, colored border
    nx.draw_networkx_nodes(DG, pos, nodelist=list(all_tree_nodes), node_color="white",
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
    AND nodes : ("R", out_field, recipe_index)

    Edges:
      ("F", out) -> ("R", out, i)     alternative recipe for out
      ("R", out, i) -> ("F", dep)     required dependency
    """
    G = nx.DiGraph()

    for out, recipes in computation_graph.recipes.items():
        f_out = ("F", out)
        G.add_node(f_out, kind="field", field=out)

        for i, r in enumerate(recipes):
            r_node = ("R", out, i)
            G.add_node(
                r_node,
                kind="recipe",
                out=out,
                idx=i,
                metadata=r.get("metadata", {}),
            )
            G.add_edge(f_out, r_node)

            for dep in r["deps"]:
                f_dep = ("F", dep)
                G.add_node(f_dep, kind="field", field=dep)
                G.add_edge(r_node, f_dep)

    return G


def plot_and_or_graph(computation_graph, ax, title="AND–OR computation graph"):
    # --- build AND–OR graph ---
    G = nx.DiGraph()
    for out, recipes in computation_graph.recipes.items():
        f_out = ("F", out)
        G.add_node(f_out, kind="field", label=out)
        for i, r in enumerate(recipes):
            r_node = ("R", out, i)
            G.add_node(r_node, kind="recipe", label=f"{out}#{i+1}")
            G.add_edge(f_out, r_node)
            for dep in r["deps"]:
                f_dep = ("F", dep)
                G.add_node(f_dep, kind="field", label=dep)
                G.add_edge(r_node, f_dep)

    # --- layout: minimize crossings ---
    try:
        from networkx.drawing.nx_agraph import graphviz_layout
        pos = graphviz_layout(G, prog="dot")
    except Exception:
        pos = nx.kamada_kawai_layout(G)

    # --- split nodes ---
    field_nodes  = [n for n,d in G.nodes(data=True) if d["kind"]=="field"]
    recipe_nodes = [n for n,d in G.nodes(data=True) if d["kind"]=="recipe"]

    # --- draw nodes ---
    nx.draw_networkx_nodes(
        G, pos, nodelist=field_nodes,
        node_shape="o", node_size=1400,
        edgecolors="black", ax=ax
    )
    nx.draw_networkx_nodes(
        G, pos, nodelist=recipe_nodes,
        node_shape="s", node_size=900,
        edgecolors="black", ax=ax
    )

    # --- labels ---
    labels = {n: d["label"] for n,d in G.nodes(data=True)}
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=10, ax=ax)

    # --- curved edges, arrows stop before nodes ---
    nx.draw_networkx_edges(
        G, pos,
        arrows=True,
        arrowstyle="->",
        arrowsize=18,
        width=2,
        connectionstyle="arc3,rad=0.15",
        min_source_margin=20,
        min_target_margin=20,
        ax=ax
    )

    ax.set_title(title)
    ax.axis("off")


from matplotlib.patches import Circle, Wedge, FancyArrowPatch
def plot_and_or_with_nubs(computation_graph, ax, title="AND–OR (recipes as nubs)"):
    # --- field-only graph for layout (deps -> out) ---
    DG = nx.DiGraph()
    for out, recipes in computation_graph.recipes.items():
        DG.add_node(out)
        for r in recipes:
            for dep in r["deps"]:
                DG.add_node(dep)
                DG.add_edge(dep, out)

    # layout: try dot, else fallback
    try:
        from networkx.drawing.nx_agraph import graphviz_layout
        pos = graphviz_layout(DG, prog="dot")
    except Exception:
        pos = nx.kamada_kawai_layout(DG)

    # de-overlap exact collisions (dot sometimes stacks)
    buckets = {}
    for n, (x, y) in pos.items():
        key = (round(float(x), 6), round(float(y), 6))
        buckets.setdefault(key, []).append(n)
    eps = 25.0
    for (x, y), nodes in buckets.items():
        if len(nodes) > 1:
            for j, n in enumerate(nodes):
                pos[n] = (x, y + (j - (len(nodes)-1)/2.0) * eps)

    # --- draw field circles ---
    field_R = 18.0   # radius in layout units
    nub_r   = 8.0
    nub_gap = 3.0

    for f, (x, y) in pos.items():
        ax.add_patch(Circle((x, y), radius=field_R, ec="black", fc="white", lw=2))
        ax.text(x, y, str(f), ha="center", va="center", fontsize=10, fontweight="bold")

    # --- draw recipe nubs + edges ---
    # nub centers: spread along a line below the field circle
    for out, recipes in computation_graph.recipes.items():
        if out not in pos:
            continue
        x0, y0 = pos[out]
        nrec = len(recipes)
        if nrec == 0:
            continue

        # horizontal offsets so multiple nubs sit under the same field
        step = 2 * nub_r + nub_gap
        start = -0.5 * (nrec - 1) * step

        for i, r in enumerate(recipes):
            cx = x0 + start + i * step
            cy = y0 - (field_R + nub_r + 2.0)

            # nub = semicircle opening downward (180°..360°)
            ax.add_patch(Wedge((cx, cy), r=nub_r, theta1=180, theta2=360, ec="black", fc="white", lw=2))
            # optional tiny label inside nub
            ax.text(cx, cy - 0.35*nub_r, f"{i+1}", ha="center", va="center", fontsize=8)

            # edges from nub center to each dependency field
            for dep in r["deps"]:
                if dep not in pos:
                    continue
                x1, y1 = pos[dep]

                # curvature: alternate sign by recipe index
                rad = 0.15 * (1 if (i % 2 == 0) else -1)

                arrow = FancyArrowPatch(
                    (cx, cy), (x1, y1),
                    arrowstyle='-|>',
                    mutation_scale=14,
                    lw=2,
                    color="gray",
                    connectionstyle=f"arc3,rad={rad}",
                    shrinkA=nub_r + 2.0,
                    shrinkB=field_R + 4.0,
                )
                ax.add_patch(arrow)

    ax.set_title(title)
    ax.axis("off")


    import itertools
import networkx as nx
import matplotlib.pyplot as plt

import networkx as nx

def field_ordinal_levels(comp_graph, direction="out_to_dep"):
    # 1) field projection
    H = nx.DiGraph()
    for out, recipes in comp_graph.recipes.items():
        H.add_node(out)
        for r in recipes:
            if not r["deps"]:
                continue
            for dep in r["deps"]:
                H.add_node(dep)
                if direction == "out_to_dep":
                    H.add_edge(out, dep)
                else:
                    H.add_edge(dep, out)

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


def plot_and_or_graph_c(comp_graph, ax, title="Computation graph"):
    """
    Full AND–OR structure with recipes as small round nodes near their output field.
      - field nodes: larger circles
      - recipe nodes: smaller circles, colored per recipe
      - recipe color applies to the recipe node and its outgoing edges (deps)
    """

    # --- build explicit AND–OR graph ---
    G = nx.DiGraph()
    field_nodes = set()
    recipe_nodes = []

    for out, recipes in comp_graph.recipes.items():
        f_out = ("F", out)
        G.add_node(f_out, kind="field", label=str(out))
        field_nodes.add(f_out)

        for i, r in enumerate(recipes):
            if not r["deps"]:
                continue   # Skip loader recipes (no dependencies, no edges)
            r_node = ("R", out, i)
            G.add_node(r_node, kind="recipe", out=out, idx=i, label=f"{i+1}")
            recipe_nodes.append(r_node)

            # OR edge: field -> recipe
            G.add_edge(f_out, r_node, kind="alt")

            # AND edges: recipe -> deps
            for dep in r["deps"]:
                f_dep = ("F", dep)
                G.add_node(f_dep, kind="field", label=str(dep))
                field_nodes.add(f_dep)
                G.add_edge(r_node, f_dep, kind="req")

    field_nodes = list(field_nodes)

    # --- layout only the FIELD subgraph (min crossings), then pin recipes near outputs ---
    field_sub = nx.DiGraph()
    field_sub.add_nodes_from(field_nodes)
    # induced edges between fields if any recipe references (dep -> out)
    for (u, v, d) in G.edges(data=True):
        if u[0] == "R" and v[0] == "F":
            # u is recipe(out,i), v is dep field; add dep -> out for layout
            out_field = ("F", u[1])
            dep_field = v
            field_sub.add_edge(dep_field, out_field)

 
    try:
        from networkx.drawing.nx_agraph import graphviz_layout
        posF = graphviz_layout(field_sub, prog="dot")
        # import pdb; pdb.set_trace()
    except ImportError:
        posF = nx.kamada_kawai_layout(field_sub)


    # # de-overlap exact collisions (dot sometimes stacks)
    # buckets = {}
    # for n, (x, y) in posF.items():
    #     key = (round(float(x), 6), round(float(y), 6))
    #     buckets.setdefault(key, []).append(n)
    # eps = 25.0
    # for (x, y), nodes in buckets.items():
    #     if len(nodes) > 1:
    #         for j, n in enumerate(nodes):
    #             posF[n] = (x, y + (j - (len(nodes)-1)/2.0) * eps)

    # ordinal_levels = True
    # if ordinal_levels:
    #     levels = field_ordinal_levels(comp_graph, direction="out_to_dep")
    #     for n, (x, y) in posF.items():          # n is ("F", field)
    #         f = n[1]
    #         if f in levels:
    #             posF[n] = (x, -levels[f])      # ordinal rows

    # full positions: start with fields
    pos = dict(posF)

    # place recipe nodes on a ring around the output field
    ring_r = 0.08
    ring_r = 30
    for out, recipes in comp_graph.recipes.items():
        f_out = ("F", out)
        if f_out not in pos:
            continue

        x0, y0 = pos[f_out]
        n = len(recipes)
        if n == 0:
            continue

        for i in range(n):
            r_node = ("R", out, i)
            angle = 2.0 * np.pi * i / n
            angle += np.pi / 2.0  
            pos[r_node] = (
                x0 + ring_r * np.cos(angle),
                y0 + ring_r * np.sin(angle),
            )
    # --- colors per recipe ---
    color_cycle = itertools.cycle(plt.cm.tab10.colors)
    recipe_color = {}
    for r in recipe_nodes:
        recipe_color[r] = next(color_cycle)


    # recipe nodes grouped by color (so each group gets its color)
    for r in recipe_nodes:
        nx.draw_networkx_nodes(
            G, pos,
            nodelist=[r],
            node_shape="o",
            node_size=450,
            # edgecolors="black",
            node_color=[recipe_color[r]],
            ax=ax
        )
    recipe_labels = {n: G.nodes[n]["label"] for n in recipe_nodes}
    nx.draw_networkx_labels(G, pos, labels=recipe_labels, font_size=8, ax=ax, font_color='white')

    # --- draw nodes ---
    nx.draw_networkx_nodes(
        G, pos,
        nodelist=field_nodes,
        node_shape="o",
        node_size=1600,
        node_color="lightgray",
        edgecolors="black",
        ax=ax,
    )

    field_labels = {n: G.nodes[n]["label"] for n in field_nodes}
    nx.draw_networkx_labels(G, pos, labels=field_labels, font_size=10, ax=ax)

    # --- edges ---
    # field -> recipe edges: neutral
    # field -> recipe edges: colored by recipe (same as recipe node)
    for r in recipe_nodes:
        u = ("F", r[1])   # output field node
        v = r            # recipe node
        if G.has_edge(u, v):
            nx.draw_networkx_edges(
                G, pos,
                # edgelist=[(u, v)],
                edgelist=[(v, u)],
                arrows=True, arrowstyle="->", arrowsize=16,
                # arrows=False,
                width=4,
                edge_color=[recipe_color[r]],
                connectionstyle="arc3,rad=0.08",
                min_source_margin=10, min_target_margin=20,
                ax=ax
            )

    # recipe -> dep edges: colored by recipe
    for r in recipe_nodes:
        req_edges = [(v, u) for (u, v, d) in G.out_edges(r, data=True)
                    if d.get("kind") == "req"]  # <-- flipped
        if req_edges:
            nx.draw_networkx_edges(
                G, pos,
                edgelist=req_edges,
                arrows=True, arrowstyle="->", arrowsize=16,
                # arrows=False,
                width=2.2,
                edge_color=[recipe_color[r]],
                connectionstyle="arc3,rad=0.18",
                min_source_margin=20, min_target_margin=10,
                ax=ax
            )
    ax.set_title(title)
    ax.axis("off")
    return G, pos
