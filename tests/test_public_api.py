import pytest

from griblet import (
    BaseLoader,
    ComputationGraph,
    ComputationTreeNode,
    UnresolvableFieldError,
)
from griblet.loader import BlockLoader


class DemoLoader(BaseLoader):
    def __init__(self):
        super().__init__()
        self._fields = {"x": 2, "y": 3}

    def cost(self, field):
        return 7.5


def test_top_level_public_api_exports_expected_symbols():
    assert BaseLoader is not None
    assert ComputationGraph is not None
    assert ComputationTreeNode is not None
    assert UnresolvableFieldError is not None


def test_graph_plan_returns_public_tree_type():
    graph = ComputationGraph()
    graph.add_recipe("x", lambda: 2, deps=[], cost=1.0)
    graph.add_recipe("y", lambda x: x + 1, deps=["x"], cost=2.0)

    cost, tree = graph.plan("y")

    assert cost == pytest.approx(3.0)
    assert isinstance(tree, ComputationTreeNode)
    assert graph.compute("y") == 3


def test_graph_plan_raises_for_unresolvable_targets():
    with pytest.raises(UnresolvableFieldError):
        ComputationGraph().plan("missing")


def test_base_loader_as_graph_uses_dynamic_cost_by_default():
    graph = DemoLoader().as_graph()

    cost, tree = graph.plan("x")

    assert cost == pytest.approx(7.5)
    assert graph.compute("x") == 2


def test_base_loader_as_graph_supports_fixed_cost_override():
    graph = DemoLoader().as_graph(cost=1.25)

    cost, tree = graph.plan("x")

    assert cost == pytest.approx(1.25)
    assert graph.compute("x") == 2


def test_block_loader_exports_work_as_a_graph():
    graph = BlockLoader({"x": 4, "y": 5}, load_cost=3.0, cached_cost=0.2).as_graph()

    cost, tree = graph.plan("x")

    assert cost == pytest.approx(3.0)
    assert graph.compute("x") == 4
