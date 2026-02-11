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
    dependency_graph = nx.DiGraph()
    # Add all fields as nodes first
    for recipe in computation_graph.recipes:
        dependency_graph.add_node(recipe)
    # Add edges for all recipes with dependencies
    for output, recipe_list in computation_graph.recipes.items():
        for recipe in recipe_list:
            for dep in recipe['deps']:
                dependency_graph.add_edge(dep, output)
    return dependency_graph


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
    digraph = flattened_dependency_graph(computation_graph)

    # Build node labels with all recipes and their costs/metadata
    if show_node_metadata:
        node_labels = {}
        for n in digraph.nodes:
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
    digraph = flattened_dependency_graph(computation_graph)
    # DG = nx.DiGraph()
    # for node, recipes in computation_graph.recipes.items():
    #     for recipe in recipes:
    #         for dep in recipe['deps']:
    #             DG.add_edge(dep, node)
    # Compute layout
    pos = nx.spring_layout(digraph, seed=42)

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
    nx.draw_networkx_nodes(digraph, pos, node_color="lightgray", node_size=node_size, ax=ax)
    nx.draw_networkx_labels(digraph, pos, font_size=font_size, ax=ax)
    nx.draw_networkx_edges(digraph, pos, edgelist=digraph.edges, edge_color="gray", 
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
            digraph, pos, edgelist=edges,
            edge_color=color, width=3, ax=ax,
            arrows=True, arrowstyle="->", arrowsize=26,
            connectionstyle=f"arc3,rad={rad}"
        )
        legend_elements.append(Line2D([0], [0], color=color, lw=3, label=label))

    # Highlight tree nodes (optional: only those in any tree) with white faces, colored border
    nx.draw_networkx_nodes(digraph, pos, nodelist=list(all_tree_nodes), node_color="white",
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
    andor_graph = nx.DiGraph()

    for out, recipes in computation_graph.recipes.items():
        f_out = ("F", out)
        andor_graph.add_node(f_out, kind="field", field=out)

        for i, r in enumerate(recipes):
            r_node = ("R", out, i)
            andor_graph.add_node(
                r_node,
                kind="recipe",
                out=out,
                idx=i,
                metadata=r.get("metadata", {}),
            )
            andor_graph.add_edge(f_out, r_node)

            for dep in r["deps"]:
                f_dep = ("F", dep)
                andor_graph.add_node(f_dep, kind="field", field=dep)
                andor_graph.add_edge(r_node, f_dep)

    return andor_graph


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


def plot_and_or_graph(comp_graph, ax, title="Computation graph"):
    """
    Full AND–OR structure with recipes as small round nodes near their output field.
      - field nodes: larger circles
      - recipe nodes: smaller circles, colored per recipe
      - recipe color applies to the recipe node and its outgoing edges (deps)
    """

    # --- build explicit AND–OR graph ---
    andor_graph = nx.DiGraph()
    field_nodes = set()
    recipe_nodes = []

    for out, recipes in comp_graph.recipes.items():
        f_out = ("F", out)
        andor_graph.add_node(f_out, kind="field", label=str(out))
        field_nodes.add(f_out)

        for i, r in enumerate(recipes):
            if not r["deps"]:
                continue   # Skip loader recipes (no dependencies, no edges)
            r_node = ("R", out, i)
            andor_graph.add_node(r_node, kind="recipe", out=out, idx=i, label=f"{i+1}")
            recipe_nodes.append(r_node)

            # OR edge: field -> recipe
            andor_graph.add_edge(f_out, r_node, kind="alt")

            # AND edges: recipe -> deps
            for dep in r["deps"]:
                f_dep = ("F", dep)
                andor_graph.add_node(f_dep, kind="field", label=str(dep))
                field_nodes.add(f_dep)
                andor_graph.add_edge(r_node, f_dep, kind="req")

    field_nodes = list(field_nodes)

    # --- layout only the FIELD subgraph (min crossings), then pin recipes near outputs ---
    field_sub = nx.DiGraph()
    field_sub.add_nodes_from(field_nodes)
    # induced edges between fields if any recipe references (dep -> out)
    for (u, v, d) in andor_graph.edges(data=True):
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
    pos = dict(posF)

    #
    # place recipe nodes on a ring around the output field
    #
    ring_r = 0.08
    ring_r = 30
    for out, recipes in comp_graph.recipes.items():
        import pdb; pdb.set_trace()
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
    # for r in recipe_nodes:
    #     recipe_color[r] = next(color_cycle)
    for out in sorted(comp_graph.recipes.keys(), key=str):
        for i, r in enumerate(comp_graph.recipes[out]):
            if not r["deps"]:
                continue
            recipe_color[("R", out, i)] = next(color_cycle)


    # recipe nodes grouped by color (so each group gets its color)
    for r in recipe_nodes:
        nx.draw_networkx_nodes(
            andor_graph, pos,
            nodelist=[r],
            node_shape="o",
            node_size=450,
            # edgecolors="black",
            node_color=[recipe_color[r]],
            ax=ax
        )
    recipe_labels = {n: andor_graph.nodes[n]["label"] for n in recipe_nodes}
    nx.draw_networkx_labels(andor_graph, pos, labels=recipe_labels, font_size=8, ax=ax, font_color='white')

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
    # field -> recipe edges: colored by recipe (same as recipe node)
    for r in recipe_nodes:
        u = ("F", r[1])   # output field node
        v = r            # recipe node
        if andor_graph.has_edge(u, v):
            nx.draw_networkx_edges(
                andor_graph, pos,
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
        req_edges = [(v, u) for (u, v, d) in andor_graph.out_edges(r, data=True)
                    if d.get("kind") == "req"]  # <-- flipped
        if req_edges:
            nx.draw_networkx_edges(
                andor_graph, pos,
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
    return andor_graph, pos
