import networkx as nx
import matplotlib.pyplot as plt
import logging
import pytest
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('matplotlib').setLevel(logging.WARNING)

from griblet import ComputationGraph
from griblet import DependencySolver
from griblet import UnresolvableFieldError

import plots

_figsize=(12, 9)


def compute_costs_and_trees(solver, fields):
    costs = {}
    trees = {}
    for field in fields:
        try:
            cost, tree = solver.resolve_field(field)
            costs[field] = cost
            trees[field] = tree
            print(field, cost)
        except UnresolvableFieldError as e:
            print(f"Cannot resolve field '{field}': {e}")
    return costs, trees
    

def plot_networkx_graph(loader, recipes_graph, filename):

    loader_graph = loader.as_graph()
    computation_graph = ComputationGraph(loader_graph)
    
    print(computation_graph)
    fig, ax = plt.subplots(figsize=_figsize)
    plots.plot_and_or_graph(computation_graph, ax=ax)
    plt.savefig(filename + "_loader.png", dpi=150)

    computation_graph.merge(recipes_graph)
    print(computation_graph)
    fig, ax = plt.subplots(figsize=_figsize)
    plots.plot_and_or_graph(computation_graph, ax=ax)
    plt.savefig(filename + "_with_recipes.png", dpi=150)

    
    # # Use the solver 
    try:
        solver = DependencySolver(computation_graph)
        cost1, tree1 = solver.resolve_field('volume')

        # (Optionally) remove 'area' as a recipe or node, then resolve again
        computation_graph.recipes.pop('area', None)
        solver2 = DependencySolver(computation_graph)
        cost2, tree2 = solver2.resolve_field('volume')

        fig, ax = plt.subplots(figsize=_figsize)
        plots.plot_computation_paths(
            computation_graph,
            [tree1, tree2],  # list of tree roots
            ax=ax,
            labels=["Best path", "Path after removing area"],
            title="Optimal computation paths before and after removing 'area'"
        )
        fig.tight_layout()
        fig.savefig(filename + "_computation_paths.png", dpi=150)
    except Exception as e:
        print(f"Error during dependency solving: {e}")

    
    fields = computation_graph.list_fields()
    print(f"Fields in graph: {fields}")
    for field in fields:
        computation_graph.describe_field(field)


    costs, trees = compute_costs_and_trees(solver, fields)    
    for field, cost in costs.items():
        print(f"{field}: {cost:.2f}")

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
    from room_demo import make_room_recipes_graph, RoomLoader

    plot_networkx_graph(RoomLoader(), make_room_recipes_graph(), str(output_prefix))

    assert (tmp_path / "demo_networkx.png_loader.png").exists()
    assert (tmp_path / "demo_networkx.png_with_recipes.png").exists()
    assert (tmp_path / "demo_networkx.png_computation_paths.png").exists()




if __name__ == "__main__":

    # from examples.room_demo import RoomLoader
    from room_demo import make_room_recipes_graph, RoomLoader
    loader = RoomLoader()
    room_recipies_graph = make_room_recipes_graph()
    plot_networkx_graph(loader, room_recipies_graph, "demo_networkx.png")


    # from batsrus_demo import make_wind_recipes_graph, WindLoader
    # loader = WindLoader()
    # batsrus_recipes_graph = make_wind_recipes_graph()
    # plot_networkx_graph(loader, batsrus_recipes_graph, "demo_batsrus_networkx.png")
