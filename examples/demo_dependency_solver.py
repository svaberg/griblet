import numpy as np
import astropy.units as u

from griblet.computation_tree import ComputationTreeNode
from griblet.dependency_solver import DependencySolver
from griblet.evaluate_tree import evaluate_tree

# Import the unified graph builder from your other example.
from demo_room_graph import make_room_graph

def print_tree(node, indent=0):
    if node is None:
        print(" " * indent + "(unresolvable)")
        return
    leaf = " [primary]" if node.used_primary else ""
    desc = node.recipe_metadata.get('description', '')
    unit = node.recipe_metadata.get('unit', '')
    print(" " * indent + f"{node.field} (cost: {node.cost}){leaf} {desc} {unit}")
    for dep in node.deps:
        print_tree(dep, indent + 4)

if __name__ == "__main__":
    g, cache = make_room_graph()  # Updated: make_room_graph returns (graph, cache)

    solver = DependencySolver(g)
    cost, tree = solver.resolve_field('volume')

    print("\n=== Dependency Solver Demo (Room Volume, multiple paths) ===\n")
    print(f"Best total cost: {cost:.2f}\nComputation tree:")
    print_tree(tree)

    # Evaluate and show caching/cost in action
    print("\nFirst evaluation (should trigger file read):")
    vol_value = evaluate_tree(tree, g)
    print("Volume:", vol_value)

    print("\nSecond evaluation (should be cached, fast):")
    vol_value2 = evaluate_tree(tree, g)
    print("Volume:", vol_value2)

    print("\nVolume in liters:")
    print(vol_value.to(u.L))
