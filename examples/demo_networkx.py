import networkx as nx
import matplotlib.pyplot as plt
import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('matplotlib').setLevel(logging.WARNING)

from griblet import ComputationGraph
from griblet import DependencySolver

from room_demo import make_room_recipes_graph, RoomLoader
import plots


def plot_networkx_graph(loader, recipes_graph, filename):
    loader_graph = loader.as_graph()
    computation_graph = ComputationGraph(loader_graph)

    print(computation_graph)
    fig, ax = plt.subplots()
    plots.plot_recipe_colored_edges_curved(computation_graph, ax=ax)
    plt.savefig(filename + "_loader.png", dpi=150)

    computation_graph.merge(recipes_graph)
    print(computation_graph)
    fig, ax = plt.subplots()
    plots.plot_recipe_colored_edges_curved(computation_graph, ax=ax)
    plt.savefig(filename + "_with_recipes.png", dpi=150)

    # Use the solver 
    solver = DependencySolver(computation_graph)
    cost1, tree1 = solver.resolve_field('volume')

    # (Optionally) remove 'area' as a recipe or node, then resolve again
    computation_graph.recipes.pop('area', None)
    solver2 = DependencySolver(computation_graph)
    cost2, tree2 = solver2.resolve_field('volume')

    fig, ax = plt.subplots(figsize=(9, 7))
    plots.plot_computation_paths(
        computation_graph,
        [tree1, tree2],  # list of tree roots
        ax=ax,
        labels=["Best path", "Path after removing area"],
        title="Optimal computation paths before and after removing 'area'"
    )
    fig.tight_layout()
    fig.savefig(filename + "_computation_paths.png", dpi=150)


if __name__ == "__main__":
    loader = RoomLoader()
    room_recipies_graph = make_room_recipes_graph()
    plot_networkx_graph(loader, room_recipies_graph, "demo_networkx.png")
