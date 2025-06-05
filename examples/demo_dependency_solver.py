import numpy as np
import astropy.units as u

from griblet.computation_graph import ComputationGraph
from griblet.computation_tree import ComputationTreeNode
from griblet.dependency_solver import DependencySolver
from griblet.loader_and_cache import DummyLoader, FieldCache
from griblet.tree_evaluator import evaluate_tree

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

def universal_loader_factory(field_name, cache: FieldCache):
    return lambda: cache.get(field_name)

if __name__ == "__main__":
    # Simulate file-backed measurements (or plans, or sensors)
    values = {
        'length': np.array([5.0]) * u.m,
        'width': np.array([4.0]) * u.m,
        'height': np.array([3.0]) * u.m,
        'area': np.array([20.0]) * u.m**2,
        'perimeter': np.array([18.0]) * u.m,
        'ceiling_height': np.array([3.0]) * u.m,
    }

    class RoomLoader:
        def load(self, field):
            # Let's simulate a "block" load: if you ask for any, you get all!
            print(f"[RoomLoader] Loading all fields (simulated file read)...")
            return values.copy()

    # Use only one cache instance here for simplicity (or split if you prefer)
    room_loader = RoomLoader()
    cache = FieldCache(room_loader, uncached_cost=50, cached_cost=0.1)

    g = ComputationGraph()

    # Register all fields as zero-dependency recipes (file-backed)
    for field in values:
        g.add_recipe(
            field, [],
            universal_loader_factory(field, cache),
            cost=lambda field=field: cache.cost(field),
            metadata={'description': f'{field} (from file or measurement)', 'unit': values[field].unit}
        )

    # --- Recipes for derived fields (multiple paths) ---

    # area = length * width
    def area_from_lw(length, width):
        return length * width
    g.add_recipe(
        'area', ['length', 'width'],
        area_from_lw,
        cost=2.0,
        metadata={'description': 'Area from length * width', 'unit': u.m**2}
    )

    # perimeter = 2*(length + width)
    def perim_from_lw(length, width):
        return 2 * (length + width)
    g.add_recipe(
        'perimeter', ['length', 'width'],
        perim_from_lw,
        cost=1.5,
        metadata={'description': 'Perimeter from length + width', 'unit': u.m}
    )

    # length = (perimeter/2) - width
    def length_from_perim_width(perimeter, width):
        return (perimeter / 2) - width
    g.add_recipe(
        'length', ['perimeter', 'width'],
        length_from_perim_width,
        cost=5.0,
        metadata={'description': 'Length from perimeter and width', 'unit': u.m}
    )

    # volume = area * height
    def volume_from_area_height(area, height):
        return area * height
    g.add_recipe(
        'volume', ['area', 'height'],
        volume_from_area_height,
        cost=2.0,
        metadata={'description': 'Volume from area * height', 'unit': u.m**3}
    )

    # volume = length * width * ceiling_height
    def volume_from_lw_ceil(length, width, ceiling_height):
        return length * width * ceiling_height
    g.add_recipe(
        'volume', ['length', 'width', 'ceiling_height'],
        volume_from_lw_ceil,
        cost=3.0,
        metadata={'description': 'Volume from l * w * ceiling_height', 'unit': u.m**3}
    )

    # --- Solve for volume ---
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
