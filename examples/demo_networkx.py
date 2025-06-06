import networkx as nx
import matplotlib.pyplot as plt

from griblet.computation_graph import ComputationGraph
from griblet.dependency_solver import DependencySolver, PenaltyDependencySolver
from griblet.field_cache import FieldCache

from room_demo import add_room_recipes, RoomLoader
import plots


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
    loader = RoomLoader()

    computation_graph.add_loader_fields(loader)
    print(computation_graph)
    fig, ax = plt.subplots()
    plots.plot_recipe_colored_edges_curved(computation_graph, ax=ax)
    plt.savefig("flattened.png", dpi=150)


    add_room_recipes(computation_graph)
    print(computation_graph)
    fig, ax = plt.subplots()
    plots.plot_recipe_colored_edges_curved(computation_graph, ax=ax)
    plt.savefig("with_recipes.png", dpi=150)

    
    # Use the solver 
    solver = DependencySolver(computation_graph)
    cost1, tree1 = solver.resolve_field('volume')

    # (Optionally) remove 'area' as a recipe or node, then resolve again
    # computation_graph.recipes.pop('area', None)
    solver2 = DependencySolver(computation_graph)
    cost2, tree2 = solver2.resolve_field('volume')

    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(9, 7))
    plots.plot_computation_paths(
        computation_graph,
        [tree1, tree2],  # list of tree roots
        ax=ax,
        labels=["Best path", "Path after removing area"],
        title="Optimal computation paths before and after removing 'area'"
    )
    fig.tight_layout()
    fig.savefig("computation_paths.png", dpi=150)
