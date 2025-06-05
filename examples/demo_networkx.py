import networkx as nx
import matplotlib.pyplot as plt

from demo_room_graph import make_room_graph
from griblet.dependency_solver import DependencySolver

def graph_to_networkx(g):
    DG = nx.DiGraph()
    for node, recipes in g.recipes.items():
        for recipe in recipes:
            for dep in recipe['deps']:
                DG.add_edge(dep, node)
    return DG

def get_subtree_nodes_edges(tree):
    """Return sets of nodes and edges in the computation subtree."""
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
    g, cache = make_room_graph()
    DG = graph_to_networkx(g)

    # Get optimal subtree for 'volume'
    solver = DependencySolver(g)
    _, tree = solver.resolve_field('volume')
    sub_nodes, sub_edges = get_subtree_nodes_edges(tree)

    # Assign colors
    node_colors = []
    for n in DG.nodes:
        if n in sub_nodes:
            node_colors.append("tomato")  # or "red"
        else:
            node_colors.append("lightgray")

    edge_colors = []
    for u, v in DG.edges:
        if (u, v) in sub_edges:
            edge_colors.append("tomato")  # or "red"
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
    plt.title("Computation Graph: Optimal Subtree Highlighted")
    plt.tight_layout()
    plt.show()
