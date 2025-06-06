import networkx as nx


def graph_to_networkx(computation_graph):
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

import networkx as nx

def plot_computation_graph(
    computation_graph,
    ax,
    title="Computation Graph Network",
    show_node_metadata=True,
    pos=None
):
    """
    Plot the computation graph on a matplotlib axis, showing all node costs/metadata.
    Edges are unlabelled (dependencies only).
    Args:
        computation_graph: your ComputationGraph object
        ax: matplotlib.axes.Axes
        title: plot title
        show_node_metadata: include recipe costs and metadata in node labels
        pos: dict of node positions (optional)
    """
    DG = graph_to_networkx(computation_graph)

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
