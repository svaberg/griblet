import pytest

from griblet import Graph, NoPathError
from griblet.loader import BaseLoader, BlockLoader
from griblet.path import Path, Step
from griblet.pathfinder import Pathfinder


class DemoLoader(BaseLoader):
    def __init__(self):
        super().__init__()
        self._fields = {"x": 2, "y": 3}

    def cost(self, field):
        return 7.5


def test_top_level_public_api_exports_expected_symbols():
    assert Graph is not None
    assert NoPathError is not None


def test_pathfinder_returns_path():
    graph = Graph()
    graph.add("x", lambda: 2, cost=1.0)
    graph.add("y", lambda x: x + 1, needs=["x"], cost=2.0)

    path = Pathfinder(graph).find_path("y")

    assert isinstance(path, Path)
    assert isinstance(path.root, Step)
    assert path.cost == pytest.approx(3.0)
    assert path.root.cost == pytest.approx(2.0)
    assert graph.compute("y") == 3


def test_pathfinder_raises_keyerror_for_missing_targets():
    with pytest.raises(KeyError, match="missing"):
        Pathfinder(Graph()).find_path("missing")


def test_graph_compute_raises_keyerror_for_missing_targets():
    with pytest.raises(KeyError, match="missing"):
        Graph().compute("missing")


def test_base_loader_as_graph_uses_dynamic_cost_by_default():
    graph = DemoLoader().as_graph()

    path = Pathfinder(graph).find_path("x")

    assert path.cost == pytest.approx(7.5)
    assert graph.compute("x") == 2


def test_base_loader_as_graph_supports_fixed_cost_override():
    graph = DemoLoader().as_graph(cost=1.25)

    path = Pathfinder(graph).find_path("x")

    assert path.cost == pytest.approx(1.25)
    assert graph.compute("x") == 2


def test_block_loader_exports_work_as_a_graph():
    graph = BlockLoader({"x": 4, "y": 5}, load_cost=3.0, cached_cost=0.2).as_graph()

    path = Pathfinder(graph).find_path("x")

    assert path.cost == pytest.approx(3.0)
    assert graph.compute("x") == 4
