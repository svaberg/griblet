import matplotlib.pyplot as plt
import logging

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('matplotlib').setLevel(logging.WARNING)

from griblet import Graph, NoPathError
from griblet.pathfinder import Pathfinder

from room_demo import RoomLoader, make_room_graph
import plots


def plot_networkx_graph(loader, ways_graph, filename):
    loader_graph = loader.as_graph()
    graph = Graph(loader_graph)

    print(graph)
    fig, ax = plt.subplots()
    plots.plot_recipe_colored_edges_curved(graph, ax=ax)
    plt.savefig(filename + "_loader.png", dpi=150)

    graph.merge(ways_graph)
    print(graph)
    fig, ax = plt.subplots()
    plots.plot_recipe_colored_edges_curved(graph, ax=ax)
    plt.savefig(filename + "_with_recipes.png", dpi=150)

    try:
        cost1, path1 = Pathfinder(graph).find_path("volume")

        graph.ways.pop("area", None)
        cost2, path2 = Pathfinder(graph).find_path("volume")

        fig, ax = plt.subplots(figsize=(9, 7))
        plots.plot_computation_paths(
            graph,
            [path1, path2],
            ax=ax,
            labels=["Best path", "Path after removing area"],
            title="Optimal computation paths before and after removing 'area'",
        )
        fig.tight_layout()
        fig.savefig(filename + "_computation_paths.png", dpi=150)
    except NoPathError as e:
        print(f"Error during pathfinding: {e}")


if __name__ == "__main__":
    loader = RoomLoader()
    room_graph = make_room_graph()
    plot_networkx_graph(loader, room_graph, "demo_networkx.png")
