import networkx as nx
import matplotlib.pyplot as plt
import logging
logging.basicConfig(level=logging.INFO)

from griblet.computation_graph import ComputationGraph
from griblet.dependency_solver import DependencySolver, UnresolvableFieldError
from griblet.evaluate_tree import evaluate_tree

from room_demo import make_room_recipes_graph, RoomLoader


if __name__ == "__main__":

    loader = RoomLoader()
    loader_graph = loader.as_graph()
    computation_graph = ComputationGraph(loader_graph)
    room_recipies_graph = make_room_recipes_graph()
    computation_graph.merge(room_recipies_graph)
    
    # Initial graph with all recipes
    solver = DependencySolver(computation_graph)
    cost1, tree1 = solver.resolve_field('volume')
    val1 = evaluate_tree(tree1, computation_graph)
    print(f"{'volume'}: {val1} (cost: {cost1:.2f})")

    # Remove 'area' recipe and resolve again
    computation_graph.recipes.pop('area', None)
    solver2 = DependencySolver(computation_graph)
    cost2, tree2 = solver2.resolve_field('volume')
    val2 = evaluate_tree(tree2, computation_graph)
    print(f"{'volume'}: {val2} (cost: {cost2:.2f})")

    # Remove 'length' recipe and resolve again
    computation_graph.recipes.pop('length', None)
    solver3 = DependencySolver(computation_graph)
    try:
        cost3, tree3 = solver3.resolve_field('volume')
        val3 = evaluate_tree(tree3, computation_graph)
        print(f"{'volume'}: {val3} (cost: {cost3:.2f})")
        assert False, "Expected UnresolvableFieldError but got a valid result"
    except UnresolvableFieldError as e:
        print(f"Got expected error: {e}")

