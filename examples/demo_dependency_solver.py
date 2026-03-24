import astropy.units as u
import pytest

from griblet import ComputationGraph
from room_demo import make_room_recipes_graph, RoomLoader

def print_tree(node, indent=0):
    if node is None:
        print(" " * indent + "(unresolvable)")
        return
    leaf = " [primary]" if getattr(node, 'used_primary', False) else ""
    desc = getattr(node, 'recipe_metadata', {}).get('description', '')
    unit = getattr(node, 'recipe_metadata', {}).get('unit', '')
    print(" " * indent + f"{node.field} (cost: {node.cost}){leaf} {desc} {unit}")
    for dep in getattr(node, 'deps', []):
        print_tree(dep, indent + 4)


def build_graph():
    loader = RoomLoader()
    loader_graph = loader.as_graph()
    computation_graph = ComputationGraph(loader_graph)
    room_recipies_graph = make_room_recipes_graph()
    computation_graph.merge(room_recipies_graph)
    return computation_graph


def solve_volume():
    computation_graph = build_graph()
    cost, tree = computation_graph.plan('volume')
    return computation_graph, cost, tree


def test_demo_dependency_solver_flow():
    computation_graph, cost, tree = solve_volume()
    vol_value = computation_graph.compute('volume')
    vol_value2 = computation_graph.compute('volume')

    assert cost == pytest.approx(2.2)
    assert vol_value.to_value(u.m**3) == pytest.approx([60.0])
    assert vol_value2.to_value(u.m**3) == pytest.approx([60.0])

if __name__ == "__main__":
    computation_graph, cost, tree = solve_volume()

    print("\n=== Dependency Solver Demo (Room Volume, multiple paths) ===\n")
    print(f"Best total cost: {cost:.2f}\nComputation tree:")
    print_tree(tree)

    # 3. Evaluate and show the computation (no cache, so both calls should behave the same)
    print("\nFirst evaluation:")
    vol_value = computation_graph.compute('volume')
    print("Volume:", vol_value)

    print("\nSecond evaluation (should be identical):")
    vol_value2 = computation_graph.compute('volume')
    print("Volume:", vol_value2)

    print("\nVolume in liters:")
    print(vol_value.to(u.L))
