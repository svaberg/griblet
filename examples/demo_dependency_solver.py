import numpy as np
import astropy.units as u

from griblet.dependency_solver import DependencySolver
from griblet.computation_graph import ComputationGraph
from griblet.evaluate_tree import evaluate_tree
from room_demo import add_room_recipes, RoomLoader

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

if __name__ == "__main__":

    loader = RoomLoader()
    computation_graph = ComputationGraph()
    computation_graph.add_loader_fields(loader)
    add_room_recipes(computation_graph)

    # 2. Dependency solve as before
    solver = DependencySolver(computation_graph)
    cost, tree = solver.resolve_field('volume')

    print("\n=== Dependency Solver Demo (Room Volume, multiple paths) ===\n")
    print(f"Best total cost: {cost:.2f}\nComputation tree:")
    print_tree(tree)

    # 3. Evaluate and show the computation (no cache, so both calls should behave the same)
    print("\nFirst evaluation:")
    vol_value = evaluate_tree(tree, computation_graph)
    print("Volume:", vol_value)

    print("\nSecond evaluation (should be identical):")
    vol_value2 = evaluate_tree(tree, computation_graph)
    print("Volume:", vol_value2)

    print("\nVolume in liters:")
    print(vol_value.to(u.L))
