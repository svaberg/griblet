"""Print the cheapest resolved box-volume path and evaluate it twice."""

from griblet import Graph

from demo_box import BoxLoader, box_graph, ureg

if __name__ == "__main__":
    graph = Graph()
    graph.merge(BoxLoader().as_graph())
    graph.merge(box_graph())
    path = graph.path("volume")

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
