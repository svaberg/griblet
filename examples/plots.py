import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


def flattened_dependency_graph(computation_graph):
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


def plot_flattened_computation_graph(
    computation_graph,
    ax,
    title="Computation Graph Network",
    show_node_metadata=True,
    pos=None
):
    """
    Plot a 'flattened' view of the computation graph: 
    all possible dependency edges are shown, ignoring recipes.
    Plot the computation graph on a matplotlib axis, showing all node costs/metadata.
    Edges are unlabelled (dependencies only).
    Args:
        computation_graph: your ComputationGraph object
        ax: matplotlib.axes.Axes
        title: plot title
        show_node_metadata: include recipe costs and metadata in node labels
        pos: dict of node positions (optional)
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


import matplotlib.pyplot as plt
import networkx as nx

def plot_recipe_colored_edges(computation_graph, ax, node_pos=None):
    """
    Plot all dependency edges in the graph, 
    coloring each set by recipe (per node).
    """
    DG = nx.DiGraph()
    # Add all nodes first
    for node in computation_graph.recipes.keys():
        DG.add_node(node)
    # Layout
    if node_pos is None:
        node_pos = nx.spring_layout(DG, seed=42)

    # Assign a unique color to each recipe of each node
    import itertools
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
    import itertools
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


import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import itertools

def plot_computation_paths(
    computation_graph,
    trees,
    ax,
    labels=None,
    colors=None,
    title="Computation Paths",
    node_size=1200,
    font_size=11
):
    """
    Plot multiple computation trees as colored, curved arrows on top of the flattened dependency graph.

    computation_graph: ComputationGraph object (with .recipes)
    trees: list of computation tree roots (e.g., from DependencySolver.resolve_field)
    ax: matplotlib axis to draw on
    labels: list of labels for legend (optional)
    colors: list of colors (optional)
    """
    # Build flattened dependency graph
    DG = nx.DiGraph()
    for node, recipes in computation_graph.recipes.items():
        for recipe in recipes:
            for dep in recipe['deps']:
                DG.add_edge(dep, node)
    # Compute layout
    pos = nx.spring_layout(DG, seed=42)

    # Collect union of all nodes/edges in any tree
    all_tree_nodes = set()
    all_tree_edges = set()
    def collect_subtree_nodes_edges(tree):
        nodes = set()
        edges = set()
        def visit(node):
            nodes.add(node.field)
            for dep in getattr(node, "deps", []):
                edges.add((dep.field, node.field))
                visit(dep)
        visit(tree)
        return nodes, edges

    # Process all trees: get per-tree nodes/edges
    trees_nodes_edges = [collect_subtree_nodes_edges(t) for t in trees]
    for nodes, edges in trees_nodes_edges:
        all_tree_nodes.update(nodes)
        all_tree_edges.update(edges)

    # Draw all nodes in lightgray, to show the union graph background
    nx.draw_networkx_nodes(DG, pos, node_color="lightgray", node_size=node_size, ax=ax, edgecolors="black")
    nx.draw_networkx_labels(DG, pos, font_size=font_size, font_weight="bold", ax=ax)

    # Draw all possible edges in lightgray (flattened)
    nx.draw_networkx_edges(DG, pos, edgelist=DG.edges, edge_color="lightgray", width=2, arrows=True, arrowstyle="->", ax=ax)

    # Prepare colors, labels
    if colors is None:
        color_palette = itertools.cycle(plt.cm.tab10.colors)
        colors = [next(color_palette) for _ in trees]
    if labels is None:
        labels = [f"Path {i+1}" for i in range(len(trees))]

    rad_vals = [-0.3, 0.3, 0.6, -0.6, 0.9, -0.9, 0.1, -0.1]
    legend_elements = [Line2D([0], [0], marker='o', color='w', label='All possible dependencies',
                              markerfacecolor='lightgray', markersize=12)]
    # Draw each tree's edges in its own color/curve
    for i, ((nodes, edges), color, label) in enumerate(zip(trees_nodes_edges, colors, labels)):
        rad = rad_vals[i % len(rad_vals)]
        nx.draw_networkx_edges(
            DG, pos, edgelist=edges,
            edge_color=color, width=3, ax=ax,
            arrows=True, arrowstyle="->", arrowsize=26,
            connectionstyle=f"arc3,rad={rad}"
        )
        legend_elements.append(Line2D([0], [0], color=color, lw=3, label=label))

    # Highlight tree nodes (optional: only those in any tree) with white faces, colored border
    nx.draw_networkx_nodes(DG, pos, nodelist=list(all_tree_nodes), node_color="white",
                           node_size=node_size, edgecolors="black", linewidths=3, ax=ax)

    ax.legend(handles=legend_elements, loc="upper left")
    ax.set_title(title)
    ax.axis("off")
