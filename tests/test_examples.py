import matplotlib.pyplot as plt
import numpy as np
import pytest

from griblet import NoPathError
from griblet import Graph

from demo_batsrus import build_wind_graph
from box_demo import BoxLoader, box_graph, ureg
import plots


def test_demo_best_path_flow():
    graph = Graph()
    graph.merge(BoxLoader().as_graph())
    graph.merge(box_graph())

    path = graph.path("volume")

    value = graph.compute("volume")
    value_second = graph.compute("volume")

    assert path.cost == pytest.approx(22.0)
    assert value.to(ureg.meter**3).magnitude == pytest.approx(60.0)
    assert value_second.to(ureg.meter**3).magnitude == pytest.approx(60.0)


def test_demo_rerouting_flow():
    graph = Graph()
    graph.merge(BoxLoader().as_graph())
    graph.merge(box_graph())

    path_1 = graph.path("volume")
    value_1 = graph.compute("volume")

    graph.paths.pop("area", None)
    path_2 = graph.path("volume")
    value_2 = graph.compute("volume")

    graph.paths.pop("length", None)

    assert value_1.to(ureg.meter**3).magnitude == pytest.approx(60.0)
    assert value_2.to(ureg.meter**3).magnitude == pytest.approx(60.0)
    assert path_2.cost > path_1.cost

    with pytest.raises(NoPathError):
        graph.path("volume")


def test_box_extra_fields():
    graph = Graph()
    graph.merge(BoxLoader().as_graph())
    graph.merge(box_graph())

    base_perimeter = graph.compute("base_perimeter")
    linear_size = graph.compute("linear_size")

    assert base_perimeter.to(ureg.meter).magnitude == pytest.approx(18.0)
    assert linear_size.to(ureg.meter).magnitude == pytest.approx(12.0)


def test_batsrus_example_flow_resolves_and_evaluates():
    graph = build_wind_graph()

    path = graph.path("T ideal (K)")
    value = graph.compute("T ideal (K)")

    assert path.cost > 0
    assert value.shape == (10,)
    assert np.all(np.isfinite(value))


def test_plot_helpers_render_box_graph():
    graph = Graph()
    graph.merge(BoxLoader().as_graph())
    graph.merge(box_graph())
    path = graph.path("volume")

    fig, ax = plt.subplots()
    plots.plot_computation_paths(graph, [path], ax=ax)
    assert ax.has_data()
    plt.close(fig)

    fig, ax = plt.subplots()
    andor_graph, pos = plots.plot_and_or_graph(graph, ax=ax)
    assert andor_graph.number_of_nodes() > 0
    assert pos
    plt.close(fig)
