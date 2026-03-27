from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pytest

from griblet import Graph, NoPathError
from griblet.pathfinder import Pathfinder

from demo_batsrus import WindLoader, make_wind_graph
from demo_networkx import plot_networkx_graph
from room_demo import RoomLoader, make_room_graph, ureg
import plots


def build_room_graph():
    graph = Graph(RoomLoader().as_graph())
    graph.merge(make_room_graph())
    return graph


def test_demo_best_path_flow():
    graph = build_room_graph()

    cost, path = Pathfinder(graph).find_path("volume")

    value = graph.compute("volume")
    value_second = graph.compute("volume")

    assert cost == pytest.approx(2.2)
    assert value.to(ureg.meter**3).magnitude == pytest.approx([60.0])
    assert value_second.to(ureg.meter**3).magnitude == pytest.approx([60.0])


def test_demo_rerouting_flow():
    graph = build_room_graph()

    cost_1, _path_1 = Pathfinder(graph).find_path("volume")
    value_1 = graph.compute("volume")

    graph.ways.pop("area", None)
    cost_2, _path_2 = Pathfinder(graph).find_path("volume")
    value_2 = graph.compute("volume")

    graph.ways.pop("length", None)

    assert value_1.to(ureg.meter**3).magnitude == pytest.approx([60.0])
    assert value_2.to(ureg.meter**3).magnitude == pytest.approx([60.0])
    assert cost_2 > cost_1

    with pytest.raises(NoPathError):
        Pathfinder(graph).find_path("volume")


def test_batsrus_example_flow_resolves_and_evaluates():
    graph = Graph(WindLoader().as_graph())
    graph.merge(make_wind_graph())

    cost, _path = Pathfinder(graph).find_path("T ideal (K)")
    value = graph.compute("T ideal (K)")

    assert cost > 0
    assert value.shape == (10,)
    assert np.all(np.isfinite(value))


def test_plot_helpers_render_room_graph():
    graph = build_room_graph()
    _, path = Pathfinder(graph).find_path("volume")

    fig, ax = plt.subplots()
    plots.plot_flattened_computation_graph(graph, ax=ax)
    assert ax.has_data()
    plt.close(fig)

    fig, ax = plt.subplots()
    plots.plot_computation_paths(graph, [path], ax=ax)
    assert ax.has_data()
    plt.close(fig)

    fig, ax = plt.subplots()
    andor_graph, pos = plots.plot_and_or_graph(graph, ax=ax)
    assert andor_graph.number_of_nodes() > 0
    assert pos
    plt.close(fig)


def test_demo_networkx_generates_expected_artifacts(tmp_path):
    output_prefix = tmp_path / "demo_networkx.png"

    plot_networkx_graph(RoomLoader(), make_room_graph(), str(output_prefix))

    assert (tmp_path / "demo_networkx.png_loader.png").exists()
    assert (tmp_path / "demo_networkx.png_with_recipes.png").exists()
    assert (tmp_path / "demo_networkx.png_computation_paths.png").exists()
