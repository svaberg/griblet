import networkx as nx
import matplotlib.pyplot as plt
import logging
import pytest
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('matplotlib').setLevel(logging.WARNING)

from griblet import Graph, NoPathError
from griblet.pathfinder import Pathfinder

import plots

_figsize=(12, 9)


def compute_costs_and_paths(graph, fields):
    costs = {}
    paths = {}
    for name in fields:
        try:
            cost, path = Pathfinder(graph).find_path(name)
            costs[name] = cost
            paths[name] = path
            print(name, cost)
        except NoPathError as e:
            print(f"Cannot resolve field '{name}': {e}")
    return costs, paths
    

def plot_networkx_graph(loader, ways_graph, filename):

    loader_graph = loader.as_graph()
    graph = Graph(loader_graph)
    
    print(graph)
    fig, ax = plt.subplots(figsize=_figsize)
    plots.plot_and_or_graph(graph, ax=ax)
    plt.savefig(filename + "_loader.png", dpi=150)

    graph.merge(ways_graph)
    print(graph)
    fig, ax = plt.subplots(figsize=_figsize)
    plots.plot_and_or_graph(graph, ax=ax)
    plt.savefig(filename + "_with_recipes.png", dpi=150)

    try:
        cost1, path1 = Pathfinder(graph).find_path("volume")

        graph.ways.pop("area", None)
        cost2, path2 = Pathfinder(graph).find_path("volume")

        fig, ax = plt.subplots(figsize=_figsize)
        plots.plot_computation_paths(
            graph,
            [path1, path2],
            ax=ax,
            labels=["Best path", "Path after removing area"],
            title="Optimal computation paths before and after removing 'area'"
        )
        fig.tight_layout()
        fig.savefig(filename + "_computation_paths.png", dpi=150)
    except NoPathError as e:
        print(f"Error during pathfinding: {e}")

    
    fields = graph.fields()
    print(f"Fields in graph: {fields}")

    costs, paths = compute_costs_and_paths(graph, fields)
    for name, cost in costs.items():
        print(f"{name}: {cost:.2f}")

    # # Print in order of increasing cost
    # print("\nFields sorted by cost:")
    # for field in sorted(costs, key=costs.get):
    #     print(f"{field}: {costs[field]:.2f}")

    # Print in order of alphabetical field name
    print("\nFields sorted alphabetically:")
    for field in sorted(costs):
        print(f"{field}: {costs[field]:.2f}")


def test_demo_networkx_generates_expected_artifacts(tmp_path):
    output_prefix = tmp_path / "demo_networkx.png"
    from room_demo import make_room_graph, RoomLoader

    plot_networkx_graph(RoomLoader(), make_room_graph(), str(output_prefix))

    assert (tmp_path / "demo_networkx.png_loader.png").exists()
    assert (tmp_path / "demo_networkx.png_with_recipes.png").exists()
    assert (tmp_path / "demo_networkx.png_computation_paths.png").exists()




if __name__ == "__main__":

    # from examples.room_demo import RoomLoader
    from room_demo import make_room_graph, RoomLoader
    loader = RoomLoader()
    room_graph = make_room_graph()
    plot_networkx_graph(loader, room_graph, "demo_networkx.png")


    # from demo_batsrus import make_wind_graph, WindLoader
    # loader = WindLoader()
    # wind_graph = make_wind_graph()
    # plot_networkx_graph(loader, wind_graph, "demo_batsrus_networkx.png")
