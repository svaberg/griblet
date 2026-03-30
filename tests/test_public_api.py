import pytest

from griblet import Graph, NoPathError
from griblet.cache import Cache
from griblet.loader import Loader, BlockLoader
from griblet.path import Path
from griblet.pathfinder import Pathfinder


class DemoLoader(Loader):
    def __init__(self):
        super().__init__()
        self._fields = {"x": 2, "y": 3}

    def cost(self, field):
        return 7.5


class ScalarCacheLoader:
    def __init__(self):
        self.calls = 0

    def fields(self):
        return ("x",)

    def load(self, field):
        self.calls += 1
        return 7


class BulkCacheLoader:
    def __init__(self):
        self.calls = 0

    def fields(self):
        return ("x", "y")

    def load(self, field):
        self.calls += 1
        return {"x": 1, "y": 2}


class MissingFieldBulkCacheLoader:
    def fields(self):
        return ("x",)

    def load(self, field):
        return {"y": 2}


def test_graph_constructor_seeds_from_other_graph():
    source = Graph()
    source.add("x", lambda: 2, cost=1.0)

    graph = Graph(source)

    assert graph is not source
    assert graph.fields() == {"x"}
    assert graph.compute("x") == 2


def test_pathfinder_returns_path():
    graph = Graph()
    graph.add("x", lambda: 2, cost=1.0)
    graph.add("y", lambda x: x + 1, needs=["x"], cost=2.0)

    path = Pathfinder(graph).find_path("y")

    assert isinstance(path, Path)
    assert path.cost == pytest.approx(3.0)
    assert graph.compute("y") == 3


def test_graph_path_returns_path():
    graph = Graph()
    graph.add("x", lambda: 2, cost=1.0)
    graph.add("y", lambda x: x + 1, needs=["x"], cost=2.0)

    path = graph.path("y")

    assert isinstance(path, Path)
    assert path.cost == pytest.approx(3.0)
    assert path.name == "y"
    assert not hasattr(path, "_record")


def test_pathfinder_raises_keyerror_for_missing_targets():
    with pytest.raises(KeyError, match="missing"):
        Pathfinder(Graph()).find_path("missing")


def test_graph_compute_raises_keyerror_for_missing_targets():
    with pytest.raises(KeyError, match="missing"):
        Graph().compute("missing")


def test_graph_compute_raises_typeerror_for_invalid_targets():
    with pytest.raises(TypeError, match="field name or a Path"):
        Graph().compute(3)


def test_graph_add_copies_metadata():
    graph = Graph()
    metadata = {"description": "source"}

    graph.add("x", lambda: 1, metadata=metadata)
    metadata["description"] = "mutated"

    assert graph.paths["x"][0].metadata == {"description": "source"}


def test_graph_merge_returns_self_and_keeps_all_steps():
    left = Graph()
    right = Graph()
    left.add("x", lambda: 1, cost=1.0)
    right.add("x", lambda: 2, cost=2.0)

    merged = left.merge(right)

    assert merged is left
    assert len(left.paths["x"]) == 2


def test_graph_fields_only_lists_outputs():
    graph = Graph()
    graph.add("y", lambda x: x + 1, needs=["x"], cost=1.0)

    assert graph.fields() == {"y"}


def test_pathfinder_prefers_lower_total_cost():
    graph = Graph()
    graph.add("x", lambda: 2, cost=5.0)
    graph.add("y", lambda x: x + 1, needs=["x"], cost=1.0)
    graph.add("y", lambda: 3, cost=3.0)

    path = Pathfinder(graph).find_path("y")

    assert path.cost == pytest.approx(3.0)
    assert path.needs == []


def test_pathfinder_avoids_cycle_when_alternative_exists():
    graph = Graph()
    graph.add("x", lambda y: y + 1, needs=["y"], cost=1.0)
    graph.add("y", lambda x: x + 1, needs=["x"], cost=1.0)
    graph.add("x", lambda: 2, cost=5.0)

    path = Pathfinder(graph).find_path("x")

    assert path.cost == pytest.approx(5.0)
    assert path.needs == []
    assert graph.compute("x") == 2


def test_pathfinder_raises_nopath_for_cycle_without_exit():
    graph = Graph()
    graph.add("x", lambda y: y + 1, needs=["y"], cost=1.0)
    graph.add("y", lambda x: x + 1, needs=["x"], cost=1.0)

    with pytest.raises(NoPathError, match="No path to x\\."):
        graph.path("x")


def test_pathfinder_raises_nopath_for_self_cycle():
    graph = Graph()
    graph.add("x", lambda x: x + 1, needs=["x"], cost=1.0)

    with pytest.raises(NoPathError, match="No path to x\\."):
        graph.path("x")


def test_pathfinder_backtracks_from_cyclic_branch_to_valid_path():
    graph = Graph()
    graph.add("y", lambda x: x + 1, needs=["x"], cost=1.0)
    graph.add("x", lambda y: y + 1, needs=["y"], cost=0.1)
    graph.add("x", lambda: 2, cost=5.0)

    path = graph.path("y")

    assert path.cost == pytest.approx(6.0)
    assert graph.compute("y") == 3


