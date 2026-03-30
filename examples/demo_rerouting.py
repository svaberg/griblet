"""Show how path choice changes when one box-volume path is removed."""

import logging

logging.basicConfig(level=logging.INFO)

from griblet import Graph, NoPathError

from box_demo import BoxLoader, box_graph


if __name__ == "__main__":
    graph = Graph()
    graph.merge(BoxLoader().as_graph())
    graph.merge(box_graph())

    path1 = graph.path("volume")
    val1 = graph.compute("volume")
    print(f"{'volume'}: {val1} (cost: {path1.cost:.2f})")

    graph.paths["volume"].pop()
    path2 = graph.path("volume")
    val2 = graph.compute("volume")
    print(f"{'volume'}: {val2} (cost: {path2.cost:.2f})")

    graph.paths.pop("length", None)
    try:
        path3 = graph.path("volume")
        val3 = graph.compute("volume")
        print(f"{'volume'}: {val3} (cost: {path3.cost:.2f})")
        assert False, "Expected NoPathError but got a valid result"
    except NoPathError as e:
        print(f"Got expected error: {e}")
