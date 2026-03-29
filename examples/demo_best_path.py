from griblet import Graph
from griblet.pathfinder import Pathfinder

from box_demo import BoxLoader, make_box_graph, ureg

if __name__ == "__main__":
    loader = BoxLoader()
    graph = Graph(loader.as_graph())
    graph.merge(make_box_graph())
    path = Pathfinder(graph).find_path("volume")

    print("\n=== Best Path Demo (Box Volume, multiple paths) ===\n")
    print(f"Best total cost: {path.cost:.2f}\nPath:")
    print(path)

    print("\nFirst evaluation:")
    vol_value = graph.compute("volume")
    print("Volume:", vol_value)

    print("\nSecond evaluation (should be identical):")
    vol_value2 = graph.compute("volume")
    print("Volume:", vol_value2)

    print("\nVolume in liters:")
    print(vol_value.to(ureg.liter))
