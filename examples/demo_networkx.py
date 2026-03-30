"""Render the box and BATSRUS example graphs as AND/OR diagrams."""

import matplotlib.pyplot as plt
import logging
import math

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('matplotlib').setLevel(logging.WARNING)

from griblet import Graph, NoPathError

from box_demo import BoxLoader, box_graph
from demo_batsrus import WindLoader, make_wind_graph
import plots


def plot_networkx_graph(loader, paths_graph, filename, *, target="volume", reroute_key="area"):
    """Plot a full graph and a rerouted-path comparison for one target."""
    loader_graph = loader.as_graph()
    graph = Graph(loader_graph)

    graph.merge(paths_graph)
    print(graph)
    field_count = len(graph.fields())
    fig_height = max(7.0, 1.8 * math.sqrt(field_count))
    fig_width = max(9.0, fig_height)

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    plots.plot_and_or_graph(graph, ax=ax)
    fig.subplots_adjust(left=0.02, right=0.98, bottom=0.02, top=0.94)
    fig.savefig(filename + "_with_recipes.png", dpi=150)

    try:
        path1 = graph.path(target)

        rerouted_graph = Graph(loader.as_graph())
        rerouted_graph.merge(paths_graph)
        rerouted_graph.paths.pop(reroute_key, None)
        path2 = rerouted_graph.path(target)

        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        plots.plot_computation_paths(
            graph,
            [path1, path2],
            ax=ax,
            labels=["Best path", f"Path after removing {reroute_key}"],
            title=f"Optimal computation paths before and after removing {reroute_key!r}",
        )
        fig.subplots_adjust(left=0.02, right=0.98, bottom=0.02, top=0.94)
        fig.savefig(filename + "_computation_paths.png", dpi=150)
    except NoPathError as e:
        print(f"Error during pathfinding: {e}")


if __name__ == "__main__":
    plot_networkx_graph(BoxLoader(), box_graph(), "demo_networkx", target="volume", reroute_key="area")
    plot_networkx_graph(WindLoader(), make_wind_graph(), "demo_batsrus_networkx", target="Ma (U/c_s)", reroute_key="GAMMA")
