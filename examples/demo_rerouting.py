import logging

logging.basicConfig(level=logging.INFO)

from griblet import NoPathError

from box_demo import build_box_graph


if __name__ == "__main__":
    graph = build_box_graph()

    path1 = graph.path("volume")
    val1 = graph.compute("volume")
    print(f"{'volume'}: {val1} (cost: {path1.cost:.2f})")

    graph.ways.pop("area", None)
    path2 = graph.path("volume")
    val2 = graph.compute("volume")
    print(f"{'volume'}: {val2} (cost: {path2.cost:.2f})")

    graph.ways.pop("length", None)
    try:
        path3 = graph.path("volume")
        val3 = graph.compute("volume")
        print(f"{'volume'}: {val3} (cost: {path3.cost:.2f})")
        assert False, "Expected NoPathError but got a valid result"
    except NoPathError as e:
        print(f"Got expected error: {e}")
