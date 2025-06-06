import networkx as nx
import matplotlib.pyplot as plt

from griblet.computation_graph import ComputationGraph
from griblet.dependency_solver import DependencySolver, PenaltyDependencySolver
from griblet.field_cache import FieldCache

from room_demo import add_room_recipes, RoomLoader


def graph_to_networkx(g):
    DG = nx.DiGraph()
    for node, recipes in g.recipes.items():
        for recipe in recipes:
            for dep in recipe['deps']:
                DG.add_edge(dep, node)
    return DG


def get_subtree_nodes_edges(tree):
    nodes = set()
    edges = set()
    def visit(node):
        nodes.add(node.field)
        for dep in getattr(node, "deps", []):
            edges.add((dep.field, node.field))
            visit(dep)
    visit(tree)
    return nodes, edges


import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

def plot_computation_paths(
    DG,
    nodes1, edges1,
    nodes2, edges2,
    out_path,
    title="Optimal computation paths before and after removing 'area'",
    pos=None
):
    """
    DG: networkx.DiGraph
    nodes1, edges1: nodes/edges of first path (highlighted blue)
    nodes2, edges2: nodes/edges of second path (highlighted tomato/red)
    out_path: filename for the PNG
    pos: node positions (optional; will generate with spring_layout if None)
    """

    # Node coloring: priority is rerouted (red), then original (blue), else gray
    node_colors = []
    for n in DG.nodes:
        if n in nodes2:
            node_colors.append("tomato")  # rerouted
        elif n in nodes1:
            node_colors.append("royalblue")  # original
        else:
            node_colors.append("lightgray")

    # Edge coloring: same logic
    edge_colors = []
    for u, v in DG.edges:
        if (u, v) in edges2:
            edge_colors.append("tomato")
        elif (u, v) in edges1:
            edge_colors.append("royalblue")
        else:
            edge_colors.append("lightgray")

    if pos is None:
        pos = nx.spring_layout(DG, seed=42)  # deterministic

    plt.figure(figsize=(8, 6))
    nx.draw(
        DG, pos,
        with_labels=True,
        node_color=node_colors,
        edge_color=edge_colors,
        node_size=1200,
        font_size=11,
        arrowsize=20,
        width=2,
    )
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label='First path', markerfacecolor='royalblue', markersize=12),
        Line2D([0], [0], marker='o', color='w', label='Second path (after removing area)', markerfacecolor='tomato', markersize=12),
        Line2D([0], [0], marker='o', color='w', label='Unused', markerfacecolor='lightgray', markersize=12),
    ]
    plt.legend(handles=legend_elements, loc='upper left')
    plt.title(title)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


import networkx as nx
import matplotlib.pyplot as plt

# def plot_computation_graph(
#     computation_graph,
#     out_path,
#     title="Computation Graph Network",
#     show_edge_costs=True,
#     show_node_metadata=True,
#     pos=None
# ):
#     """
#     Plots and saves the computation graph with node/edge metadata where possible.
    
#     Args:
#         computation_graph: your ComputationGraph object
#         out_path: output filename
#         title: plot title
#         show_edge_costs: show edge cost in labels
#         show_node_metadata: show node metadata (desc/unit)
#         pos: node positions (optional, for consistent layout)
#     """
#     DG = graph_to_networkx(computation_graph)

#     # Try to gather metadata
#     field_metadata = {}
#     # Try to get metadata from computation_graph, fallback to empty
#     for field in DG.nodes:
#         meta = None
#         try:
#             # Some implementations may have .metadata or .field_metadata
#             meta = computation_graph.field_metadata[field]
#         except Exception:
#             try:
#                 meta = computation_graph.metadata[field]
#             except Exception:
#                 pass
#         field_metadata[field] = meta

#     if show_node_metadata:
#         node_labels = {}
#         for n in DG.nodes:
#             meta = field_metadata.get(n)
#             if meta:
#                 desc = meta.get("description", "")
#                 unit = meta.get("unit", "")
#                 lines = [str(n)]
#                 if desc: lines.append(str(desc))
#                 if unit: lines.append(f"[{unit}]")
#                 node_labels[n] = "\n".join(lines)
#             else:
#                 node_labels[n] = str(n)
#     else:
#         node_labels = {n: str(n) for n in DG.nodes}

#     # Edge metadata (show cost if available)
#     edge_labels = {}
#     if show_edge_costs:
#         for u, v in DG.edges:
#             rec = None
#             # recipes.values() is likely a list of lists!
#             for recipe_list in computation_graph.recipes.values():
#                 for r in (recipe_list if isinstance(recipe_list, list) else [recipe_list]):
#                     if getattr(r, 'output', None) == u and v in getattr(r, 'deps', []):
#                         rec = r
#                         break
#                 if rec:
#                     break
#             if rec:
#                 label = ""
#                 if hasattr(rec, 'cost'):
#                     label += f"cost: {rec.cost}"
#                 if hasattr(rec, 'metadata') and rec.metadata:
#                     desc = rec.metadata.get('description')
#                     if desc:
#                         label = f"{desc}\n{label}" if label else desc
#                 edge_labels[(u, v)] = label
#             else:
#                 edge_labels[(u, v)] = ""
#     else:
#         edge_labels = {}

