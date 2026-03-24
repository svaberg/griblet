import astropy.units as u
import pytest

from griblet import Graph
from griblet.pathfinder import Pathfinder
from room_demo import make_room_graph, RoomLoader

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


def build_graph():
    loader = RoomLoader()
    loader_graph = loader.as_graph()
    graph = Graph(loader_graph)
    graph.merge(make_room_graph())
    return graph


def solve_volume():
    graph = build_graph()
    cost, path = Pathfinder(graph).find_path("volume")
    return graph, cost, path


def test_demo_dependency_solver_flow():
    graph, cost, path = solve_volume()
    vol_value = graph.compute("volume")
    vol_value2 = graph.compute("volume")

    assert cost == pytest.approx(2.2)
    assert vol_value.to_value(u.m**3) == pytest.approx([60.0])
    assert vol_value2.to_value(u.m**3) == pytest.approx([60.0])

if __name__ == "__main__":
    graph, cost, path = solve_volume()

    print("\n=== Dependency Solver Demo (Room Volume, multiple paths) ===\n")
    print(f"Best total cost: {cost:.2f}\nPath:")
    print_path(path)

    # 3. Evaluate and show the computation (no cache, so both calls should behave the same)
    print("\nFirst evaluation:")
    vol_value = graph.compute("volume")
    print("Volume:", vol_value)

    print("\nSecond evaluation (should be identical):")
    vol_value2 = graph.compute("volume")
    print("Volume:", vol_value2)

    print("\nVolume in liters:")
    print(vol_value.to(u.L))
