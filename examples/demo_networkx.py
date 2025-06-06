import networkx as nx
import matplotlib.pyplot as plt

from griblet.computation_graph import ComputationGraph
from griblet.dependency_solver import DependencySolver, PenaltyDependencySolver
from griblet.field_cache import FieldCache

from room_demo import make_room_graph, RoomLoader


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


if __name__ == "__main__":

    computation_graph = ComputationGraph()

    room_loader = RoomLoader()

    field_cache = FieldCache(room_loader)

    # Add the fields that the loader provides directly
    for field in room_loader.fields():
        computation_graph.add_recipe(
            field, 
            lambda field=field: field_cache.get(field),
            cost=lambda field=field: field_cache.cost(field),
            metadata={'description': f'{field} (from file)'}
        )

    computation_graph = make_room_graph(computation_graph)

    DG = graph_to_networkx(computation_graph)

    # Compute first optimal subtree
    solver = DependencySolver(computation_graph)
    _, tree = solver.resolve_field('volume')
    nodes1, edges1 = get_subtree_nodes_edges(tree)

    # Remove 'area' and compute new optimal subtree
    # g.recipes.pop('area', None)
    solver2 = DependencySolver(computation_graph)
    _, tree2 = solver2.resolve_field('volume')
    nodes2, edges2 = get_subtree_nodes_edges(tree2)

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

    pos = nx.spring_layout(DG)
    plt.figure(figsize=(8, 6))
    nx.draw(DG, pos,
            with_labels=True,
            node_color=node_colors,
            edge_color=edge_colors,
            node_size=1200,
            font_size=11,
            arrowsize=20,
            width=2)
    # Legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label='First path', markerfacecolor='royalblue', markersize=12),
        Line2D([0], [0], marker='o', color='w', label='Second path (after removing area)', markerfacecolor='tomato', markersize=12),
        Line2D([0], [0], marker='o', color='w', label='Unused', markerfacecolor='lightgray', markersize=12),
    ]
    plt.legend(handles=legend_elements, loc='upper left')
    plt.title("Optimal computation paths before and after removing 'area'")
    plt.tight_layout()
    plt.show()
