from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pytest

from griblet import ComputationGraph, DependencySolver, UnresolvableFieldError, evaluate_tree

from batsrus_demo import WindLoader, make_wind_recipes_graph
from demo_networkx import plot_networkx_graph
from room_demo import RoomLoader, make_room_recipes_graph, ureg
import plots


def make_room_graph():
    graph = ComputationGraph(RoomLoader().as_graph())
    graph.merge(make_room_recipes_graph())
    return graph


def test_demo_dependency_solver_flow():
    graph = make_room_graph()

    solver = DependencySolver(graph)
    cost, tree = solver.resolve_field("volume")

    value = evaluate_tree(tree, graph)
    value_second = evaluate_tree(tree, graph)

    assert cost == pytest.approx(2.2)
    assert value.to(ureg.meter**3).magnitude == pytest.approx([60.0])
    assert value_second.to(ureg.meter**3).magnitude == pytest.approx([60.0])


def test_demo_rerouting_flow():
    graph = make_room_graph()

    solver = DependencySolver(graph)
    cost_1, tree_1 = solver.resolve_field("volume")
    value_1 = evaluate_tree(tree_1, graph)

    graph.recipes.pop("area", None)
    solver = DependencySolver(graph)
    cost_2, tree_2 = solver.resolve_field("volume")
    value_2 = evaluate_tree(tree_2, graph)

    graph.recipes.pop("length", None)
    solver = DependencySolver(graph)

    assert value_1.to(ureg.meter**3).magnitude == pytest.approx([60.0])
    assert value_2.to(ureg.meter**3).magnitude == pytest.approx([60.0])
    assert cost_2 > cost_1

    with pytest.raises(UnresolvableFieldError):
        solver.resolve_field("volume")


def test_batsrus_example_flow_resolves_and_evaluates():
    graph = ComputationGraph(WindLoader().as_graph())
    graph.merge(make_wind_recipes_graph())

    solver = DependencySolver(graph)
    cost, tree = solver.resolve_field("T ideal (K)")
    value = evaluate_tree(tree, graph)

    assert cost > 0
    assert value.shape == (10,)
    assert np.all(np.isfinite(value))


def test_plot_helpers_render_room_graph():
    graph = make_room_graph()
    solver = DependencySolver(graph)
    _, tree = solver.resolve_field("volume")

    fig, ax = plt.subplots()
    plots.plot_flattened_computation_graph(graph, ax=ax)
    assert ax.has_data()
    plt.close(fig)

    fig, ax = plt.subplots()
    plots.plot_computation_paths(graph, [tree], ax=ax)
    assert ax.has_data()
    plt.close(fig)

    fig, ax = plt.subplots()
    andor_graph, pos = plots.plot_and_or_graph(graph, ax=ax)
    assert andor_graph.number_of_nodes() > 0
    assert pos
    plt.close(fig)


def test_demo_networkx_generates_expected_artifacts(tmp_path):
    output_prefix = tmp_path / "demo_networkx.png"

    plot_networkx_graph(RoomLoader(), make_room_recipes_graph(), str(output_prefix))

    assert (tmp_path / "demo_networkx.png_loader.png").exists()
    assert (tmp_path / "demo_networkx.png_with_recipes.png").exists()
    assert (tmp_path / "demo_networkx.png_computation_paths.png").exists()
