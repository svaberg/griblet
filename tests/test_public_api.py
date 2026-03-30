import logging

import pytest

from griblet import Graph, NoPathError
from griblet.cache import Cache
from griblet.loader import BaseLoader, BlockLoader
from griblet.path import Path
from griblet.pathfinder import Pathfinder


class DemoLoader(BaseLoader):
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


def test_top_level_public_api_exports_expected_symbols():
    assert Graph is not None
    assert NoPathError is not None


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

    assert graph.paths["x"][0]["metadata"] == {"description": "source"}


def test_graph_merge_returns_self_and_keeps_all_ways():
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
    assert path.is_source is True
    assert graph.compute("x") == 2


def test_pathfinder_raises_nopath_for_known_but_unreachable_target():
    graph = Graph()
    graph.add("y", lambda x: x + 1, needs=["x"], cost=1.0)

    with pytest.raises(NoPathError, match="No path to y\\."):
        Pathfinder(graph).find_path("y")


def test_path_str_reports_total_cost_and_tree():
    graph = Graph()
    graph.add("x", lambda: 2, cost=1.0)
    graph.add("y", lambda x: x + 1, needs=["x"], cost=2.0)

    explanation = str(graph.path("y"))

    assert explanation.startswith("Path to y (total cost: 3.0)\n")
    assert "y (cost: 3.0)" in explanation
    assert "x (cost: 1.0) [source]" in explanation


def test_cache_str_reports_loader_costs_and_cached_fields():
    cache = Cache(Graph(), ScalarCacheLoader(), load_cost=9.0, cached_cost=0.5)

    assert str(cache) == "\n".join([
        "Cache",
        "  loader: ScalarCacheLoader",
        "  load cost: 9.0",
        "  cached cost: 0.5",
        "  cached fields: -",
    ])

    cache.load("x")

    assert str(cache).endswith("  cached fields: x")


def test_base_loader_str_lists_fields():
    assert str(DemoLoader()) == "\n".join([
        "DemoLoader",
        "  fields: x, y",
    ])


def test_block_loader_str_reports_state_and_costs():
    loader = BlockLoader({"x": 4, "y": 5}, load_cost=3.0, cached_cost=0.2)

    assert str(loader) == "\n".join([
        "BlockLoader",
        "  fields: x, y",
        "  state: not loaded",
        "  load cost: 3.0",
        "  cached cost: 0.2",
    ])

    loader.load("x")

    assert "  state: loaded" in str(loader)


def test_pathfinder_str_lists_known_fields_and_memo_size():
    graph = Graph()
    graph.add("x", lambda: 2, cost=1.0)
    graph.add("y", lambda x: x + 1, needs=["x"], cost=2.0)
    finder = Pathfinder(graph)

    assert str(finder) == "\n".join([
        "Pathfinder",
        "  fields: x, y",
        "  memoized targets: 0",
    ])

    finder.find_path("y")

    assert "  memoized targets: 2" in str(finder)


def test_graph_compute_logs_compute_and_path_messages(caplog):
    graph = Graph()
    graph.add("x", lambda: 2, cost=1.0)
    graph.add("y", lambda x: x + 1, needs=["x"], cost=2.0)

    with caplog.at_level(logging.DEBUG):
        assert graph.compute("y") == 3

    assert "Computing y" in caplog.text
    assert "Chosen path for y:" in caplog.text
    assert "Found path to y with total cost 3.0" in caplog.text
    assert "Computed y with total cost 3.0" in caplog.text


def test_graph_compute_accepts_a_precomputed_path(caplog):
    graph = Graph()
    graph.add("x", lambda: 2, cost=1.0)
    graph.add("y", lambda x: x + 1, needs=["x"], cost=2.0)
    path = graph.path("y")

    caplog.clear()
    with caplog.at_level(logging.DEBUG):
        assert graph.compute(path) == 3

    assert "Finding path to y" not in caplog.text
    assert "Chosen path for y:" not in caplog.text
    assert "Computing y" in caplog.text


def test_cache_logs_miss_hit_and_bulk_load(caplog):
    cache = Cache(Graph(), BulkCacheLoader(), load_cost=9.0, cached_cost=0.5)

    with caplog.at_level(logging.DEBUG):
        assert cache.load("x") == 1
        assert cache.load("x") == 1

    assert "Cache miss for x" in caplog.text
    assert "Loaded 2 field(s) while fetching x" in caplog.text
    assert "Cache hit for x" in caplog.text


def test_block_loader_logs_block_load(caplog):
    loader = BlockLoader({"x": 4, "y": 5}, load_cost=3.0, cached_cost=0.2)

    with caplog.at_level(logging.DEBUG):
        assert loader.load("x") == {"x": 4, "y": 5}
        assert loader.load("y") == 5

    assert "Loading block for x (2 field(s))" in caplog.text
    assert "Serving y from loaded block" in caplog.text


def test_pathfinder_logs_failed_route_and_missing_path(caplog):
    graph = Graph()
    graph.add("y", lambda x: x + 1, needs=["x"], cost=1.0)

    with caplog.at_level(logging.DEBUG):
        with pytest.raises(NoPathError):
            Pathfinder(graph).find_path("y")

    assert "Trying path 0 for y with needs=('x',) and local cost=1.0" in caplog.text
    assert "Path 0 for y failed at need x" in caplog.text
    assert "No path found to y" in caplog.text


def test_cache_adds_cached_way_after_scalar_load():
    graph = Graph()
    cache = Cache(graph, ScalarCacheLoader(), load_cost=9.0, cached_cost=0.5)

    assert len(graph.paths["x"]) == 1
    assert graph.path("x").cost == pytest.approx(9.0)
    assert cache.load("x") == 7
    assert graph.path("x").cost == pytest.approx(0.5)
    assert cache.loader.calls == 1


def test_cache_bulk_load_adds_cached_ways_for_all_loaded_fields():
    graph = Graph()
    cache = Cache(graph, BulkCacheLoader(), load_cost=9.0, cached_cost=0.5)

    assert cache.load("x") == 1
    assert graph.path("y").cost == pytest.approx(0.5)
    assert cache.load("y") == 2
    assert cache.loader.calls == 1


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
    graph = BlockLoader({"x": 4, "y": 5}, load_cost=3.0, cached_cost=0.2).as_graph()

    path = Pathfinder(graph).find_path("x")

    assert path.cost == pytest.approx(3.0)
    assert graph.compute("x") == 4
    assert graph.path("y").cost == pytest.approx(0.2)