#     if pos is None:
#         pos = nx.spring_layout(DG, seed=42)

#     plt.figure(figsize=(10, 7))
#     nx.draw_networkx_nodes(DG, pos, node_color="skyblue", node_size=1500)
#     nx.draw_networkx_edges(DG, pos, arrowstyle="->", arrowsize=20, width=2, edge_color="gray")
#     nx.draw_networkx_labels(DG, pos, labels=node_labels, font_size=10, font_weight="bold")
#     if edge_labels:
#         nx.draw_networkx_edge_labels(DG, pos, edge_labels=edge_labels, font_size=9)

#     plt.title(title)
#     plt.axis("off")
#     plt.tight_layout()
#     plt.savefig(out_path, dpi=150)
#     plt.close()

import plots



if __name__ == "__main__":
    computation_graph = ComputationGraph()
    loader = RoomLoader()
    field_cache = FieldCache(loader)
    computation_graph.add_loader_fields(loader, field_cache)
    print(computation_graph)
    fig, ax = plt.subplots()
    plots.plot_computation_graph(computation_graph, ax=ax)
    plt.savefig("initial_graph.png", dpi=150)
    add_room_recipes(computation_graph)
    fig, ax = plt.subplots()
    plots.plot_computation_graph(computation_graph, ax=ax)
    plt.savefig("with_recipes.png", dpi=150)
    print(computation_graph)
    


    DG = graph_to_networkx(computation_graph)
    solver = DependencySolver(computation_graph)
    _, tree = solver.resolve_field('volume')
    nodes1, edges1 = get_subtree_nodes_edges(tree)

    # Remove 'area' and compute new optimal subtree
    # computation_graph.recipes.pop('area', None)
    solver2 = DependencySolver(computation_graph)
    _, tree2 = solver2.resolve_field('volume')
    nodes2, edges2 = get_subtree_nodes_edges(tree2)

    # Save to file
    plot_computation_paths(
        DG,
        nodes1, edges1,
        nodes2, edges2,
        out_path="computation_paths.png"
    )


# if __name__ == "__main__":

#     computation_graph = ComputationGraph()

#     loader = RoomLoader()

#     field_cache = FieldCache(loader)

#     # Add the fields that the loader provides directly
#     # Todo this should (?) not require both the cache and the loader
#     computation_graph.add_loader_fields(loader, field_cache)
#     add_room_recipes(computation_graph)

#     DG = graph_to_networkx(computation_graph)

#     # Compute first optimal subtree
#     solver = DependencySolver(computation_graph)
#     _, tree = solver.resolve_field('volume')
#     nodes1, edges1 = get_subtree_nodes_edges(tree)

#     # Remove 'area' and compute new optimal subtree
#     # g.recipes.pop('area', None)
#     solver2 = DependencySolver(computation_graph)
#     _, tree2 = solver2.resolve_field('volume')
#     nodes2, edges2 = get_subtree_nodes_edges(tree2)

#     # Node coloring: priority is rerouted (red), then original (blue), else gray
#     node_colors = []
#     for n in DG.nodes:
#         if n in nodes2:
#             node_colors.append("tomato")  # rerouted
#         elif n in nodes1:
#             node_colors.append("royalblue")  # original
#         else:
#             node_colors.append("lightgray")

#     # Edge coloring: same logic
#     edge_colors = []
#     for u, v in DG.edges:
#         if (u, v) in edges2:
#             edge_colors.append("tomato")
#         elif (u, v) in edges1:
#             edge_colors.append("royalblue")
#         else:
#             edge_colors.append("lightgray")

#     pos = nx.spring_layout(DG)
#     plt.figure(figsize=(8, 6))
#     nx.draw(DG, pos,
#             with_labels=True,
#             node_color=node_colors,
#             edge_color=edge_colors,
#             node_size=1200,
#             font_size=11,
#             arrowsize=20,
#             width=2)
#     # Legend
#     from matplotlib.lines import Line2D
#     legend_elements = [
#         Line2D([0], [0], marker='o', color='w', label='First path', markerfacecolor='royalblue', markersize=12),
#         Line2D([0], [0], marker='o', color='w', label='Second path (after removing area)', markerfacecolor='tomato', markersize=12),
#         Line2D([0], [0], marker='o', color='w', label='Unused', markerfacecolor='lightgray', markersize=12),
#     ]
#     plt.legend(handles=legend_elements, loc='upper left')
#     plt.title("Optimal computation paths before and after removing 'area'")
#     plt.tight_layout()
#     plt.show()
