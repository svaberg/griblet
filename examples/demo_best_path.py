from griblet import Graph
from griblet.pathfinder import Pathfinder

from box_demo import BoxLoader, make_box_graph, ureg


def print_path(node, indent=0):
    if node is None:
        print(" " * indent + "(unresolvable)")
        return
    leaf = " [source]" if getattr(node, "is_source", False) else ""
    desc = getattr(node, "metadata", {}).get("description", "")
    unit = getattr(node, "metadata", {}).get("unit", "")
    print(" " * indent + f"{node.name} (cost: {node.cost}){leaf} {desc} {unit}")
    for need in getattr(node, "needs", []):
        print_path(need, indent + 4)

if __name__ == "__main__":
    loader = BoxLoader()
    graph = Graph(loader.as_graph())
    graph.merge(make_box_graph())
    cost, path = Pathfinder(graph).find_path("volume")

    print("\n=== Best Path Demo (Box Volume, multiple paths) ===\n")
    print(f"Best total cost: {cost:.2f}\nPath:")
    print_path(path)

    print("\nFirst evaluation:")
    vol_value = graph.compute("volume")
    print("Volume:", vol_value)

    print("\nSecond evaluation (should be identical):")
    vol_value2 = graph.compute("volume")
    print("Volume:", vol_value2)

    print("\nVolume in liters:")
    print(vol_value.to(ureg.liter))
