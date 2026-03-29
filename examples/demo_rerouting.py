import logging

logging.basicConfig(level=logging.INFO)

from griblet import Graph, NoPathError
from griblet.pathfinder import Pathfinder

from box_demo import BoxLoader, make_box_graph


if __name__ == "__main__":
    loader = BoxLoader()
    graph = Graph(loader.as_graph())
    graph.merge(make_box_graph())

    cost1, _path1 = Pathfinder(graph).find_path("volume")
    val1 = graph.compute("volume")
    print(f"{'volume'}: {val1} (cost: {cost1:.2f})")

    graph.ways.pop("area", None)
    cost2, _path2 = Pathfinder(graph).find_path("volume")
    val2 = graph.compute("volume")
    print(f"{'volume'}: {val2} (cost: {cost2:.2f})")

    graph.ways.pop("length", None)
    try:
        cost3, _path3 = Pathfinder(graph).find_path("volume")
        val3 = graph.compute("volume")
        print(f"{'volume'}: {val3} (cost: {cost3:.2f})")
        assert False, "Expected NoPathError but got a valid result"
    except NoPathError as e:
        print(f"Got expected error: {e}")