def test_pathfinder_raises_nopath_for_known_but_unreachable_target():
    graph = Graph()
    graph.add("y", lambda x: x + 1, needs=["x"], cost=1.0)

    with pytest.raises(NoPathError, match="No path to y\\."):
        Pathfinder(graph).find_path("y")


def test_pathfinder_does_not_poison_later_searches_after_failed_subsearch():
    graph = Graph()
    graph.add("x", lambda y: y + 1, needs=["y"], cost=1.0)
    graph.add("x", lambda: 2, cost=5.0)
    graph.add("y", lambda x: x + 1, needs=["x"], cost=1.0)

    assert graph.path("x").cost == pytest.approx(5.0)
    assert graph.path("y").cost == pytest.approx(6.0)
    assert graph.compute("y") == 3


def test_path_str_reports_total_cost_and_tree():
    graph = Graph()
    graph.add("x", lambda: 2, cost=1.0)
    graph.add("y", lambda x: x + 1, needs=["x"], cost=2.0)

    explanation = str(graph.path("y"))

    assert explanation.startswith("Path to y (total cost: 3.0)\n")
    assert "y (cost: 3.0)" in explanation
    assert "x (cost: 1.0)" in explanation


def test_graph_compute_accepts_a_precomputed_path():
    graph = Graph()
    graph.add("x", lambda: 2, cost=1.0)
    graph.add("y", lambda x: x + 1, needs=["x"], cost=2.0)
    path = graph.path("y")

    assert graph.compute(path) == 3


def test_cache_adds_cached_path_after_scalar_load():
    graph = Graph()
    cache = Cache(graph, ScalarCacheLoader(), load_cost=9.0, cached_cost=0.5)

    assert len(graph.paths["x"]) == 1
    assert graph.path("x").cost == pytest.approx(9.0)
    assert cache.load("x") == 7
    assert graph.path("x").cost == pytest.approx(0.5)
    assert cache.loader.calls == 1


def test_cache_bulk_load_adds_cached_steps_for_all_loaded_fields():
    graph = Graph()
    cache = Cache(graph, BulkCacheLoader(), load_cost=9.0, cached_cost=0.5)

    assert cache.load("x") == 1
    assert graph.path("y").cost == pytest.approx(0.5)
    assert cache.load("y") == 2
    assert cache.loader.calls == 1


def test_cache_bulk_load_raises_keyerror_when_requested_field_is_missing():
    graph = Graph()
    cache = Cache(graph, MissingFieldBulkCacheLoader(), load_cost=9.0, cached_cost=0.5)

    with pytest.raises(KeyError, match="Field x not found in loaded data"):
        cache.load("x")

    assert graph.compute("y") == 2


def test_cache_discard_removes_cached_path_and_forces_reload():
    graph = Graph()
    cache = Cache(graph, ScalarCacheLoader(), load_cost=9.0, cached_cost=0.5)

    assert cache.load("x") == 7
    assert graph.path("x").cost == pytest.approx(0.5)

    cache.discard("x")

    assert len(graph.paths["x"]) == 1
    assert graph.path("x").cost == pytest.approx(9.0)
    assert cache.load("x") == 7
    assert cache.loader.calls == 2


def test_cache_discard_ignores_uncached_fields():
    graph = Graph()
    cache = Cache(graph, ScalarCacheLoader(), load_cost=9.0, cached_cost=0.5)

    cache.discard("x")

    assert graph.path("x").cost == pytest.approx(9.0)
    assert cache.loader.calls == 0


def test_loader_raises_valueerror_for_unknown_fields():
    loader = Loader()
    loader._fields = {"x": 1}

    with pytest.raises(ValueError, match="Field 'missing' not found\\."):
        loader.load("missing")

    with pytest.raises(ValueError, match="Field 'missing' not found\\."):
        loader.cost("missing")


def test_base_loader_as_graph_uses_loader_cost_by_default():
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
    loader = BlockLoader({"x": 4, "y": 5}, load_cost=3.0, cached_cost=0.2)
    graph = loader.as_graph()

    path = Pathfinder(graph).find_path("x")

    assert loader.as_graph() is graph
    assert path.cost == pytest.approx(3.0)
    assert graph.compute("x") == 4
    assert graph.path("y").cost == pytest.approx(0.2)


def test_block_loader_cost_raises_valueerror_for_unknown_fields():
    loader = BlockLoader({"x": 4})

    with pytest.raises(ValueError, match="Field 'missing' not found\\."):
        loader.cost("missing")


def test_block_loader_cost_returns_load_cost_for_known_fields():
    loader = BlockLoader({"x": 4}, load_cost=3.0)

    assert loader.cost("x") == pytest.approx(3.0)


def test_block_loader_as_graph_rejects_conflicting_cost_override():
    loader = BlockLoader({"x": 4}, load_cost=3.0)

    with pytest.raises(ValueError, match="uses the loader's own load_cost"):
        loader.as_graph(cost=1.0)
