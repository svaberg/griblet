import networkx as nx
import matplotlib.pyplot as plt
import logging
import astropy.units as u
import pytest
logging.basicConfig(level=logging.INFO)

from griblet import Graph, NoPathError
from griblet.pathfinder import Pathfinder

from room_demo import make_room_graph, RoomLoader


def build_graph():
    loader = RoomLoader()
    loader_graph = loader.as_graph()
    graph = Graph(loader_graph)
    graph.merge(make_room_graph())
    return graph


def test_demo_rerouting_flow():
    graph = build_graph()

    cost1, _path1 = Pathfinder(graph).find_path("volume")
    val1 = graph.compute("volume")

    graph.ways.pop("area", None)
    cost2, _path2 = Pathfinder(graph).find_path("volume")
    val2 = graph.compute("volume")

    assert val1.to_value(u.m**3) == pytest.approx([60.0])
    assert val2.to_value(u.m**3) == pytest.approx([60.0])
    assert cost2 > cost1

    graph.ways.pop("length", None)
    with pytest.raises(NoPathError):
        Pathfinder(graph).find_path("volume")


if __name__ == "__main__":
    graph = build_graph()
    
    cost1, path1 = Pathfinder(graph).find_path("volume")
    val1 = graph.compute("volume")
    print(f"{'volume'}: {val1} (cost: {cost1:.2f})")

    graph.ways.pop("area", None)
    cost2, path2 = Pathfinder(graph).find_path("volume")
    val2 = graph.compute("volume")
    print(f"{'volume'}: {val2} (cost: {cost2:.2f})")

    graph.ways.pop("length", None)
    try:
        cost3, path3 = Pathfinder(graph).find_path("volume")
        val3 = graph.compute("volume")
        print(f"{'volume'}: {val3} (cost: {cost3:.2f})")
        assert False, "Expected NoPathError but got a valid result"
    except NoPathError as e:
        print(f"Got expected error: {e}")
